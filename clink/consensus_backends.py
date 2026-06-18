"""Subscription-CLI backends for the ``cli_consensus`` tool.

Each backend wraps one local CLI that authenticates via an existing *subscription*
(Claude Max / ChatGPT / Google One) instead of a paid API key:

    claude  ->  claude --print --output-format json --model <m>          (prompt via stdin)
    codex   ->  codex exec --skip-git-repo-check --sandbox read-only --json  (prompt via stdin)
    agy     ->  agy --model "<m>" -p "<prompt>"                           (prompt as argument)

All flags are deliberately **read-only** (no ``--yolo`` / ``acceptEdits`` /
``--dangerously-bypass``): the consensus only needs the model to *answer*, not to
touch the filesystem. This differs from the agentic clink conf profiles on purpose.

A backend runs the CLI as a short-lived async subprocess, parses stdout with the
matching clink parser, and **degrades gracefully**: ``run()`` never raises — any
failure, timeout, or rate-limit yields a :class:`BackendResult` with
``status != "success"`` so the consensus continues with the surviving backends.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import signal
import time
from dataclasses import dataclass, field

from clink.parsers import ParsedCLIResponse, get_parser

DEFAULT_TIMEOUT_SECONDS = 300
_STREAM_LIMIT = 10 * 1024 * 1024  # 10 MB per stream
_POST_KILL_TIMEOUT = 5.0  # bounded reap after kill so we never hang
# arg-mode prompts ride on the command line -> bounded by OS ARG_MAX (E2BIG). Stay well under.
_ARG_PROMPT_LIMIT = 96 * 1024

# A global user CLAUDE.md can force a leading "**HH:MM ...**" timestamp line onto
# `claude --print` output; strip it so consensus answers stay clean.
_TIMESTAMP_PREFIX = re.compile(r"^\s*\*\*[^\n]*\d{2}:\d{2}[^\n]*\*\*\s*\n*")

_RATE_LIMIT_HINTS = ("429", "rate limit", "quota", "resource_exhausted", "too many requests")


def _looks_rate_limited(*texts: str) -> bool:
    blob = " ".join(t for t in texts if t).lower()
    return any(hint in blob for hint in _RATE_LIMIT_HINTS)


def _clean(content: str) -> str:
    return _TIMESTAMP_PREFIX.sub("", content or "").strip()


@dataclass
class BackendResult:
    """Outcome of one backend invocation. Always returned, never raised."""

    name: str
    model: str | None
    status: str  # "success" | "error" | "rate_limited"
    content: str = ""
    error: str | None = None
    duration_seconds: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == "success" and bool(self.content)


@dataclass
class CliBackend:
    """One subscription-CLI backend (claude / codex / agy)."""

    name: str
    executable: str
    parser_name: str
    prompt_mode: str = "stdin"  # "stdin" | "arg"
    pre_model_args: list[str] = field(default_factory=list)
    post_model_args: list[str] = field(default_factory=list)
    model: str | None = None
    model_flag: str = "--model"
    timeout: int = DEFAULT_TIMEOUT_SECONDS

    def build_command(self, prompt: str) -> list[str]:
        """Assemble argv. Model flag sits between pre/post args; agy needs it before ``-p``."""
        cmd = [self.executable, *self.pre_model_args]
        if self.model:
            cmd += [self.model_flag, self.model]
        cmd += self.post_model_args
        if self.prompt_mode == "arg":
            cmd.append(prompt)
        return cmd

    async def run(self, prompt: str) -> BackendResult:
        """Run the backend. NEVER raises — degrades to a BackendResult on any failure."""
        try:
            return await self._run(prompt)
        except Exception as exc:  # noqa: BLE001 - partial-failure contract: degrade, never propagate
            return BackendResult(self.name, self.model, "error", error=f"backend error: {exc}")

    async def _run(self, prompt: str) -> BackendResult:
        start = time.monotonic()

        # arg-mode (agy) puts the prompt on the command line -> guard against ARG_MAX (E2BIG).
        if self.prompt_mode == "arg" and len(prompt.encode("utf-8")) > _ARG_PROMPT_LIMIT:
            return BackendResult(
                self.name,
                self.model,
                "error",
                error=f"prompt too large ({len(prompt)} chars) for arg-mode backend '{self.name}'",
            )

        resolved = shutil.which(self.executable)
        if resolved is None:
            return BackendResult(
                self.name, self.model, "error", error=f"executable '{self.executable}' not found in PATH"
            )

        command = self.build_command(prompt)
        command[0] = resolved
        stdin_data = prompt.encode("utf-8") if self.prompt_mode == "stdin" else b""

        try:
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=_STREAM_LIMIT,
                start_new_session=True,  # own process group -> kill the whole tree on timeout
            )
        except OSError as exc:
            return BackendResult(
                self.name, self.model, "error", error=str(exc), duration_seconds=time.monotonic() - start
            )

        try:
            out_b, err_b = await asyncio.wait_for(proc.communicate(stdin_data), timeout=self.timeout)
        except asyncio.TimeoutError:
            await self._terminate(proc)
            return BackendResult(
                self.name,
                self.model,
                "error",
                error=f"timeout after {self.timeout}s",
                duration_seconds=time.monotonic() - start,
            )

        duration = time.monotonic() - start
        stdout = out_b.decode("utf-8", "replace")
        stderr = err_b.decode("utf-8", "replace")
        returncode = proc.returncode

        try:
            parsed: ParsedCLIResponse = get_parser(self.parser_name).parse(stdout, stderr)
        except Exception as exc:  # noqa: BLE001 - any parser failure (ParserError, KeyError, JSON…) degrades
            status = "rate_limited" if _looks_rate_limited(stdout, stderr) else "error"
            return BackendResult(
                self.name,
                self.model,
                status,
                error=f"parse error: {exc}",
                duration_seconds=duration,
                metadata={"returncode": returncode, "stderr": stderr[:500]},
            )

        meta = dict(parsed.metadata)
        meta["returncode"] = returncode

        # Scan only stderr + the parser's flag here — NOT stdout: a successfully parsed answer
        # that *discusses* rate limits/quota must not be misclassified (real bug from live demo).
        if parsed.metadata.get("rate_limited") or _looks_rate_limited(stderr):
            return BackendResult(
                self.name,
                self.model,
                "rate_limited",
                content=_clean(parsed.content),
                error="rate limited / quota exhausted",
                duration_seconds=duration,
                metadata=meta,
            )

        content = _clean(parsed.content)
        if not content:
            # Empty after cleaning (e.g. non-zero exit with no usable output) -> not a success.
            return BackendResult(
                self.name,
                self.model,
                "error",
                error=f"empty content (returncode={returncode})",
                duration_seconds=duration,
                metadata=meta,
            )

        return BackendResult(
            self.name, self.model, "success", content=content, duration_seconds=duration, metadata=meta
        )

    @staticmethod
    async def _terminate(proc) -> None:
        """Kill the whole process group, then reap with a bounded wait (never hang)."""
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                proc.kill()
            except ProcessLookupError:
                return
        try:
            await asyncio.wait_for(proc.communicate(), timeout=_POST_KILL_TIMEOUT)
        except Exception:  # noqa: BLE001 - best-effort reap; the kill already happened
            pass


def default_backends(timeout: int = DEFAULT_TIMEOUT_SECONDS) -> list[CliBackend]:
    """Default consensus panel — one backend per subscription pool.

    claude (Claude Max) · codex (ChatGPT) · agy (Google One). agy additionally
    covers Claude/GPT-OSS via Google One and can serve as a fallback pool.
    """
    return [
        CliBackend(
            name="claude",
            executable="claude",
            parser_name="claude_json",
            prompt_mode="stdin",
            pre_model_args=["--print", "--output-format", "json"],
            model="sonnet",
            model_flag="--model",
            timeout=timeout,
        ),
        CliBackend(
            name="codex",
            executable="codex",
            parser_name="codex_jsonl",
            prompt_mode="stdin",
            pre_model_args=["exec", "--skip-git-repo-check", "--sandbox", "read-only", "--json"],
            model=None,
            model_flag="-m",
            timeout=timeout,
        ),
        CliBackend(
            name="agy",
            executable="agy",
            parser_name="agy_text",
            prompt_mode="arg",
            post_model_args=["-p"],
            model="Gemini 3.1 Pro (Low)",
            model_flag="--model",
            timeout=timeout,
        ),
    ]


async def run_backends(backends: list[CliBackend], prompt: str) -> list[BackendResult]:
    """Run all backends concurrently with the same prompt. Partial-failure safe.

    ``return_exceptions=True`` is defence-in-depth: ``run()`` already never raises,
    but this guarantees the gather itself cannot fail the whole panel.
    """
    if not backends:
        return []
    results = await asyncio.gather(*(b.run(prompt) for b in backends), return_exceptions=True)
    normalised: list[BackendResult] = []
    for backend, result in zip(backends, results):
        if isinstance(result, BaseException):
            normalised.append(BackendResult(backend.name, backend.model, "error", error=f"unexpected: {result}"))
        else:
            normalised.append(result)
    return normalised

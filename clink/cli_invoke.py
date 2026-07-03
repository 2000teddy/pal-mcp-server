"""Synchronous subscription-CLI invocation for the global CLI provider.

This is the blocking sibling of :mod:`clink.consensus_backends`: the provider
interface (``ModelProvider.generate_content``) is synchronous and is called from
inside the server's asyncio event loop, so running the CLI via ``asyncio`` here
would deadlock ("cannot be called from a running event loop", see
docs/architecture/ADR-002-global-cli-backend.md). Instead the CLI runs as a
blocking subprocess — exactly as long-blocking as the HTTP calls the API
providers make, so no new behaviour is introduced at the event-loop level.

Unlike the consensus backends (partial-failure contract: never raise), this
module raises on failure: tools expect provider errors to surface as
exceptions, mirroring the API providers.

The command-shape knowledge (prompt modes, arg-size guard, timestamp cleaning,
rate-limit heuristics) is shared with the consensus backends via imports so it
lives in exactly one place.
"""

from __future__ import annotations

import logging
import os
import shutil
import signal
import subprocess
import time
from dataclasses import dataclass, field

from clink.consensus_backends import (
    _ARG_PROMPT_LIMIT,
    DEFAULT_TIMEOUT_SECONDS,
    _clean,
    _looks_rate_limited,
)
from clink.parsers import ParsedCLIResponse, get_parser

logger = logging.getLogger(__name__)

_POST_KILL_TIMEOUT = 5.0  # bounded reap after killpg so we never hang


class CliInvocationError(RuntimeError):
    """A subscription-CLI call failed (not found, timeout, bad exit, empty output)."""


class CliRateLimitError(CliInvocationError):
    """The subscription CLI reported a rate limit / exhausted quota."""


@dataclass
class CliInvocationSpec:
    """How to invoke one subscription CLI for one catalogue model.

    Mirrors the ``cli`` object in ``conf/cli_models.json``.
    """

    name: str
    executable: str
    parser_name: str
    prompt_mode: str = "stdin"  # "stdin" | "arg"
    pre_model_args: list[str] = field(default_factory=list)
    post_model_args: list[str] = field(default_factory=list)
    cli_model: str | None = None
    model_flag: str = "--model"
    timeout: int = DEFAULT_TIMEOUT_SECONDS

    @classmethod
    def from_config(cls, name: str, config: dict, timeout: int | None = None) -> CliInvocationSpec:
        return cls(
            name=name,
            executable=config["executable"],
            parser_name=config.get("parser", "claude_json"),
            prompt_mode=config.get("prompt_mode", "stdin"),
            pre_model_args=list(config.get("pre_model_args") or []),
            post_model_args=list(config.get("post_model_args") or []),
            cli_model=config.get("cli_model"),
            model_flag=config.get("model_flag", "--model"),
            timeout=timeout or int(config.get("timeout") or DEFAULT_TIMEOUT_SECONDS),
        )

    def build_command(self, prompt: str) -> list[str]:
        """Assemble argv. Model flag sits between pre/post args; agy needs it before ``-p``."""
        cmd = [self.executable, *self.pre_model_args]
        if self.cli_model:
            cmd += [self.model_flag, self.cli_model]
        cmd += self.post_model_args
        if self.prompt_mode == "arg":
            cmd.append(prompt)
        return cmd


def run_cli_sync(spec: CliInvocationSpec, prompt: str) -> tuple[str, dict]:
    """Run one subscription CLI to completion and return ``(content, metadata)``.

    Raises:
        CliRateLimitError: rate limit / quota exhaustion detected.
        CliInvocationError: any other failure (missing executable, timeout,
            oversized arg-mode prompt, parse failure, empty output).
    """
    start = time.monotonic()

    # arg-mode (agy) puts the prompt on the command line -> guard against ARG_MAX (E2BIG).
    if spec.prompt_mode == "arg" and len(prompt.encode("utf-8")) > _ARG_PROMPT_LIMIT:
        raise CliInvocationError(f"prompt too large ({len(prompt)} chars) for arg-mode CLI backend '{spec.name}'")

    resolved = shutil.which(spec.executable)
    if resolved is None:
        raise CliInvocationError(f"executable '{spec.executable}' not found in PATH")

    command = spec.build_command(prompt)
    command[0] = resolved
    stdin_data = prompt.encode("utf-8") if spec.prompt_mode == "stdin" else b""

    try:
        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,  # own process group -> kill the whole tree on timeout
        )
    except OSError as exc:
        raise CliInvocationError(f"failed to launch '{spec.executable}': {exc}") from exc

    try:
        out_b, err_b = proc.communicate(stdin_data, timeout=spec.timeout)
    except subprocess.TimeoutExpired as exc:
        _terminate(proc)
        # "timeout" wording matters: ModelProvider._is_error_retryable treats it as transient.
        raise CliInvocationError(f"CLI backend '{spec.name}' timeout after {spec.timeout}s") from exc

    duration = time.monotonic() - start
    stdout = out_b.decode("utf-8", "replace")
    stderr = err_b.decode("utf-8", "replace")
    returncode = proc.returncode

    try:
        parsed: ParsedCLIResponse = get_parser(spec.parser_name).parse(stdout, stderr)
    except Exception as exc:
        if _looks_rate_limited(stdout, stderr):
            raise CliRateLimitError(f"CLI backend '{spec.name}' rate limited: {exc}") from exc
        raise CliInvocationError(
            f"CLI backend '{spec.name}' output could not be parsed (returncode={returncode}): {exc}"
        ) from exc

    metadata = dict(parsed.metadata)
    metadata["returncode"] = returncode
    metadata["duration_seconds"] = round(duration, 3)
    metadata["cli_backend"] = spec.name

    # Scan only stderr + the parser's flag here — NOT stdout: a successfully parsed answer
    # that *discusses* rate limits/quota must not be misclassified (see consensus_backends).
    if parsed.metadata.get("rate_limited") or _looks_rate_limited(stderr):
        raise CliRateLimitError(f"CLI backend '{spec.name}' rate limited / quota exhausted")

    content = _clean(parsed.content)
    if not content:
        raise CliInvocationError(f"CLI backend '{spec.name}' returned empty content (returncode={returncode})")

    logger.debug("CLI backend '%s' answered in %.1fs (returncode=%s)", spec.name, duration, returncode)
    return content, metadata


def _terminate(proc: subprocess.Popen) -> None:
    """Kill the whole process group, then reap with a bounded wait (never hang)."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except ProcessLookupError:
            return
    try:
        proc.communicate(timeout=_POST_KILL_TIMEOUT)
    except Exception:  # noqa: BLE001 - best-effort reap; the kill already happened
        pass

"""Unit tests for the cli_consensus subscription-CLI backends."""

import asyncio
import json
import shutil
from dataclasses import replace

import pytest

from clink.consensus_backends import (
    CliBackend,
    default_backends,
    run_backends,
)


class DummyProcess:
    def __init__(self, *, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode
        self.stdin_data: bytes | None = None
        self.killed = False

    async def communicate(self, input_data=b""):
        self.stdin_data = input_data
        return self._stdout, self._stderr

    def kill(self):
        self.killed = True


def _patch_subprocess(monkeypatch, process):
    captured: dict[str, tuple] = {}

    async def fake_exec(*args, **_kwargs):
        captured["args"] = args
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(shutil, "which", lambda name: f"/usr/bin/{name}")
    return captured


def _backend(name: str) -> CliBackend:
    return {b.name: b for b in default_backends(timeout=5)}[name]


@pytest.mark.asyncio
async def test_claude_backend_success(monkeypatch):
    payload = json.dumps({"type": "result", "is_error": False, "result": "Spaces."}).encode()
    proc = DummyProcess(stdout=payload)
    captured = _patch_subprocess(monkeypatch, proc)

    result = await _backend("claude").run("Tabs or spaces?")

    assert result.ok and result.status == "success"
    assert result.content == "Spaces."
    assert proc.stdin_data.decode() == "Tabs or spaces?"  # claude reads stdin
    assert "--print" in captured["args"] and "--yolo" not in captured["args"]


@pytest.mark.asyncio
async def test_codex_backend_success(monkeypatch):
    lines = "\n".join(
        [
            json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "Use spaces."}}),
            json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10}}),
        ]
    ).encode()
    _patch_subprocess(monkeypatch, DummyProcess(stdout=lines))

    result = await _backend("codex").run("Q?")
    assert result.ok and "Use spaces." in result.content


@pytest.mark.asyncio
async def test_agy_backend_uses_prompt_as_arg(monkeypatch):
    proc = DummyProcess(stdout=b"Plain answer")
    captured = _patch_subprocess(monkeypatch, proc)

    result = await _backend("agy").run("My question")

    assert result.ok and result.content == "Plain answer"
    assert proc.stdin_data == b""  # agy passes prompt as arg, not stdin
    args = list(captured["args"])
    assert "My question" in args
    assert args.index("--model") < args.index("-p")  # model precedes -p


@pytest.mark.asyncio
async def test_executable_not_found(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None)
    result = await _backend("claude").run("Q?")
    assert result.status == "error" and "not found" in (result.error or "")


@pytest.mark.asyncio
async def test_rate_limited_detected(monkeypatch):
    _patch_subprocess(monkeypatch, DummyProcess(stdout=b"", stderr=b"Error: 429 quota exceeded"))
    result = await _backend("agy").run("Q?")
    assert result.status == "rate_limited"


@pytest.mark.asyncio
async def test_timestamp_prefix_stripped(monkeypatch):
    payload = json.dumps({"type": "result", "result": "**⏱ 21:00:00 — 2026-06-17**\n\nThe answer."}).encode()
    _patch_subprocess(monkeypatch, DummyProcess(stdout=payload))
    result = await _backend("claude").run("Q?")
    assert result.content == "The answer."


@pytest.mark.asyncio
async def test_run_backends_partial_failure(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda name: None if name == "agy" else f"/usr/bin/{name}")

    async def fake_exec(*_args, **_kwargs):
        return DummyProcess(stdout=json.dumps({"type": "result", "result": "ok"}).encode())

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)

    results = await run_backends([_backend("claude"), _backend("agy")], "Q?")
    statuses = {r.name: r.status for r in results}
    assert statuses == {"claude": "success", "agy": "error"}


def test_build_command_shapes():
    cmd = _backend("claude").build_command("PROMPT")
    assert cmd[0] == "claude" and "--print" in cmd and "PROMPT" not in cmd  # stdin mode

    cmd = _backend("agy").build_command("PROMPT")
    assert cmd[-1] == "PROMPT" and cmd.index("--model") < cmd.index("-p")  # arg mode


def test_default_backends_use_safe_flags():
    assert {b.name for b in default_backends()} == {"claude", "codex", "agy"}
    for b in default_backends():
        joined = " ".join(b.pre_model_args + b.post_model_args)
        assert "--yolo" not in joined
        assert "--dangerously" not in joined
        assert "acceptEdits" not in joined


@pytest.mark.asyncio
async def test_arg_mode_prompt_too_large(monkeypatch):
    # agy puts the prompt on the command line -> must guard against ARG_MAX, not crash.
    _patch_subprocess(monkeypatch, DummyProcess(stdout=b"unused"))
    result = await _backend("agy").run("x" * (200 * 1024))
    assert result.status == "error"
    assert "too large" in (result.error or "")


@pytest.mark.asyncio
async def test_unknown_parser_degrades_not_crashes(monkeypatch):
    # A non-ParserError exception (KeyError from get_parser) must degrade, never propagate.
    _patch_subprocess(monkeypatch, DummyProcess(stdout=b"something"))
    backend = replace(_backend("claude"), parser_name="does_not_exist")
    result = await backend.run("Q?")
    assert result.status == "error"


@pytest.mark.asyncio
async def test_empty_content_after_strip_is_error(monkeypatch):
    # Response that is only the CLAUDE.md timestamp prefix -> cleaned to "" -> not a success.
    payload = json.dumps({"type": "result", "result": "**⏱ 21:00:00 — 2026-06-17**"}).encode()
    _patch_subprocess(monkeypatch, DummyProcess(stdout=payload))
    result = await _backend("claude").run("Q?")
    assert result.status == "error"
    assert not result.ok

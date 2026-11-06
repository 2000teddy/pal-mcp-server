"""Unit tests for the cli_consensus subscription-CLI backends."""

import asyncio
import json
import shutil
import socket
import threading
import time
from dataclasses import replace
from types import SimpleNamespace

import pytest

from clink.consensus_backends import (
    CliBackend,
    MiniMaxBackend,
    default_backends,
    load_panel_models,
    run_backends,
)
from providers.minimax import MiniMaxModelProvider


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


def _backend(name: str):
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
    assert {b.name for b in default_backends()} == {"claude", "codex", "agy", "minimax"}
    for b in default_backends():
        if not isinstance(b, CliBackend):
            continue
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


@pytest.mark.asyncio
async def test_answer_discussing_rate_limits_is_not_flagged(monkeypatch):
    # A successfully parsed answer that *mentions* rate limits/quota must stay "success".
    # (Regression for the false-positive found in the live pal:cli_consensus demo.)
    payload = json.dumps(
        {"type": "result", "result": "APIs have documented rate limits and quota caps; set spend caps."}
    ).encode()
    _patch_subprocess(monkeypatch, DummyProcess(stdout=payload, stderr=b""))
    result = await _backend("claude").run("Q?")
    assert result.status == "success"
    assert result.ok


# --- panel config -------------------------------------------------------------------------------


def test_panel_config_names_the_agreed_models():
    assert load_panel_models() == {
        "claude": "opus",
        "codex": "gpt-6.1-sol",
        "agy": "Gemini 4 Argon (High)",
        "minimax": "MiniMax-M3.1-Flash",
    }


def test_backends_take_their_models_from_the_panel_config(monkeypatch, tmp_path):
    panel = tmp_path / "panel.json"
    panel.write_text(
        json.dumps({"models": {"claude": "c-x", "codex": "g-x", "agy": "a-x", "minimax": "m-x"}}), encoding="utf-8"
    )
    monkeypatch.setenv("CLI_CONSENSUS_PANEL_CONFIG_PATH", str(panel))

    assert {b.name: b.model for b in default_backends()} == {
        "claude": "c-x",
        "codex": "g-x",
        "agy": "a-x",
        "minimax": "m-x",
    }


def test_codex_and_agy_command_carry_the_configured_model():
    codex = _backend("codex").build_command("P")
    assert codex[codex.index("-m") + 1] == "gpt-6.1-sol"
    agy = _backend("agy").build_command("P")
    assert agy[agy.index("--model") + 1] == "Gemini 4 Argon (High)"
    claude = _backend("claude").build_command("P")
    assert claude[claude.index("--model") + 1] == "opus"


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "{}",
        '{"models": []}',
        '{"models": {"claude": "opus"}}',
        '{"models": {"claude": "opus", "codex": "g", "agy": "a", "minimax": "m", "extra": "x"}}',
        '{"models": {"claude": "", "codex": "g", "agy": "a", "minimax": "m"}}',
        '{"models": {"claude": 1, "codex": "g", "agy": "a", "minimax": "m"}}',
    ],
)
def test_invalid_panel_config_raises_instead_of_guessing(monkeypatch, tmp_path, content):
    panel = tmp_path / "panel.json"
    panel.write_text(content, encoding="utf-8")
    monkeypatch.setenv("CLI_CONSENSUS_PANEL_CONFIG_PATH", str(panel))
    with pytest.raises(ValueError, match="panel config"):
        load_panel_models()


def test_missing_panel_config_raises(monkeypatch, tmp_path):
    monkeypatch.setenv("CLI_CONSENSUS_PANEL_CONFIG_PATH", str(tmp_path / "nope.json"))
    with pytest.raises(ValueError, match="panel config"):
        load_panel_models()


# --- MiniMax backend ----------------------------------------------------------------------------

_FAKE_KEY = "fake-minimax-key-value"


def _minimax_with_key(monkeypatch, *, timeout: int = 5) -> MiniMaxBackend:
    monkeypatch.setattr("clink.consensus_backends.get_env", lambda _name: _FAKE_KEY)
    return MiniMaxBackend(model="MiniMax-M3.1-Flash", timeout=timeout)


def _patch_generate(monkeypatch, generate) -> None:
    monkeypatch.setattr(MiniMaxModelProvider, "generate_content", generate)


@pytest.mark.parametrize("key", [None, "", "your_minimax_api_key_here"])
@pytest.mark.asyncio
async def test_minimax_skips_without_usable_key(monkeypatch, key):
    def must_not_run(self, **_kwargs):  # noqa: ARG001
        raise AssertionError("provider must not be called without a key")

    _patch_generate(monkeypatch, must_not_run)
    monkeypatch.setattr("clink.consensus_backends.get_env", lambda _name: key)

    result = await MiniMaxBackend(model="MiniMax-M3.1-Flash").run("Q?")

    assert result.status == "skipped" and not result.ok
    assert "MINIMAX_API_KEY" in result.error


@pytest.mark.asyncio
async def test_minimax_success_passes_prompt_and_model_to_provider(monkeypatch):
    seen = {}

    def generate(self, *, prompt, model_name):  # noqa: ARG001
        seen.update(prompt=prompt, model=model_name)
        return SimpleNamespace(content="Use spaces.", metadata={"finish_reason": "stop"})

    _patch_generate(monkeypatch, generate)

    result = await _minimax_with_key(monkeypatch).run("Tabs or spaces?")

    assert result.ok and result.content == "Use spaces."
    assert seen == {"prompt": "Tabs or spaces?", "model": "MiniMax-M3.1-Flash"}


@pytest.mark.asyncio
async def test_minimax_strips_inline_reasoning_of_older_models(monkeypatch):
    _patch_generate(
        monkeypatch,
        lambda self, **_kw: SimpleNamespace(content="<think>hmm\nmore</think>\n\nVerdict.", metadata={}),
    )
    result = await _minimax_with_key(monkeypatch).run("Q?")
    assert result.content == "Verdict."


@pytest.mark.asyncio
async def test_minimax_empty_content_reports_finish_reason(monkeypatch):
    # Thinking counts toward the output limit: finish_reason "length" can leave content empty.
    _patch_generate(
        monkeypatch, lambda self, **_kw: SimpleNamespace(content=None, metadata={"finish_reason": "length"})
    )
    result = await _minimax_with_key(monkeypatch).run("Q?")
    assert result.status == "error" and "length" in result.error


@pytest.mark.asyncio
async def test_minimax_error_never_leaks_the_key(monkeypatch):
    def generate(self, **_kwargs):  # noqa: ARG001
        raise RuntimeError(f"401 invalid api key {_FAKE_KEY}")

    _patch_generate(monkeypatch, generate)
    result = await _minimax_with_key(monkeypatch).run("Q?")
    assert result.status == "error"
    assert _FAKE_KEY not in result.error and "***" in result.error


@pytest.mark.asyncio
async def test_minimax_rate_limit_is_flagged(monkeypatch):
    def generate(self, **_kwargs):  # noqa: ARG001
        raise RuntimeError("Error code: 429 - too many requests")

    _patch_generate(monkeypatch, generate)
    result = await _minimax_with_key(monkeypatch).run("Q?")
    assert result.status == "rate_limited"


@pytest.mark.asyncio
async def test_minimax_unknown_model_errors_without_fallback(monkeypatch):
    # Real provider path: an unknown model must fail, not silently become another model.
    backend = replace(_minimax_with_key(monkeypatch), model="MiniMax-Does-Not-Exist")
    result = await backend.run("Q?")
    assert result.status == "error"
    assert result.content == ""
    assert "MiniMax-Does-Not-Exist" in result.error


@pytest.fixture
def hanging_minimax(monkeypatch):
    """A real local endpoint that accepts and never answers. Yields (connections, worker_done)."""
    connections = []
    server = socket.create_server(("127.0.0.1", 0))
    server.settimeout(0.1)
    stop = threading.Event()

    def accept_and_hang():
        while not stop.is_set():
            try:
                connections.append(server.accept()[0])
            except OSError:
                continue

    acceptor = threading.Thread(target=accept_and_hang, daemon=True)
    acceptor.start()
    monkeypatch.setenv("MINIMAX_API_BASE_URL", f"http://127.0.0.1:{server.getsockname()[1]}/v1")
    # Shorten the provider's retry delays (1s, 3s, 5s), but keep them longer than the gap to the abort.
    real_sleep = time.sleep
    monkeypatch.setattr("providers.base.time.sleep", lambda _seconds: real_sleep(0.3))

    worker_done = threading.Event()
    real_generate = MiniMaxModelProvider.generate_content

    def spying_generate(self, **kwargs):
        try:
            return real_generate(self, **kwargs)
        finally:
            worker_done.set()

    _patch_generate(monkeypatch, spying_generate)
    try:
        yield connections, worker_done
    finally:
        stop.set()
        acceptor.join(2)
        server.close()
        for connection in connections:
            connection.close()


@pytest.mark.asyncio
async def test_minimax_timeout_ends_the_worker_and_sends_no_retry(monkeypatch, hanging_minimax):
    connections, worker_done = hanging_minimax
    backend = _minimax_with_key(monkeypatch)
    backend.timeout = 0.5

    result = await backend.run("Q?")

    assert result.status == "error" and "timeout" in result.error
    assert await asyncio.to_thread(worker_done.wait, 8), "worker thread kept running after the timeout"
    assert len(connections) == 1


@pytest.mark.asyncio
async def test_minimax_cancellation_ends_the_worker_and_sends_no_retry(monkeypatch, hanging_minimax):
    connections, worker_done = hanging_minimax
    backend = _minimax_with_key(monkeypatch)
    backend.timeout = 0.8

    task = asyncio.create_task(backend.run("Q?"))
    await asyncio.sleep(0.4)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert await asyncio.to_thread(worker_done.wait, 8), "worker thread kept running after the cancellation"
    assert len(connections) == 1


@pytest.mark.asyncio
async def test_run_backends_mixes_cli_and_minimax(monkeypatch):
    _patch_subprocess(monkeypatch, DummyProcess(stdout=json.dumps({"type": "result", "result": "ok"}).encode()))
    monkeypatch.setattr("clink.consensus_backends.get_env", lambda _name: None)

    results = await run_backends([_backend("claude"), _backend("minimax")], "Q?")

    assert {r.name: r.status for r in results} == {"claude": "success", "minimax": "skipped"}


# --- MiniMax model catalogue --------------------------------------------------------------------


def test_m31_flash_carries_the_measured_specs():
    caps = MiniMaxModelProvider("k").get_capabilities("MiniMax-M3.1-Flash")
    assert caps.context_window == 1_000_000
    assert caps.max_output_tokens == 524_288
    assert caps.supports_temperature is False
    assert caps.supports_images is True and caps.max_image_size_mb == 10.0
    assert caps.supports_json_mode is False


def test_existing_aliases_still_resolve_as_before():
    provider = MiniMaxModelProvider("k")
    for alias in ("minimax", "minimax-m3", "m3", "minimax3"):
        assert provider._resolve_model_name(alias) == "MiniMax-M3"
    for alias in ("minimax-m2.7", "m2.7", "minimax2.7"):
        assert provider._resolve_model_name(alias) == "MiniMax-M2.7"
    assert MiniMaxModelProvider.PRIMARY_MODEL == "MiniMax-M2.7"


def test_new_aliases_resolve_to_m31_flash():
    provider = MiniMaxModelProvider("k")
    for alias in ("minimax-m3.1-flash", "m3.1-flash", "minimax3.1-flash"):
        assert provider._resolve_model_name(alias) == "MiniMax-M3.1-Flash"


def test_m31_flash_does_not_displace_m3_in_model_ordering():
    names = MiniMaxModelProvider("k").list_models(respect_restrictions=False)
    assert names.index("MiniMax-M3") < names.index("MiniMax-M3.1-Flash")

"""Unit tests for the cli_consensus tool."""

import json

import pytest

from clink.consensus_backends import BackendResult, CliBackend, MiniMaxBackend
from tools.cli_consensus import CliConsensusTool


def _tool() -> CliConsensusTool:
    return CliConsensusTool()


def _patch_run(monkeypatch, fake_run) -> None:
    """Replace run() on both backend classes of the panel."""
    monkeypatch.setattr(CliBackend, "run", fake_run)
    monkeypatch.setattr(MiniMaxBackend, "run", fake_run)


def _payload(text_content_list) -> dict:
    """Unwrap ToolOutput JSON -> inner consensus payload dict."""
    tool_output = json.loads(text_content_list[0].text)
    return json.loads(tool_output["content"])


def test_schema_exposes_prompt_and_backends():
    schema = _tool().get_input_schema()
    assert schema["required"] == ["prompt"]
    props = schema["properties"]
    assert "prompt" in props and "backends" in props
    enum = props["backends"]["items"]["properties"]["backend"]["enum"]
    assert set(enum) == {"claude", "codex", "agy", "minimax"}


def test_blinded_prompt_varies_by_stance():
    tool = _tool()
    q = "Should we adopt approach X?"
    p_for = tool._blinded_prompt(q, "for", None)
    p_against = tool._blinded_prompt(q, "against", None)
    p_neutral = tool._blinded_prompt(q, "neutral", None)
    assert q in p_for and q in p_against and q in p_neutral
    assert p_for != p_against and p_against != p_neutral and p_for != p_neutral


@pytest.mark.asyncio
async def test_execute_runs_default_backends(monkeypatch):
    async def fake_run(self, prompt):  # noqa: ARG001
        return BackendResult(self.name, self.model, "success", content=f"verdict-{self.name}", duration_seconds=1.0)

    _patch_run(monkeypatch, fake_run)

    payload = _payload(await _tool().execute({"prompt": "Evaluate option A vs B"}))

    assert payload["status"] == "consensus_complete"
    assert payload["backends_consulted"] == 4
    assert payload["successful"] == 4
    assert {r["backend"]: r["model"] for r in payload["responses"]} == {
        "claude": "opus",
        "codex": "gpt-6.1-sol",
        "agy": "Gemini 4 Argon (High)",
        "minimax": "MiniMax-M3.1-Flash",
    }
    assert all(r["verdict"].startswith("verdict-") for r in payload["responses"])


@pytest.mark.asyncio
async def test_execute_partial_failure(monkeypatch):
    async def fake_run(self, prompt):  # noqa: ARG001
        if self.name == "agy":
            return BackendResult(self.name, self.model, "rate_limited", error="quota")
        return BackendResult(self.name, self.model, "success", content="ok")

    _patch_run(monkeypatch, fake_run)

    payload = _payload(await _tool().execute({"prompt": "Q?"}))
    assert payload["successful"] == 3
    assert "agy" in payload["skipped_or_failed"]


@pytest.mark.asyncio
async def test_execute_honours_custom_stance_and_model(monkeypatch):
    captured: dict[str, dict] = {}

    async def fake_run(self, prompt):
        captured[self.name] = {"model": self.model, "prompt": prompt}
        return BackendResult(self.name, self.model, "success", content="ok")

    _patch_run(monkeypatch, fake_run)

    await _tool().execute(
        {"prompt": "Evaluate X", "backends": [{"backend": "claude", "stance": "for", "model": "opus"}]}
    )
    assert captured["claude"]["model"] == "opus"
    assert "Evaluate X" in captured["claude"]["prompt"]


@pytest.mark.asyncio
async def test_execute_rejects_unknown_backend():
    tool_output = json.loads((await _tool().execute({"prompt": "Q?", "backends": [{"backend": "grok"}]}))[0].text)
    assert tool_output["status"] == "error"
    assert "Unknown backend" in tool_output["content"]


@pytest.mark.asyncio
async def test_execute_rejects_invalid_stance():
    out = await _tool().execute({"prompt": "Q?", "backends": [{"backend": "claude", "stance": "sideways"}]})
    tool_output = json.loads(out[0].text)
    assert tool_output["status"] == "error"
    assert "stance" in tool_output["content"].lower()


@pytest.mark.asyncio
async def test_execute_rejects_duplicate_backend_stance():
    out = await _tool().execute(
        {
            "prompt": "Q?",
            "backends": [{"backend": "claude", "stance": "for"}, {"backend": "claude", "stance": "for"}],
        }
    )
    tool_output = json.loads(out[0].text)
    assert tool_output["status"] == "error"
    assert "duplicate" in tool_output["content"].lower()


@pytest.mark.asyncio
async def test_execute_rejects_too_many_backends():
    specs = [{"backend": b, "stance": s} for b in ("claude", "codex", "agy") for s in ("for", "against", "neutral")]
    assert len(specs) == 9  # > _MAX_BACKENDS (8)
    out = await _tool().execute({"prompt": "Q?", "backends": specs})
    tool_output = json.loads(out[0].text)
    assert tool_output["status"] == "error"
    assert "too many" in tool_output["content"].lower()


@pytest.mark.asyncio
async def test_minimax_without_key_is_skipped_and_reported(monkeypatch):
    # Real MiniMaxBackend.run, no key: reported as skipped, while the CLI backends carry on.
    async def fake_cli_run(self, prompt):  # noqa: ARG001
        return BackendResult(self.name, self.model, "success", content="ok")

    monkeypatch.setattr(CliBackend, "run", fake_cli_run)
    monkeypatch.setattr("clink.consensus_backends.get_env", lambda _name: None)

    payload = _payload(await _tool().execute({"prompt": "Q?"}))

    assert payload["successful"] == 3
    assert payload["skipped_or_failed"] == ["minimax"]
    minimax = next(r for r in payload["responses"] if r["backend"] == "minimax")
    assert minimax["status"] == "skipped"
    assert "MINIMAX_API_KEY" in minimax["error"]
    assert minimax["verdict"] is None


@pytest.mark.asyncio
async def test_minimax_sees_the_same_blinded_prompt_as_cli_backends(monkeypatch):
    prompts: dict[str, str] = {}

    async def fake_run(self, prompt):
        prompts[self.name] = prompt
        return BackendResult(self.name, self.model, "success", content=f"secret-{self.name}")

    _patch_run(monkeypatch, fake_run)

    await _tool().execute({"prompt": "Evaluate X"})

    assert set(prompts) == {"claude", "codex", "agy", "minimax"}
    assert len(set(prompts.values())) == 1
    assert "secret-" not in prompts["minimax"]


@pytest.mark.asyncio
async def test_broken_panel_config_is_a_clear_tool_error(monkeypatch, tmp_path):
    bad = tmp_path / "panel.json"
    bad.write_text('{"models": {"claude": "opus"}}', encoding="utf-8")
    monkeypatch.setenv("CLI_CONSENSUS_PANEL_CONFIG_PATH", str(bad))

    tool_output = json.loads((await _tool().execute({"prompt": "Q?"}))[0].text)

    assert tool_output["status"] == "error"
    assert "panel config" in tool_output["content"]


def test_schema_does_not_depend_on_panel_config(monkeypatch, tmp_path):
    # A broken config must not take the tool listing (and with it the server) down.
    monkeypatch.setenv("CLI_CONSENSUS_PANEL_CONFIG_PATH", str(tmp_path / "missing.json"))
    assert "backends" in _tool().get_input_schema()["properties"]

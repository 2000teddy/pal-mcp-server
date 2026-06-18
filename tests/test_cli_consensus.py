"""Unit tests for the cli_consensus tool."""

import json

import pytest

from clink.consensus_backends import BackendResult, CliBackend
from tools.cli_consensus import CliConsensusTool


def _tool() -> CliConsensusTool:
    return CliConsensusTool()


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
    assert set(enum) == {"claude", "codex", "agy"}


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

    monkeypatch.setattr(CliBackend, "run", fake_run)

    payload = _payload(await _tool().execute({"prompt": "Evaluate option A vs B"}))

    assert payload["status"] == "consensus_complete"
    assert payload["backends_consulted"] == 3
    assert payload["successful"] == 3
    assert {r["backend"] for r in payload["responses"]} == {"claude", "codex", "agy"}
    assert all(r["verdict"].startswith("verdict-") for r in payload["responses"])


@pytest.mark.asyncio
async def test_execute_partial_failure(monkeypatch):
    async def fake_run(self, prompt):  # noqa: ARG001
        if self.name == "agy":
            return BackendResult(self.name, self.model, "rate_limited", error="quota")
        return BackendResult(self.name, self.model, "success", content="ok")

    monkeypatch.setattr(CliBackend, "run", fake_run)

    payload = _payload(await _tool().execute({"prompt": "Q?"}))
    assert payload["successful"] == 2
    assert "agy" in payload["skipped_or_failed"]


@pytest.mark.asyncio
async def test_execute_honours_custom_stance_and_model(monkeypatch):
    captured: dict[str, dict] = {}

    async def fake_run(self, prompt):
        captured[self.name] = {"model": self.model, "prompt": prompt}
        return BackendResult(self.name, self.model, "success", content="ok")

    monkeypatch.setattr(CliBackend, "run", fake_run)

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

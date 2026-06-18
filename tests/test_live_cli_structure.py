"""Live structural smoke-test for the ADR-002 API->CLI migration.

This exercises the REAL subscription CLIs (``claude`` / ``codex`` / ``agy``) — it is
NOT mocked. It proves the migration carries in practice: each migrated path makes one
short real call and returns a non-empty, plausible answer.

**Not part of the normal gate** — marked ``integration`` (real CLIs cost quota + time).
Run it explicitly:

    .pal_venv/bin/python -m pytest tests/test_live_cli_structure.py -v -s -m integration

Design notes
------------
* **Machine-independent**: no TH01-specific paths. A part ``skip``\\s if its CLI is not
  on ``PATH`` (e.g. a machine without ``codex``) and ``skip``\\s on rate-limit/quota
  (quota reality must not hard-fail the suite).
* **Key-free**: drives the migrated *seams* directly. ``ModelContext.provider`` raises
  without a registered provider (= without a paid API key), so we avoid full
  ``tool.execute()`` model-context resolution and call the CLI-only seams that the
  migration introduced. (Residual note: ``consensus._consult_model`` still builds a
  ModelContext for temperature validation — patched here; flagged for the Hub deploy.)
* **No secrets in output**: only backend name, status, duration and answer *length*
  are printed — never the prompt env or raw answer body.
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from types import SimpleNamespace

import pytest

logger = logging.getLogger("live_cli_structure")

pytestmark = pytest.mark.integration

CLAUDE = "claude"
CODEX = "codex"

_QUOTA_HINTS = ("rate limit", "rate_limited", "quota", "429", "resource_exhausted", "too many requests")


def _skip_if_missing(executable: str) -> None:
    if shutil.which(executable) is None:
        pytest.skip(f"'{executable}' CLI not found on PATH — machine without this subscription CLI")


def _looks_quota(message: str | None) -> bool:
    if not message:
        return False
    low = message.lower()
    return any(hint in low for hint in _QUOTA_HINTS)


def _report(part: str, status: str, seconds: float, detail: str) -> None:
    """Self-documenting one-liner per part. No secrets — names/status/duration/length only."""
    line = f"[live-cli] {part}: {status} in {seconds:.1f}s — {detail}"
    print("\n" + line)
    logger.info(line)


@pytest.mark.asyncio
async def test_a_cli_consensus_claude_codex():
    """a) cli_consensus over claude + codex — blinded, both answer."""
    _skip_if_missing(CLAUDE)
    _skip_if_missing(CODEX)
    from tools.cli_consensus import CliConsensusTool

    tool = CliConsensusTool()
    start = time.monotonic()
    result = await tool.execute(
        {
            "prompt": "Evaluate in ONE short sentence: a small software team should write unit tests.",
            "backends": [{"backend": "claude"}, {"backend": "codex"}],
        }
    )
    elapsed = time.monotonic() - start

    payload = json.loads(json.loads(result[0].text)["content"])
    responses = {r["backend"]: r for r in payload["responses"]}
    statuses = {b: r["status"] for b, r in responses.items()}

    rate_limited = [b for b, r in responses.items() if r["status"] == "rate_limited"]
    if len(rate_limited) == len(responses):
        _report("a) cli_consensus", "SKIP(quota)", elapsed, f"all rate-limited: {rate_limited}")
        pytest.skip("all CLI backends rate-limited")

    for backend, response in responses.items():
        if response["status"] == "rate_limited":
            continue
        assert response["status"] == "success", f"{backend}: {response['status']} ({response.get('error')})"
        assert response["verdict"] and response["verdict"].strip(), f"{backend}: empty verdict"

    _report("a) cli_consensus", "PASS", elapsed, f"statuses={statuses}")


@pytest.mark.asyncio
async def test_b_workflow_expert_analysis_via_cli():
    """b) workflow expert_analysis path (analyze) — confirms backend.run delivers."""
    _skip_if_missing(CLAUDE)
    from tools.analyze import AnalyzeTool
    from tools.shared.base_models import ConsolidatedFindings

    tool = AnalyzeTool()
    # Stub the model context (capabilities tolerated as None) so no provider/API key is needed.
    tool._model_context = SimpleNamespace(capabilities=None)
    tool._current_model_name = "opus"  # -> claude backend
    tool.initial_request = "Confirm that a function add(a, b) returning a + b is correct."
    tool.consolidated_findings = ConsolidatedFindings(findings=["add(a, b) returns a + b; arithmetic looks correct."])

    start = time.monotonic()
    result = await tool._call_expert_analysis({}, SimpleNamespace())
    elapsed = time.monotonic() - start

    status = result.get("status")
    if status == "analysis_error" and _looks_quota(result.get("error")):
        _report("b) expert_analysis", "SKIP(quota)", elapsed, str(result.get("error")))
        pytest.skip("expert_analysis backend rate-limited")

    assert status != "analysis_error", f"expert_analysis failed: {result.get('error')}"
    assert status != "empty_response", "expert_analysis returned empty response"
    body = result.get("raw_analysis") or json.dumps(result)
    assert body and body.strip(), "expert_analysis produced no content"

    _report("b) expert_analysis", "PASS", elapsed, f"backend=claude(opus), status={status}, len={len(body)}")


@pytest.mark.asyncio
async def test_c_chat_via_cli():
    """c) chat over its CLI backend — short prompt, real answer."""
    _skip_if_missing(CLAUDE)
    from tools.chat import ChatTool

    tool = ChatTool()
    tool._current_model_name = "opus"  # -> claude backend

    start = time.monotonic()
    model_response, provider_label = await tool._run_cli_backend(
        "Reply with a short, friendly one-line greeting.", "You are concise."
    )
    elapsed = time.monotonic() - start

    finish_reason = (model_response.metadata or {}).get("finish_reason")
    if finish_reason != "STOP":
        cli_error = (model_response.metadata or {}).get("cli_error")
        if _looks_quota(cli_error):
            _report("c) chat", "SKIP(quota)", elapsed, str(cli_error))
            pytest.skip("chat backend rate-limited")
        raise AssertionError(f"chat backend did not succeed: finish_reason={finish_reason} ({cli_error})")

    assert provider_label == "cli:claude", f"unexpected backend label {provider_label}"
    assert model_response.content and model_response.content.strip(), "chat produced no content"

    _report("c) chat", "PASS", elapsed, f"backend={provider_label}, len={len(model_response.content)}")


@pytest.mark.asyncio
async def test_d_consensus_migrated_claude_codex(monkeypatch):
    """d) migrated consensus over claude + codex — blinded, real answers."""
    _skip_if_missing(CLAUDE)
    _skip_if_missing(CODEX)
    from tools.consensus import ConsensusTool

    tool = ConsensusTool()
    tool.initial_prompt = "Should a small team adopt trunk-based development? Answer in one sentence."
    tool.original_proposal = tool.initial_prompt
    # Temperature validation would resolve a provider (API key); irrelevant to CLI generation.
    monkeypatch.setattr(tool, "validate_and_correct_temperature", lambda temperature, model_context: (0.2, []))

    request = SimpleNamespace(relevant_files=[], images=None, continuation_id=None)
    consultations = {"claude": "opus", "codex": "gpt-5"}

    start = time.monotonic()
    results = {}
    for label, model in consultations.items():
        results[label] = await tool._consult_model({"model": model, "stance": "neutral"}, request)
    elapsed = time.monotonic() - start

    quota = {label: r for label, r in results.items() if r["status"] == "error" and _looks_quota(r.get("error"))}
    if len(quota) == len(results):
        _report("d) consensus", "SKIP(quota)", elapsed, f"all rate-limited: {list(quota)}")
        pytest.skip("all consensus CLI backends rate-limited")

    for label, response in results.items():
        if label in quota:
            continue
        assert response["status"] == "success", f"{label}: {response['status']} ({response.get('error')})"
        assert response["verdict"] and response["verdict"].strip(), f"{label}: empty verdict"

    statuses = {label: r["status"] for label, r in results.items()}
    _report("d) consensus", "PASS", elapsed, f"statuses={statuses}")

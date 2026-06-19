"""Tests for the expert_analysis -> subscription-CLI-backend migration (ADR-002).

Covers two units:

1. The model -> backend mapping (``select_expert_backend_name`` / ``backend_for_model``).
2. The ``_call_expert_analysis`` adapter that turns a ``BackendResult`` into the
   dict shape the workflow layer expects (success / plain-text / rate_limited /
   error / empty), driven through ``AnalyzeTool`` with the backend mocked.
"""

import json
import unittest
from unittest.mock import AsyncMock, Mock, patch

from clink.consensus_backends import (
    DEFAULT_EXPERT_BACKEND,
    BackendResult,
    CliBackend,
    backend_for_model,
    select_expert_backend_name,
)
from tools.analyze import AnalyzeTool
from tools.shared.base_models import ConsolidatedFindings


def _fake_backend(status="success", content="", error=None, name="claude"):
    backend = Mock()
    backend.name = name
    backend.run = AsyncMock(
        return_value=BackendResult(name=name, model="sonnet", status=status, content=content, error=error)
    )
    return backend


class TestExpertBackendMapping(unittest.TestCase):
    """model name -> subscription-CLI backend selection."""

    def test_claude_family_maps_to_claude(self):
        for model in ("claude-opus-4", "sonnet", "opus", "haiku", "CLAUDE-3.5"):
            with self.subTest(model=model):
                name, matched = select_expert_backend_name(model)
                self.assertEqual(name, "claude")
                self.assertTrue(matched)

    def test_openai_family_maps_to_codex(self):
        for model in ("gpt-4o", "openai/gpt-5", "o1-preview", "o3-mini", "codex"):
            with self.subTest(model=model):
                name, matched = select_expert_backend_name(model)
                self.assertEqual(name, "codex")
                self.assertTrue(matched)

    def test_gemini_family_maps_to_agy(self):
        for model in ("gemini-2.5-pro", "flash", "Gemini 3.1 Pro", "gemini-flash"):
            with self.subTest(model=model):
                name, matched = select_expert_backend_name(model)
                self.assertEqual(name, "agy")
                self.assertTrue(matched)

    def test_unknown_model_falls_back_to_default_unmatched(self):
        name, matched = select_expert_backend_name("some-exotic-model-xyz")
        self.assertEqual(name, DEFAULT_EXPERT_BACKEND)
        self.assertFalse(matched)

    def test_none_model_falls_back_to_default(self):
        name, matched = select_expert_backend_name(None)
        self.assertEqual(name, DEFAULT_EXPERT_BACKEND)
        self.assertFalse(matched)

    def test_default_backend_env_override(self):
        with patch.dict("os.environ", {"PAL_EXPERT_CLI_DEFAULT_BACKEND": "codex"}):
            name, matched = select_expert_backend_name("totally-unknown")
            self.assertEqual(name, "codex")
            self.assertFalse(matched)

    def test_backend_for_model_returns_named_clibackend(self):
        self.assertIsInstance(backend_for_model("opus"), CliBackend)
        self.assertEqual(backend_for_model("opus").name, "claude")
        self.assertEqual(backend_for_model("gpt-4o").name, "codex")
        self.assertEqual(backend_for_model("gemini-2.5-pro").name, "agy")
        # Unknown -> default backend (still a valid CliBackend).
        self.assertEqual(backend_for_model("nope").name, DEFAULT_EXPERT_BACKEND)


class TestExpertAnalysisAdapter(unittest.IsolatedAsyncioTestCase):
    """BackendResult -> expert_analysis dict adapter, via AnalyzeTool."""

    def _tool_with_backend(self, backend):
        tool = AnalyzeTool()
        tool._model_context = Mock(capabilities=None)
        tool._current_model_name = "sonnet"
        tool.consolidated_findings = ConsolidatedFindings()
        # Avoid heavy context/file machinery — we only test the backend adapter.
        tool.prepare_expert_analysis_context = Mock(return_value="EXPERT CONTEXT")
        tool.should_include_files_in_expert_prompt = Mock(return_value=False)
        tool._resolve_expert_backend = Mock(return_value=backend)
        return tool

    async def test_success_json_is_parsed(self):
        backend = _fake_backend(content=json.dumps({"status": "analysis_complete", "raw_analysis": "ok"}))
        tool = self._tool_with_backend(backend)
        result = await tool._call_expert_analysis({}, Mock())
        backend.run.assert_awaited_once()
        self.assertEqual(result["status"], "analysis_complete")
        self.assertEqual(result["raw_analysis"], "ok")

    async def test_success_json_in_markdown_fence_is_parsed(self):
        fenced = "```json\n" + json.dumps({"status": "analysis_complete", "raw_analysis": "x"}) + "\n```"
        tool = self._tool_with_backend(_fake_backend(content=fenced))
        result = await tool._call_expert_analysis({}, Mock())
        self.assertEqual(result["status"], "analysis_complete")
        self.assertEqual(result["raw_analysis"], "x")

    async def test_success_plain_text_returns_raw_analysis(self):
        tool = self._tool_with_backend(_fake_backend(content="just some prose, not JSON"))
        result = await tool._call_expert_analysis({}, Mock())
        self.assertEqual(result["status"], "analysis_complete")
        self.assertEqual(result["format"], "text")
        self.assertEqual(result["raw_analysis"], "just some prose, not JSON")

    async def test_rate_limited_degrades_to_analysis_error(self):
        backend = _fake_backend(status="rate_limited", content="", error="rate limited / quota exhausted")
        tool = self._tool_with_backend(backend)
        result = await tool._call_expert_analysis({}, Mock())
        self.assertEqual(result["status"], "analysis_error")
        self.assertIn("rate limited", result["error"])

    async def test_backend_error_degrades_to_analysis_error(self):
        backend = _fake_backend(status="error", content="", error="executable 'claude' not found in PATH")
        tool = self._tool_with_backend(backend)
        result = await tool._call_expert_analysis({}, Mock())
        self.assertEqual(result["status"], "analysis_error")
        self.assertIn("not found", result["error"])

    async def test_empty_success_returns_empty_response(self):
        tool = self._tool_with_backend(_fake_backend(status="success", content=""))
        result = await tool._call_expert_analysis({}, Mock())
        self.assertEqual(result["status"], "empty_response")

    async def test_system_prompt_folded_into_cli_prompt(self):
        backend = _fake_backend(content=json.dumps({"status": "analysis_complete"}))
        tool = self._tool_with_backend(backend)
        await tool._call_expert_analysis({}, Mock())
        sent_prompt = backend.run.await_args.args[0]
        # The expert context must reach the single CLI prompt string.
        self.assertIn("EXPERT CONTEXT", sent_prompt)


if __name__ == "__main__":
    unittest.main(verbosity=2)

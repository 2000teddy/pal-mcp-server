"""Tests for ADR-002 Phase B — chat + consensus migrated to subscription-CLI backends.

Covers:
1. ``backend_result_to_model_response`` shim (success / error / rate_limited).
2. ``SimpleTool._run_cli_backend`` (chat path): folds system prompt, returns the
   shim + a ``cli:<backend>`` label, drives the chosen backend.
3. ``ConsensusTool._consult_model``: maps the model to a backend, success ->
   verdict, non-success -> per-model error (consensus stays partial-failure safe).
"""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from clink.consensus_backends import BackendResult, backend_result_to_model_response
from tools.chat import ChatTool
from tools.consensus import ConsensusTool


def _fake_backend(status="success", content="", error=None, name="claude"):
    backend = Mock()
    backend.name = name
    backend.run = AsyncMock(
        return_value=BackendResult(name=name, model="sonnet", status=status, content=content, error=error)
    )
    return backend


class TestBackendResultToModelResponse(unittest.TestCase):
    def test_success_maps_content_and_stop(self):
        r = backend_result_to_model_response(BackendResult("claude", "sonnet", "success", content="hello"), "opus")
        self.assertEqual(r.content, "hello")
        self.assertEqual(r.model_name, "opus")
        self.assertEqual(r.metadata["finish_reason"], "STOP")
        self.assertEqual(r.metadata["backend"], "claude")

    def test_error_maps_empty_and_non_stop(self):
        r = backend_result_to_model_response(
            BackendResult("claude", "sonnet", "error", content="", error="boom"), "opus"
        )
        self.assertEqual(r.content, "")
        self.assertNotEqual(r.metadata["finish_reason"], "STOP")
        self.assertEqual(r.metadata["finish_reason"], "error")
        self.assertEqual(r.metadata["cli_error"], "boom")

    def test_rate_limited_is_non_stop(self):
        r = backend_result_to_model_response(
            BackendResult("agy", "gemini", "rate_limited", content="", error="quota"), "flash"
        )
        self.assertEqual(r.metadata["finish_reason"], "rate_limited")


class TestChatRunCliBackend(unittest.IsolatedAsyncioTestCase):
    async def test_folds_system_prompt_and_labels_backend(self):
        tool = ChatTool()
        tool._current_model_name = "opus"
        backend = _fake_backend(content="the answer")
        with patch("clink.consensus_backends.backend_for_model", return_value=backend) as sel:
            model_response, provider_label = await tool._run_cli_backend("USER PROMPT", "SYS PROMPT")
        sel.assert_called_once_with("opus")
        backend.run.assert_awaited_once()
        sent = backend.run.await_args.args[0]
        self.assertIn("SYS PROMPT", sent)
        self.assertIn("USER PROMPT", sent)
        self.assertEqual(model_response.content, "the answer")
        self.assertEqual(provider_label, "cli:claude")

    async def test_no_system_prompt_passes_user_prompt_only(self):
        tool = ChatTool()
        tool._current_model_name = "opus"
        backend = _fake_backend(content="x")
        with patch("clink.consensus_backends.backend_for_model", return_value=backend):
            await tool._run_cli_backend("ONLY PROMPT", "")
        self.assertEqual(backend.run.await_args.args[0], "ONLY PROMPT")


class TestConsensusConsultModel(unittest.IsolatedAsyncioTestCase):
    def _tool(self):
        tool = ConsensusTool()
        tool.original_proposal = "Should we ship X?"
        tool.initial_prompt = "Should we ship X?"
        return tool

    def _request(self):
        return SimpleNamespace(relevant_files=[], images=None, continuation_id=None)

    async def test_success_returns_verdict_via_cli_backend(self):
        tool = self._tool()
        backend = _fake_backend(content="I am in favour.", name="claude")
        with (
            patch("tools.consensus.backend_for_model", return_value=backend) as sel,
            patch.object(tool, "_get_stance_enhanced_prompt", return_value="STANCE SYS"),
        ):
            result = await tool._consult_model({"model": "opus", "stance": "for"}, self._request())
        sel.assert_called_once_with("opus")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["verdict"], "I am in favour.")
        self.assertEqual(result["metadata"]["provider"], "cli:claude")
        # Stance system prompt must reach the single CLI prompt.
        self.assertIn("STANCE SYS", backend.run.await_args.args[0])

    async def test_backend_error_degrades_to_per_model_error(self):
        tool = self._tool()
        backend = _fake_backend(status="error", content="", error="executable 'agy' not found in PATH", name="agy")
        with (
            patch("tools.consensus.backend_for_model", return_value=backend),
            patch.object(tool, "_get_stance_enhanced_prompt", return_value="SYS"),
        ):
            result = await tool._consult_model({"model": "gemini-2.5-pro", "stance": "neutral"}, self._request())
        self.assertEqual(result["status"], "error")
        self.assertIn("not found", result["error"])

    async def test_rate_limited_degrades_to_per_model_error(self):
        tool = self._tool()
        backend = _fake_backend(status="rate_limited", content="", error="rate limited / quota exhausted")
        with (
            patch("tools.consensus.backend_for_model", return_value=backend),
            patch.object(tool, "_get_stance_enhanced_prompt", return_value="SYS"),
        ):
            result = await tool._consult_model({"model": "opus", "stance": "against"}, self._request())
        self.assertEqual(result["status"], "error")
        self.assertIn("rate limited", result["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

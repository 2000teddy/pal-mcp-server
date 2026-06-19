"""Key-free operation tests for the ADR-002 CLI migration (Phase E / Option B-plus).

Two guarantees:

1. **Key-free** — with NO provider registered (no API key) AND the CLI backends mocked,
   a full ``chat.execute()``, a workflow ``analyze.execute()`` and ``consensus.execute()``
   run end-to-end over the CLI backend WITHOUT ``ValueError``/``ToolExecutionError``. This
   is the Hub reality: pal runs without provider API keys.
2. **Regression** — WITH a provider present, the normal path is unchanged: the real
   provider capabilities are used (not the key-free defaults).

The migrated tools declare ``requires_model() == False`` (boundary-exempt) and resolve
their model context via ``ModelContext.resolve(allow_keyfree=True)``, which only falls back
to conservative CLI defaults when no provider exists.
"""

import json

import pytest

from providers.registry import ModelProviderRegistry
from tests.mock_helpers import create_mock_cli_backend, create_mock_provider
from utils.model_context import NO_PROVIDER_CONTEXT_WINDOW


def _simulate_no_provider(monkeypatch):
    """Force the no-provider (key-free) path regardless of the test registry."""
    monkeypatch.setattr(ModelProviderRegistry, "get_provider_for_model", lambda model_name=None: None)
    monkeypatch.setattr(ModelProviderRegistry, "get_available_model_names", lambda: [])


def _mock_cli_backends(monkeypatch, content="hello from the CLI backend"):
    """Mock the CLI backend selector at both import sites (chat/workflow lazy, consensus top-level)."""
    backend_factory = lambda *a, **k: create_mock_cli_backend(content=content)  # noqa: E731
    monkeypatch.setattr("clink.consensus_backends.backend_for_model", backend_factory)
    monkeypatch.setattr("tools.consensus.backend_for_model", backend_factory)


class TestKeyFreeOperation:
    """No provider / no API key — migrated tools must still run over the CLI backend."""

    def test_migrated_tools_are_boundary_exempt(self):
        from tools.analyze import AnalyzeTool
        from tools.chat import ChatTool
        from tools.consensus import ConsensusTool

        assert ChatTool().requires_model() is False
        assert AnalyzeTool().requires_model() is False
        assert ConsensusTool().requires_model() is False

    @pytest.mark.asyncio
    async def test_chat_execute_keyfree(self, tmp_path, monkeypatch):
        from tools.chat import ChatTool

        _simulate_no_provider(monkeypatch)
        _mock_cli_backends(monkeypatch, content="hi there from claude")

        tool = ChatTool()
        result = await tool.execute(
            {"prompt": "Say hello.", "model": "opus", "working_directory_absolute_path": str(tmp_path)}
        )
        assert len(result) == 1
        output = json.loads(result[0].text)
        assert output["status"] in ("success", "continuation_available")
        assert "hi there from claude" in output["content"]
        # The key-free default capabilities were used (no provider).
        assert tool._model_context.capabilities.context_window == NO_PROVIDER_CONTEXT_WINDOW

    @pytest.mark.asyncio
    async def test_workflow_analyze_execute_keyfree(self, tmp_path, monkeypatch):
        from tools.analyze import AnalyzeTool

        _simulate_no_provider(monkeypatch)
        _mock_cli_backends(monkeypatch, content="Expert analysis: the code looks correct.")

        target = tmp_path / "calc.py"
        target.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

        tool = AnalyzeTool()
        result = await tool.execute(
            {
                "step": "Analyze the add() helper.",
                "step_number": 1,
                "total_steps": 1,
                "next_step_required": False,
                "findings": "add(a, b) returns a + b.",
                "relevant_files": [str(target)],
                "model": "opus",
            }
        )
        assert result and len(result) == 1
        output = json.loads(result[0].text)
        # Reached + completed expert analysis over the CLI backend (no ValueError/ToolExecutionError).
        assert output.get("status") not in ("error", "analysis_error")
        assert "expert_analysis" in output

    @pytest.mark.asyncio
    async def test_consensus_execute_keyfree(self, monkeypatch):
        from tools.consensus import ConsensusTool

        _simulate_no_provider(monkeypatch)
        _mock_cli_backends(monkeypatch, content="I am broadly in favour.")

        tool = ConsensusTool()
        # Step 1 records the agent analysis and consults the first model over the CLI backend.
        result = await tool.execute(
            {
                "step": "My initial view: trunk-based development suits small teams.",
                "step_number": 1,
                "total_steps": 2,
                "next_step_required": True,
                "findings": "Initial analysis.",
                "models": [
                    {"model": "opus", "stance": "neutral"},
                    {"model": "gpt-5", "stance": "neutral"},
                ],
            }
        )
        assert result and len(result) == 1
        output = json.loads(result[0].text)
        assert output.get("status") != "error"
        # The consulted model's verdict (from the CLI backend) is present in the response.
        assert "in favour" in json.dumps(output)


class TestProviderRegressionUnchanged:
    """With a provider present, the normal path is unchanged (real capabilities, not defaults)."""

    @pytest.mark.asyncio
    async def test_chat_execute_with_provider_uses_real_capabilities(self, tmp_path, monkeypatch):
        from tools.chat import ChatTool

        mock_provider = create_mock_provider(model_name="gemini-2.5-flash", context_window=1_048_576)
        monkeypatch.setattr(ModelProviderRegistry, "get_provider_for_model", lambda model_name=None: mock_provider)
        # Generation is always CLI now; the provider only supplies the model context.
        _mock_cli_backends(monkeypatch, content="real-path response")

        tool = ChatTool()
        result = await tool.execute(
            {"prompt": "Hi", "model": "gemini-2.5-flash", "working_directory_absolute_path": str(tmp_path)}
        )
        assert len(result) == 1
        output = json.loads(result[0].text)
        assert output["status"] in ("success", "continuation_available")
        # Real provider capabilities were used — NOT the key-free default window.
        assert tool._model_context.capabilities.context_window == 1_048_576
        assert tool._model_context.capabilities.context_window != NO_PROVIDER_CONTEXT_WINDOW

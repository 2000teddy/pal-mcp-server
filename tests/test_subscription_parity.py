"""Parity tests: every model-calling tool must work identically in subscription mode.

Acceptance criterion from docs/cli_provider_plan.md §7.3: each of the 11
model-calling tools executes end-to-end with PAL_BACKEND=subscription, the
model call being served by the CLI provider (subprocess mocked — no real CLI
is launched). The tool sees a standard ModelResponse and completes with the
same output shape as in api mode.

All three ``generate_content`` call sites in the codebase are covered:
``tools/simple/base.py`` (chat), ``tools/workflow/workflow_mixin.py`` (the
workflow tools) and ``tools/consensus.py`` (consensus).
"""

import json
import shutil as real_shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

import server
from providers.registry import ModelProviderRegistry

MARKER = "PARITY-ANALYSIS-4711"

_ORIGINAL_WHICH = real_shutil.which


def _which_with_clis(name, *args, **kwargs):
    if name in ("claude", "codex", "agy"):
        return f"/usr/local/bin/{name}"
    return _ORIGINAL_WHICH(name, *args, **kwargs)


def _claude_stdout(result: str) -> str:
    return json.dumps({"type": "result", "result": result, "is_error": False})


def _codex_stdout(result: str) -> str:
    return json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": result}})


def _stdout_for_command(argv: list, answer: str) -> str:
    """Return output in the format the invoked CLI would produce."""
    executable = argv[0]
    if "codex" in executable:
        return _codex_stdout(answer)
    if "agy" in executable:
        return answer  # agy prints plain text
    return _claude_stdout(answer)


def _mock_popen(stdout: str):
    proc = MagicMock()
    proc.communicate.return_value = (stdout.encode(), b"")
    proc.returncode = 0
    proc.pid = 4711
    return proc


@pytest.fixture
def subscription_registry(monkeypatch):
    """Configure the provider registry exactly as the server does in subscription mode."""
    monkeypatch.setenv("PAL_BACKEND", "subscription")
    monkeypatch.setenv("DEFAULT_MODEL", "auto")
    ModelProviderRegistry.reset_for_testing()
    with patch("shutil.which", side_effect=_which_with_clis):
        server.configure_providers()
    yield
    ModelProviderRegistry.reset_for_testing()


@pytest.fixture
def cli_answer():
    """Mock the CLI subprocess to answer every model call with the marker text."""
    answer = f"{MARKER}: analysis text."
    with (
        patch("clink.cli_invoke.shutil.which", side_effect=_which_with_clis),
        patch(
            "clink.cli_invoke.subprocess.Popen",
            side_effect=lambda argv, **k: _mock_popen(_stdout_for_command(argv, answer)),
        ) as popen_cls,
    ):
        yield popen_cls


def _workflow_arguments(**overrides):
    args = {
        "step": "Final verification step for parity testing.",
        "step_number": 1,
        "total_steps": 1,
        "next_step_required": False,
        "findings": "Collected findings for the parity check.",
        "model": "sonnet",
    }
    args.update(overrides)
    return args


async def _run_tool(tool, arguments):
    result = await tool.execute(arguments)
    assert result and result[0].type == "text"
    return json.loads(result[0].text)


class TestSimpleToolParity:
    """Call site 1: tools/simple/base.py."""

    @pytest.mark.asyncio
    async def test_chat(self, subscription_registry, cli_answer):
        from tools.chat import ChatTool

        with tempfile.TemporaryDirectory() as tmpdir:
            parsed = await _run_tool(
                ChatTool(),
                {
                    "prompt": "Say the marker.",
                    "model": "sonnet",
                    "working_directory_absolute_path": tmpdir,
                },
            )
        assert parsed["status"] in ("success", "continuation_available")
        assert MARKER in parsed["content"]
        # The CLI subprocess actually served the call
        assert cli_answer.call_count >= 1
        # Parity: the tool reports the *requested* model name, exactly as in api mode
        assert parsed["metadata"]["model_used"] == "sonnet"


class TestWorkflowToolParity:
    """Call site 2: tools/workflow/workflow_mixin.py (expert analysis)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "tool_module,tool_class,extra_args",
        [
            ("tools.thinkdeep", "ThinkDeepTool", {}),
            ("tools.debug", "DebugIssueTool", {"confidence": "high"}),
            ("tools.codereview", "CodeReviewTool", {"confidence": "high"}),
            ("tools.precommit", "PrecommitTool", {}),
            ("tools.secaudit", "SecauditTool", {"confidence": "high"}),
            ("tools.analyze", "AnalyzeTool", {}),
            ("tools.refactor", "RefactorTool", {"confidence": "incomplete"}),
            ("tools.testgen", "TestGenTool", {"confidence": "high"}),
        ],
    )
    async def test_workflow_tool_expert_analysis_via_cli(
        self, subscription_registry, cli_answer, tool_module, tool_class, extra_args
    ):
        import importlib

        tool = getattr(importlib.import_module(tool_module), tool_class)()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def add(a, b):\n    return a + b\n")
            code_file = f.name

        arguments = _workflow_arguments(relevant_files=[code_file], **extra_args)
        if tool.get_name() == "precommit":
            arguments["path"] = "/tmp"

        parsed = await _run_tool(tool, arguments)

        assert "error" not in parsed.get("status", ""), f"{tool.get_name()} failed: {parsed}"
        expert = parsed.get("expert_analysis") or {}
        assert MARKER in json.dumps(expert), f"{tool.get_name()}: expert analysis did not run over the CLI provider"
        assert cli_answer.call_count >= 1

    @pytest.mark.asyncio
    async def test_docgen_completes_without_model_call(self, subscription_registry, cli_answer):
        """docgen drives its workflow without expert analysis — must still work in subscription mode."""
        from tools.docgen import DocgenTool

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("def add(a, b):\n    return a + b\n")
            code_file = f.name

        parsed = await _run_tool(
            DocgenTool(),
            _workflow_arguments(
                relevant_files=[code_file],
                num_files_documented=1,
                total_files_to_document=1,
            ),
        )
        assert "error" not in parsed.get("status", ""), f"docgen failed: {parsed}"


class TestConsensusParity:
    """Call site 3: tools/consensus.py — the classic consensus follows PAL_BACKEND."""

    @pytest.mark.asyncio
    async def test_consensus_consults_models_via_cli(self, subscription_registry, cli_answer):
        """Consensus consults one model per step: step 1 -> claude CLI, step 2 -> codex CLI."""
        from tools.consensus import ConsensusTool

        tool = ConsensusTool()
        models = [{"model": "sonnet"}, {"model": "gpt5"}]

        step1 = await _run_tool(
            tool,
            {
                "step": "Should we adopt the proposal? Give a verdict.",
                "step_number": 1,
                "total_steps": 2,
                "next_step_required": True,
                "findings": "Initial analysis of the proposal.",
                "models": models,
            },
        )
        assert "error" not in step1.get("status", ""), f"consensus step 1 failed: {step1}"
        assert MARKER in json.dumps(step1)
        assert cli_answer.call_count == 1

        step2 = await _run_tool(
            tool,
            {
                "step": "Consult the second model.",
                "step_number": 2,
                "total_steps": 2,
                "next_step_required": False,
                "findings": "Continuing the consultation.",
                "models": models,
                "continuation_id": step1.get("continuation_id"),
            },
        )
        assert "error" not in step2.get("status", ""), f"consensus step 2 failed: {step2}"
        # Second consultation was served by the codex CLI backend
        assert cli_answer.call_count == 2
        codex_argv = cli_answer.call_args[0][0]
        assert "codex" in codex_argv[0]


class TestBoundaryParity:
    """Interface-level parity for every catalogue model the 11 tools may pick."""

    def test_every_cli_model_serves_generate_content(self, subscription_registry, cli_answer):
        for model in ("sonnet", "opus", "gpt5", "pro", "flash", "o3"):
            provider = ModelProviderRegistry.get_provider_for_model(model)
            assert provider is not None, f"no provider for '{model}' in subscription mode"
            response = provider.generate_content(prompt="ping", model_name=model, temperature=0.2)
            assert MARKER in response.content
            assert response.provider.value == "cli"

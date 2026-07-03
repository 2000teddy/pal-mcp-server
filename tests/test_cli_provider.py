"""Unit tests for the subscription-CLI provider (PAL_BACKEND=subscription).

All subprocess interaction is mocked — no real CLI is launched. Live behaviour
against real CLIs is covered by the integration checklist in
docs/architecture/ADR-002-global-cli-backend.md.
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from clink.cli_invoke import (
    CliInvocationError,
    CliInvocationSpec,
    CliRateLimitError,
    run_cli_sync,
)
from providers.cli_provider import CLIModelProvider
from providers.shared import ProviderType

CLI_MODELS = ["cli-claude-sonnet", "cli-claude-opus", "cli-codex-gpt", "cli-agy-gemini-pro"]


def _claude_stdout(result: str = "Hello from Claude") -> str:
    return json.dumps({"type": "result", "result": result, "is_error": False})


def _mock_popen(stdout: str = "", stderr: str = "", returncode: int = 0):
    """Build a Popen mock whose communicate() returns the given streams."""
    proc = MagicMock()
    proc.communicate.return_value = (stdout.encode(), stderr.encode())
    proc.returncode = returncode
    proc.pid = 12345
    return proc


@pytest.fixture
def provider():
    return CLIModelProvider()


class TestCommandBuilding:
    """The argv shape per backend must match the proven cli_consensus commands."""

    def test_claude_command(self, provider):
        spec = provider._invocation_spec("cli-claude-sonnet")
        cmd = spec.build_command("PROMPT")
        assert cmd == ["claude", "--print", "--output-format", "json", "--model", "sonnet"]
        assert spec.prompt_mode == "stdin"  # prompt rides on stdin, not argv

    def test_claude_opus_command(self, provider):
        spec = provider._invocation_spec("cli-claude-opus")
        assert spec.build_command("x") == ["claude", "--print", "--output-format", "json", "--model", "opus"]

    def test_codex_command_without_model_flag(self, provider):
        spec = provider._invocation_spec("cli-codex-gpt")
        cmd = spec.build_command("PROMPT")
        # cli_model is null -> the CLI's subscription default model, no -m flag
        assert cmd == ["codex", "exec", "--skip-git-repo-check", "--sandbox", "read-only", "--json"]

    def test_agy_command_model_before_prompt_flag(self, provider):
        spec = provider._invocation_spec("cli-agy-gemini-pro")
        cmd = spec.build_command("PROMPT")
        # agy is arg-mode: model flag must come before -p, prompt is the last argv entry
        assert cmd == ["agy", "--model", "Gemini 3.1 Pro (Low)", "-p", "PROMPT"]


class TestAliasResolution:
    """Every alias a tool may request in api mode must resolve in subscription mode."""

    @pytest.mark.parametrize(
        "alias,expected",
        [
            ("sonnet", "cli-claude-sonnet"),
            ("claude", "cli-claude-sonnet"),
            ("flash", "cli-claude-sonnet"),
            ("gemini-2.5-flash", "cli-claude-sonnet"),
            ("flashlite", "cli-claude-sonnet"),
            ("mini", "cli-claude-sonnet"),
            ("nano", "cli-claude-sonnet"),
            ("opus", "cli-claude-opus"),
            ("claude-opus", "cli-claude-opus"),
            ("gpt5", "cli-codex-gpt"),
            ("gpt-5.5", "cli-codex-gpt"),
            ("chat-latest", "cli-codex-gpt"),
            ("o3", "cli-codex-gpt"),
            ("o3-pro", "cli-codex-gpt"),
            ("o4-mini", "cli-codex-gpt"),
            ("codex", "cli-codex-gpt"),
            ("gpt4.1", "cli-codex-gpt"),
            ("pro", "cli-agy-gemini-pro"),
            ("gemini", "cli-agy-gemini-pro"),
            ("gemini-3.1-pro-preview", "cli-agy-gemini-pro"),
            ("gemini-2.5-pro", "cli-agy-gemini-pro"),
        ],
    )
    def test_alias_resolves(self, provider, alias, expected):
        assert provider._resolve_model_name(alias) == expected
        assert provider.validate_model_name(alias) is True

    def test_all_api_catalogue_aliases_resolve(self, provider):
        """Mirror check: every alias in the Gemini/OpenAI API catalogues resolves here."""
        from providers.registries.gemini import GeminiModelRegistry
        from providers.registries.openai import OpenAIModelRegistry

        missing = []
        for registry_cls in (GeminiModelRegistry, OpenAIModelRegistry):
            registry = registry_cls()
            for model_name, capability, _ in registry.iter_entries():
                for candidate in [model_name, *capability.aliases]:
                    if not provider.validate_model_name(candidate):
                        missing.append(candidate)
        assert not missing, f"Unresolvable in subscription mode: {missing}"

    def test_unknown_model_rejected(self, provider):
        assert provider.validate_model_name("definitely-not-a-model") is False


class TestCapabilities:
    def test_provider_type(self, provider):
        assert provider.get_provider_type() == ProviderType.CLI

    def test_list_models_contains_catalogue(self, provider):
        models = provider.list_models(include_aliases=False)
        assert sorted(models) == sorted(CLI_MODELS)

    def test_capabilities_flags(self, provider):
        caps = provider.get_capabilities("sonnet")
        assert caps.provider == ProviderType.CLI
        assert caps.supports_images is False
        assert caps.supports_temperature is False

    def test_preferred_model_categories(self, provider):
        from tools.models import ToolModelCategory

        allowed = list(CLI_MODELS)
        assert provider.get_preferred_model(ToolModelCategory.EXTENDED_REASONING, allowed) == "cli-claude-opus"
        assert provider.get_preferred_model(ToolModelCategory.FAST_RESPONSE, allowed) == "cli-claude-sonnet"
        assert provider.get_preferred_model(ToolModelCategory.BALANCED, allowed) == "cli-claude-sonnet"
        assert provider.get_preferred_model(ToolModelCategory.BALANCED, []) is None


class TestRunCliSync:
    """Failure semantics of the synchronous invocation layer."""

    def _spec(self, **overrides):
        defaults = {
            "name": "claude-test",
            "executable": "claude",
            "parser_name": "claude_json",
            "prompt_mode": "stdin",
            "pre_model_args": ["--print", "--output-format", "json"],
            "cli_model": "sonnet",
        }
        defaults.update(overrides)
        return CliInvocationSpec(**defaults)

    def test_success_returns_content_and_metadata(self):
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/usr/local/bin/claude"),
            patch("clink.cli_invoke.subprocess.Popen", return_value=_mock_popen(_claude_stdout("Answer"))),
        ):
            content, metadata = run_cli_sync(self._spec(), "prompt")
        assert content == "Answer"
        assert metadata["returncode"] == 0
        assert metadata["cli_backend"] == "claude-test"

    def test_timestamp_prefix_is_stripped(self):
        stdout = _claude_stdout("**⏱ 10:45:31 — 2026-07-03**\n\nActual answer")
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/claude"),
            patch("clink.cli_invoke.subprocess.Popen", return_value=_mock_popen(stdout)),
        ):
            content, _ = run_cli_sync(self._spec(), "prompt")
        assert content == "Actual answer"

    def test_missing_executable_raises(self):
        with patch("clink.cli_invoke.shutil.which", return_value=None):
            with pytest.raises(CliInvocationError, match="not found in PATH"):
                run_cli_sync(self._spec(), "prompt")

    def test_timeout_kills_and_raises(self):
        proc = _mock_popen()
        proc.communicate.side_effect = [subprocess.TimeoutExpired(cmd="claude", timeout=1), (b"", b"")]
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/claude"),
            patch("clink.cli_invoke.subprocess.Popen", return_value=proc),
            patch("clink.cli_invoke.os.getpgid", return_value=12345),
            patch("clink.cli_invoke.os.killpg") as killpg,
        ):
            with pytest.raises(CliInvocationError, match="timeout"):
                run_cli_sync(self._spec(timeout=1), "prompt")
        killpg.assert_called_once()  # whole process group killed, not just the child

    def test_empty_content_raises(self):
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/claude"),
            patch("clink.cli_invoke.subprocess.Popen", return_value=_mock_popen(_claude_stdout(""))),
        ):
            with pytest.raises(CliInvocationError):
                run_cli_sync(self._spec(), "prompt")

    def test_rate_limit_in_stderr_raises_rate_limit_error(self):
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/claude"),
            patch(
                "clink.cli_invoke.subprocess.Popen",
                return_value=_mock_popen(_claude_stdout("partial"), stderr="429 rate limit exceeded"),
            ),
        ):
            with pytest.raises(CliRateLimitError):
                run_cli_sync(self._spec(), "prompt")

    def test_answer_discussing_rate_limits_is_not_misclassified(self):
        """A parsed answer that merely *talks about* rate limits must succeed."""
        stdout = _claude_stdout("Rate limits (429) are a common API quota mechanism.")
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/claude"),
            patch("clink.cli_invoke.subprocess.Popen", return_value=_mock_popen(stdout)),
        ):
            content, _ = run_cli_sync(self._spec(), "prompt")
        assert "quota mechanism" in content

    def test_arg_mode_prompt_size_guard(self):
        spec = self._spec(prompt_mode="arg", post_model_args=["-p"])
        with pytest.raises(CliInvocationError, match="too large"):
            run_cli_sync(spec, "x" * (100 * 1024))

    def test_stdin_prompt_not_on_argv(self):
        popen = _mock_popen(_claude_stdout("ok"))
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/claude"),
            patch("clink.cli_invoke.subprocess.Popen", return_value=popen) as popen_cls,
        ):
            run_cli_sync(self._spec(), "SECRET-PROMPT")
        argv = popen_cls.call_args[0][0]
        assert "SECRET-PROMPT" not in argv
        popen.communicate.assert_called_once()
        assert b"SECRET-PROMPT" in popen.communicate.call_args[0][0]


class TestGenerateContent:
    """The provider must return a standard ModelResponse — tools see no difference."""

    def _generate(self, provider, **kwargs):
        defaults = {
            "prompt": "What is 2+2?",
            "model_name": "sonnet",
            "system_prompt": "You are terse.",
            "temperature": 0.7,
        }
        defaults.update(kwargs)
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/claude"),
            patch(
                "clink.cli_invoke.subprocess.Popen",
                return_value=_mock_popen(_claude_stdout("4")),
            ) as popen_cls,
        ):
            response = provider.generate_content(**defaults)
        return response, popen_cls

    def test_returns_model_response(self, provider):
        response, _ = self._generate(provider)
        assert response.content == "4"
        assert response.model_name == "cli-claude-sonnet"
        assert response.provider == ProviderType.CLI
        assert response.friendly_name == "CLI (Claude Sonnet via Claude Max)"
        assert response.usage["total_tokens"] == response.usage["input_tokens"] + response.usage["output_tokens"]
        assert response.metadata["cli_backend"] == "cli-claude-sonnet"

    def test_system_prompt_is_folded_into_stdin(self, provider):
        _, popen_cls = self._generate(provider)
        proc = popen_cls.return_value
        stdin_payload = proc.communicate.call_args[0][0].decode()
        assert stdin_payload.startswith("You are terse.")
        assert "What is 2+2?" in stdin_payload

    def test_tuning_params_are_ignored_not_rejected(self, provider):
        """temperature/thinking_mode/max_output_tokens must not break the call."""
        response, _ = self._generate(
            provider,
            temperature=1.5,
            max_output_tokens=123,
            thinking_mode="high",
            top_p=0.9,
        )
        assert response.content == "4"

    def test_images_are_rejected_with_clear_error(self, provider):
        with pytest.raises(ValueError, match="does not support image"):
            provider.generate_content(
                prompt="Describe this",
                model_name="sonnet",
                images=["/tmp/pic.png"],
            )

    def test_alias_resolves_to_backend_command(self, provider):
        """Requesting 'gpt5' must invoke the codex CLI."""
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/codex"),
            patch(
                "clink.cli_invoke.subprocess.Popen",
                return_value=_mock_popen(
                    json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "4"}})
                ),
            ) as popen_cls,
        ):
            response = provider.generate_content(prompt="2+2?", model_name="gpt5")
        argv = popen_cls.call_args[0][0]
        assert argv[0] == "/bin/codex"
        assert "exec" in argv
        assert response.model_name == "cli-codex-gpt"

    def test_rate_limit_is_not_retried(self, provider):
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/claude"),
            patch(
                "clink.cli_invoke.subprocess.Popen",
                return_value=_mock_popen(_claude_stdout("x"), stderr="429 rate limit"),
            ) as popen_cls,
        ):
            with pytest.raises(CliRateLimitError):
                provider.generate_content(prompt="hi", model_name="sonnet")
        assert popen_cls.call_count == 1  # no retry on rate limits

    def test_transient_failure_is_retried_once(self, provider):
        good = _mock_popen(_claude_stdout("recovered"))
        bad = _mock_popen()
        bad.communicate.side_effect = [subprocess.TimeoutExpired(cmd="claude", timeout=1), (b"", b"")]
        with (
            patch("clink.cli_invoke.shutil.which", return_value="/bin/claude"),
            patch("clink.cli_invoke.subprocess.Popen", side_effect=[bad, good]),
            patch("clink.cli_invoke.os.killpg"),
            patch("providers.base.time.sleep"),
        ):
            response = provider.generate_content(prompt="hi", model_name="sonnet")
        assert response.content == "recovered"

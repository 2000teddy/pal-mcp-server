"""Tests for the global PAL_BACKEND switch (ADR-002).

``subscription`` (default) registers the CLI provider plus MiniMax and keeps
all open per-token API providers unregistered; ``api`` is the emergency
fallback restoring the full historical API behaviour.
"""

from unittest.mock import patch

import pytest

import server
from providers.registry import ModelProviderRegistry
from providers.shared import ProviderType

REAL_KEY_ENVS = {
    "GEMINI_API_KEY": "test-gemini-key",
    "OPENAI_API_KEY": "test-openai-key",
    "MINIMAX_API_KEY": "test-minimax-key",
}

OPEN_API_PROVIDERS = {
    ProviderType.GOOGLE,
    ProviderType.OPENAI,
    ProviderType.AZURE,
    ProviderType.XAI,
    ProviderType.DIAL,
    ProviderType.OPENROUTER,
    ProviderType.CUSTOM,
}


@pytest.fixture(autouse=True)
def clean_registry(monkeypatch):
    """Isolate the singleton registry and give every test a full set of API keys."""
    ModelProviderRegistry.reset_for_testing()
    for env, value in REAL_KEY_ENVS.items():
        monkeypatch.setenv(env, value)
    monkeypatch.delenv("CUSTOM_API_URL", raising=False)
    yield
    ModelProviderRegistry.reset_for_testing()


def _registered() -> set[ProviderType]:
    return set(ModelProviderRegistry.get_available_providers())


class TestSubscriptionMode:
    def _configure(self, monkeypatch, backend_value=None, clis_present=True):
        if backend_value is None:
            monkeypatch.delenv("PAL_BACKEND", raising=False)
        else:
            monkeypatch.setenv("PAL_BACKEND", backend_value)
        which = (lambda name: f"/usr/local/bin/{name}") if clis_present else (lambda name: None)
        with patch("shutil.which", side_effect=which):
            server.configure_providers()

    def test_default_is_subscription(self, monkeypatch):
        """PAL_BACKEND unset must behave exactly like PAL_BACKEND=subscription."""
        self._configure(monkeypatch, backend_value=None)
        assert ProviderType.CLI in _registered()
        assert not (_registered() & OPEN_API_PROVIDERS)

    def test_subscription_registers_cli_and_minimax_only(self, monkeypatch):
        self._configure(monkeypatch, backend_value="subscription")
        assert _registered() == {ProviderType.CLI, ProviderType.MINIMAX}

    def test_cli_provider_wins_model_resolution(self, monkeypatch):
        from providers.cli_provider import CLIModelProvider

        self._configure(monkeypatch, backend_value="subscription")
        provider = ModelProviderRegistry.get_provider_for_model("sonnet")
        assert isinstance(provider, CLIModelProvider)
        # Aliases of the disabled API providers must also land on the CLI provider
        for alias in ("flash", "pro", "gpt5", "o3", "opus"):
            provider = ModelProviderRegistry.get_provider_for_model(alias)
            assert isinstance(provider, CLIModelProvider), f"alias '{alias}' did not resolve to CLI"

    def test_minimax_still_resolves_its_own_models(self, monkeypatch):
        from providers.minimax import MiniMaxModelProvider

        self._configure(monkeypatch, backend_value="subscription")
        provider = ModelProviderRegistry.get_provider_for_model("minimax")
        assert isinstance(provider, MiniMaxModelProvider)

    def test_no_minimax_key_means_cli_only(self, monkeypatch):
        monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
        self._configure(monkeypatch, backend_value="subscription")
        assert _registered() == {ProviderType.CLI}

    def test_auto_fallback_prefers_cli_models(self, monkeypatch):
        from tools.models import ToolModelCategory

        self._configure(monkeypatch, backend_value="subscription")
        assert (
            ModelProviderRegistry.get_preferred_fallback_model(ToolModelCategory.EXTENDED_REASONING)
            == "cli-claude-opus"
        )
        assert (
            ModelProviderRegistry.get_preferred_fallback_model(ToolModelCategory.FAST_RESPONSE) == "cli-claude-sonnet"
        )

    def test_missing_all_clis_fails_loudly(self, monkeypatch):
        with pytest.raises(ValueError, match="none of the subscription CLIs"):
            self._configure(monkeypatch, backend_value="subscription", clis_present=False)
        # And crucially: no silent fallback onto open API providers
        assert not (_registered() & OPEN_API_PROVIDERS)

    def test_case_insensitive_value(self, monkeypatch):
        self._configure(monkeypatch, backend_value="  SUBSCRIPTION ")
        assert ProviderType.CLI in _registered()


class TestApiMode:
    def test_api_mode_restores_full_api_behaviour(self, monkeypatch):
        monkeypatch.setenv("PAL_BACKEND", "api")
        server.configure_providers()
        registered = _registered()
        assert ProviderType.CLI not in registered
        assert ProviderType.GOOGLE in registered
        assert ProviderType.OPENAI in registered
        assert ProviderType.MINIMAX in registered

    def test_api_mode_resolves_models_via_api_providers(self, monkeypatch):
        from providers.gemini import GeminiModelProvider

        monkeypatch.setenv("PAL_BACKEND", "api")
        server.configure_providers()
        provider = ModelProviderRegistry.get_provider_for_model("flash")
        assert isinstance(provider, GeminiModelProvider)

    def test_api_mode_without_any_key_still_fails(self, monkeypatch):
        monkeypatch.setenv("PAL_BACKEND", "api")
        for env in REAL_KEY_ENVS:
            monkeypatch.delenv(env, raising=False)
        for env in ("XAI_API_KEY", "DIAL_API_KEY", "OPENROUTER_API_KEY", "AZURE_OPENAI_API_KEY", "CUSTOM_API_URL"):
            monkeypatch.delenv(env, raising=False)
        with pytest.raises(ValueError, match="At least one API configuration is required"):
            server.configure_providers()


class TestInvalidValue:
    def test_unknown_backend_value_raises(self, monkeypatch):
        monkeypatch.setenv("PAL_BACKEND", "hybrid")
        with pytest.raises(ValueError, match="Invalid PAL_BACKEND"):
            server.configure_providers()

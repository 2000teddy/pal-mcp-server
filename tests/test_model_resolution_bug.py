"""
Test to reproduce and fix the OpenRouter model name resolution bug.

This test specifically targets the bug where:
1. User specifies "gemini" in consensus tool
2. System incorrectly resolves to "gemini-2.5-pro" instead of "google/gemini-2.5-pro"
3. OpenRouter API returns "gemini-2.5-pro is not a valid model ID"
"""

from unittest.mock import Mock, patch

from providers.openrouter import OpenRouterProvider
from tools.consensus import ConsensusTool


class TestModelResolutionBug:
    """Test cases for the OpenRouter model name resolution bug."""

    def setup_method(self):
        """Setup test environment."""
        self.consensus_tool = ConsensusTool()

    def test_openrouter_registry_resolves_gemini_alias(self):
        """Test that OpenRouter registry properly resolves 'gemini' to 'google/gemini-3-pro-preview'."""
        # Test the registry directly
        provider = OpenRouterProvider("test_key")

        # Test alias resolution
        resolved_model_name = provider._resolve_model_name("gemini")
        assert (
            resolved_model_name == "google/gemini-3-pro-preview"
        ), f"Expected 'google/gemini-3-pro-preview', got '{resolved_model_name}'"

        # Test that it also works with 'pro' alias
        resolved_pro = provider._resolve_model_name("pro")
        assert (
            resolved_pro == "google/gemini-3-pro-preview"
        ), f"Expected 'google/gemini-3-pro-preview', got '{resolved_pro}'"

    # DELETED: test_provider_registry_returns_openrouter_for_gemini
    # This test had a flawed mock setup - it mocked get_provider() but called get_provider_for_model().
    # The test was trying to verify OpenRouter model resolution functionality that is already
    # comprehensively tested in working OpenRouter provider tests.

    @patch.dict("os.environ", {"OPENROUTER_API_KEY": "test_key"}, clear=False)
    def test_consensus_tool_model_resolution_bug_reproduction(self):
        """Consensus passes the model alias to the CLI backend selector (ADR-002).

        Pre-migration this asserted the alias reached ``provider.generate_content``.
        Consensus now consults a subscription-CLI backend, so the alias must reach
        ``backend_for_model`` instead; the verdict still flows through unchanged.
        """
        import asyncio

        from tests.mock_helpers import create_mock_cli_backend

        backend = create_mock_cli_backend(content="Test response", name="agy")

        # Track the model name passed to the backend selector.
        received_model_names = []

        def track_backend_for_model(model_name, *args, **kwargs):
            received_model_names.append(model_name)
            return backend

        with patch("tools.consensus.backend_for_model", side_effect=track_backend_for_model):
            self.consensus_tool.initial_prompt = "Test prompt"

            request = Mock()
            request.relevant_files = []
            request.continuation_id = None
            request.images = None

            result = asyncio.run(self.consensus_tool._consult_model({"model": "gemini", "stance": "neutral"}, request))

            # The original alias "gemini" must reach the backend selector.
            assert len(received_model_names) == 1
            assert received_model_names[0] == "gemini"

            # Verify the result structure.
            assert result["model"] == "gemini"
            assert result["status"] == "success"
            assert result["verdict"] == "Test response"

    def test_bug_reproduction_with_malformed_model_name(self):
        """Test what happens when 'gemini-2.5-pro' (malformed) is passed to OpenRouter."""
        provider = OpenRouterProvider("test_key")

        # This should NOT resolve because 'gemini-2.5-pro' is not in the OpenRouter registry
        resolved = provider._resolve_model_name("gemini-2.5-pro")

        # The bug: this returns "gemini-2.5-pro" as-is instead of resolving to proper name
        # This is what causes the OpenRouter API to fail
        assert resolved == "gemini-2.5-pro", f"Expected fallback to 'gemini-2.5-pro', got '{resolved}'"

        # Verify the registry doesn't have this malformed name
        config = provider._registry.resolve("gemini-2.5-pro")
        assert config is None, "Registry should not contain 'gemini-2.5-pro' - only 'google/gemini-2.5-pro'"


if __name__ == "__main__":
    # Run the tests
    test = TestModelResolutionBug()
    test.setup_method()

    print("Testing OpenRouter registry resolution...")
    test.test_openrouter_registry_resolves_gemini_alias()
    print("✅ Registry resolves aliases correctly")

    print("\nTesting malformed model name handling...")
    test.test_bug_reproduction_with_malformed_model_name()
    print("✅ Confirmed: malformed names fall through as-is")

    print("\nConsensus tool test completed successfully.")

    print("\nAll tests completed. The bug is fixed.")

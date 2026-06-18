"""Helper functions for test mocking."""

from unittest.mock import AsyncMock, Mock

from providers.shared import ModelCapabilities, ProviderType, RangeTemperatureConstraint


def create_mock_cli_backend(content="Test response", name="claude", status="success", error=None):
    """Create a mock subscription-CLI backend (ADR-002).

    Workflow/chat/consensus generation now goes through
    ``clink.consensus_backends.backend_for_model(...).run(prompt)`` instead of
    ``provider.generate_content(...)``. Patch ``backend_for_model`` to return this.
    ``backend.run`` is an AsyncMock yielding a ``BackendResult``; ``run.await_args``
    captures the single CLI prompt string for assertions.
    """
    from clink.consensus_backends import BackendResult

    backend = Mock()
    backend.name = name
    backend.run = AsyncMock(
        return_value=BackendResult(name=name, model="sonnet", status=status, content=content, error=error)
    )
    return backend


def create_mock_provider(model_name="gemini-2.5-flash", context_window=1_048_576):
    """Create a properly configured mock provider."""
    mock_provider = Mock()

    # Set up capabilities
    mock_capabilities = ModelCapabilities(
        provider=ProviderType.GOOGLE,
        model_name=model_name,
        friendly_name="Gemini",
        context_window=context_window,
        max_output_tokens=8192,
        supports_extended_thinking=False,
        supports_system_prompts=True,
        supports_streaming=True,
        supports_function_calling=True,
        temperature_constraint=RangeTemperatureConstraint(0.0, 2.0, 0.7),
    )

    mock_provider.get_capabilities.return_value = mock_capabilities
    mock_provider.get_provider_type.return_value = ProviderType.GOOGLE
    mock_provider.validate_model_name.return_value = True

    # Set up generate_content response
    mock_response = Mock()
    mock_response.content = "Test response"
    mock_response.usage = {"input_tokens": 10, "output_tokens": 20}
    mock_response.model_name = model_name
    mock_response.friendly_name = "Gemini"
    mock_response.provider = ProviderType.GOOGLE
    mock_response.metadata = {"finish_reason": "STOP"}

    mock_provider.generate_content.return_value = mock_response

    return mock_provider

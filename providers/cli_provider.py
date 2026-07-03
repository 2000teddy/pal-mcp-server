"""Subscription-CLI model provider (PAL_BACKEND=subscription).

Routes ``generate_content`` calls to local, subscription-authenticated CLIs
(Claude Max via ``claude``, ChatGPT via ``codex``, Google One via ``agy``)
instead of paid provider APIs. Tools are completely unaware of the difference:
they talk to the standard :class:`ModelProvider` interface and receive a
standard :class:`ModelResponse`.

Design notes (see docs/architecture/ADR-002-global-cli-backend.md):

* ``generate_content`` is synchronous by contract and is invoked from within
  the server's event loop, so the CLI runs as a **blocking** subprocess via
  :func:`clink.cli_invoke.run_cli_sync` — never ``asyncio`` (deadlock).
* Tuning parameters the CLIs cannot honour (``temperature``, ``thinking_mode``,
  ``max_output_tokens``, ``top_p`` …) are accepted and ignored so tool call
  sites work unchanged in both backend modes.
* Image inputs are rejected with a clear error (``supports_images=False``).
* Failures surface as exceptions, mirroring the API providers (unlike the
  partial-failure contract of ``cli_consensus``).
"""

import logging
from typing import TYPE_CHECKING, ClassVar, Optional

if TYPE_CHECKING:
    from tools.models import ToolModelCategory

from clink.cli_invoke import CliInvocationSpec, run_cli_sync

from .base import ModelProvider
from .registries.cli import CLIModelRegistry
from .registry_provider_mixin import RegistryBackedProviderMixin
from .shared import ModelCapabilities, ModelResponse, ProviderType

logger = logging.getLogger(__name__)


class CLIModelProvider(RegistryBackedProviderMixin, ModelProvider):
    """Provider that fulfils model requests through subscription CLIs."""

    FRIENDLY_NAME = "CLI"

    REGISTRY_CLASS = CLIModelRegistry
    MODEL_CAPABILITIES: ClassVar[dict[str, ModelCapabilities]] = {}

    # Preferred catalogue models per tool category (auto mode).
    PREFERRED_EXTENDED_REASONING = "cli-claude-opus"
    PREFERRED_DEFAULT = "cli-claude-sonnet"

    def __init__(self, api_key: str = "", **kwargs):
        """No API key required — authentication lives in the CLIs' own sessions."""
        self._ensure_registry()
        super().__init__(api_key or "", **kwargs)
        self._invalidate_capability_cache()

    def get_provider_type(self) -> ProviderType:
        return ProviderType.CLI

    def get_preferred_model(self, category: "ToolModelCategory", allowed_models: list[str]) -> Optional[str]:
        from tools.models import ToolModelCategory

        if not allowed_models:
            return None
        if category == ToolModelCategory.EXTENDED_REASONING and self.PREFERRED_EXTENDED_REASONING in allowed_models:
            return self.PREFERRED_EXTENDED_REASONING
        if self.PREFERRED_DEFAULT in allowed_models:
            return self.PREFERRED_DEFAULT
        return allowed_models[0]

    def generate_content(
        self,
        prompt: str,
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
        max_output_tokens: Optional[int] = None,
        **kwargs,
    ) -> ModelResponse:
        capabilities = self.get_capabilities(model_name)
        canonical_name = capabilities.model_name

        images = kwargs.get("images")
        if images:
            raise ValueError(
                f"Model '{canonical_name}' runs over a subscription CLI and does not support image "
                "inputs. Remove the images or switch PAL_BACKEND to 'api'."
            )
        # temperature / thinking_mode / max_output_tokens / top_p etc. are accepted but
        # ignored: the subscription CLIs expose no equivalent tuning knobs. This keeps
        # tool call sites identical across PAL_BACKEND modes.

        spec = self._invocation_spec(canonical_name)

        # The CLIs take a single prompt stream; fold the system prompt in on top.
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        logger.info("CLI provider: '%s' -> backend '%s'", canonical_name, spec.name)
        content, metadata = self._run_with_retries(
            operation=lambda: run_cli_sync(spec, full_prompt),
            max_attempts=2,
            delays=[1.0],
            log_prefix=f"CLI({spec.name})",
        )

        return ModelResponse(
            content=content,
            usage=self._estimate_usage(full_prompt, content, canonical_name),
            model_name=canonical_name,
            friendly_name=capabilities.friendly_name,
            provider=ProviderType.CLI,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _invocation_spec(self, canonical_name: str) -> CliInvocationSpec:
        entry = self._registry.get_entry(canonical_name) if self._registry else None
        cli_config = (entry or {}).get("cli")
        if not cli_config:
            raise ValueError(f"No CLI invocation config found for model '{canonical_name}' in cli_models.json.")
        return CliInvocationSpec.from_config(canonical_name, cli_config)

    def _estimate_usage(self, prompt: str, content: str, canonical_name: str) -> dict[str, int]:
        input_tokens = self.count_tokens(prompt, canonical_name)
        output_tokens = self.count_tokens(content, canonical_name)
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        }

    def _is_error_retryable(self, error: Exception) -> bool:
        from clink.cli_invoke import CliRateLimitError

        if isinstance(error, CliRateLimitError):
            return False
        return super()._is_error_retryable(error)


CLIModelProvider._ensure_registry()

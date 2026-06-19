"""
Model context management for dynamic token allocation.

This module provides a clean abstraction for model-specific token management,
ensuring that token limits are properly calculated based on the current model
being used, not global constants.

CONVERSATION MEMORY INTEGRATION:
This module works closely with the conversation memory system to provide
optimal token allocation for multi-turn conversations:

1. DUAL PRIORITIZATION STRATEGY SUPPORT:
   - Provides separate token budgets for conversation history vs. files
   - Enables the conversation memory system to apply newest-first prioritization
   - Ensures optimal balance between context preservation and new content

2. MODEL-SPECIFIC ALLOCATION:
   - Dynamic allocation based on model capabilities (context window size)
   - Conservative allocation for smaller models (O3: 200K context)
   - Generous allocation for larger models (Gemini: 1M+ context)
   - Adapts token distribution ratios based on model capacity

3. CROSS-TOOL CONSISTENCY:
   - Provides consistent token budgets across different tools
   - Enables seamless conversation continuation between tools
   - Supports conversation reconstruction with proper budget management
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from config import DEFAULT_MODEL
from providers import ModelCapabilities, ModelProviderRegistry

logger = logging.getLogger(__name__)


@dataclass
class TokenAllocation:
    """Token allocation strategy for a model."""

    total_tokens: int
    content_tokens: int
    response_tokens: int
    file_tokens: int
    history_tokens: int

    @property
    def available_for_prompt(self) -> int:
        """Tokens available for the actual prompt after allocations."""
        return self.content_tokens - self.file_tokens - self.history_tokens


# Default context window used when a tool runs WITHOUT a registered provider
# (ADR-002 key-free CLI operation). Conservative so token budgeting does not
# overshoot a CLI's real context. Tunable.
NO_PROVIDER_CONTEXT_WINDOW = 200_000


def default_no_provider_capabilities(model_name: str) -> ModelCapabilities:
    """Conservative, provider-free capabilities for key-free CLI tools (ADR-002).

    Used ONLY when no provider/API key is registered for ``model_name`` AND the
    tool declared it does not require a provider (``requires_model() == False``).
    Generation runs over subscription-CLI backends, so these capabilities only
    feed model-context consumers (system-prompt augmentation, token budgeting,
    temperature validation) — never a real provider call.
    """
    from providers.shared import ProviderType, RangeTemperatureConstraint

    return ModelCapabilities(
        provider=ProviderType.CUSTOM,
        model_name=model_name,
        friendly_name=f"CLI:{model_name}",
        context_window=NO_PROVIDER_CONTEXT_WINDOW,
        max_output_tokens=64_000,
        supports_extended_thinking=False,
        supports_system_prompts=True,
        supports_streaming=False,
        supports_function_calling=False,
        supports_images=False,
        supports_json_mode=False,
        supports_temperature=False,  # CLI backends take no temperature
        allow_code_generation=False,  # conservative default (tunable)
        temperature_constraint=RangeTemperatureConstraint(0.0, 2.0, 0.3),
    )


class ModelContext:
    """
    Encapsulates model-specific information and token calculations.

    This class provides a single source of truth for all model-related
    token calculations, ensuring consistency across the system.
    """

    def __init__(self, model_name: str, model_option: Optional[str] = None):
        self.model_name = model_name
        self.model_option = model_option  # Store optional model option (e.g., "for", "against", etc.)
        self._provider = None
        self._capabilities = None
        self._token_allocation = None

    @property
    def provider(self):
        """Get the model provider lazily."""
        if self._provider is None:
            self._provider = ModelProviderRegistry.get_provider_for_model(self.model_name)
            if not self._provider:
                available_models = ModelProviderRegistry.get_available_model_names()
                if available_models:
                    available_text = ", ".join(available_models)
                else:
                    available_text = (
                        "No models detected. Configure provider credentials or set DEFAULT_MODEL to a valid option."
                    )

                raise ValueError(
                    f"Model '{self.model_name}' is not available with current API keys. Available models: {available_text}."
                )
        return self._provider

    @property
    def capabilities(self) -> ModelCapabilities:
        """Get model capabilities lazily."""
        if self._capabilities is None:
            self._capabilities = self.provider.get_capabilities(self.model_name)
        return self._capabilities

    @classmethod
    def resolve(cls, model_name: str, *, allow_keyfree: bool = False, model_option: Optional[str] = None):
        """Build a ModelContext, tolerating a missing provider for key-free CLI tools.

        Normal path (``allow_keyfree=False``): identical to ``ModelContext(model_name)`` —
        the provider resolves lazily and raises if absent (fail-fast for real API tools
        is preserved).

        Key-free path (``allow_keyfree=True``, set by tools with ``requires_model()==False``):
        if a provider IS registered the real capabilities are used unchanged; only when
        no provider exists (no API key) do conservative CLI defaults kick in. Defaults
        therefore NEVER mask a missing key for a tool that genuinely needs a provider.
        """
        ctx = cls(model_name, model_option)
        if not allow_keyfree:
            return ctx
        try:
            _ = ctx.capabilities  # force provider resolution now
        except ValueError:
            ctx._capabilities = default_no_provider_capabilities(model_name)
            logger.info(
                "No provider for model '%s' — using key-free CLI default capabilities (window=%d)",
                model_name,
                NO_PROVIDER_CONTEXT_WINDOW,
            )
        return ctx

    def calculate_token_allocation(self, reserved_for_response: Optional[int] = None) -> TokenAllocation:
        """
        Calculate token allocation based on model capacity and conversation requirements.

        This method implements the core token budget calculation that supports the
        dual prioritization strategy used in conversation memory and file processing:

        TOKEN ALLOCATION STRATEGY:
        1. CONTENT vs RESPONSE SPLIT:
           - Smaller models (< 300K): 60% content, 40% response (conservative)
           - Larger models (≥ 300K): 80% content, 20% response (generous)

        2. CONTENT SUB-ALLOCATION:
           - File tokens: 30-40% of content budget for newest file versions
           - History tokens: 40-50% of content budget for conversation context
           - Remaining: Available for tool-specific prompt content

        3. CONVERSATION MEMORY INTEGRATION:
           - History allocation enables conversation reconstruction in reconstruct_thread_context()
           - File allocation supports newest-first file prioritization in tools
           - Remaining budget passed to tools via _remaining_tokens parameter

        Args:
            reserved_for_response: Override response token reservation

        Returns:
            TokenAllocation with calculated budgets for dual prioritization strategy
        """
        total_tokens = self.capabilities.context_window

        # Dynamic allocation based on model capacity
        if total_tokens < 300_000:
            # Smaller context models (O3): Conservative allocation
            content_ratio = 0.6  # 60% for content
            response_ratio = 0.4  # 40% for response
            file_ratio = 0.3  # 30% of content for files
            history_ratio = 0.5  # 50% of content for history
        else:
            # Larger context models (Gemini): More generous allocation
            content_ratio = 0.8  # 80% for content
            response_ratio = 0.2  # 20% for response
            file_ratio = 0.4  # 40% of content for files
            history_ratio = 0.4  # 40% of content for history

        # Calculate allocations
        content_tokens = int(total_tokens * content_ratio)
        response_tokens = reserved_for_response or int(total_tokens * response_ratio)

        # Sub-allocations within content budget
        file_tokens = int(content_tokens * file_ratio)
        history_tokens = int(content_tokens * history_ratio)

        allocation = TokenAllocation(
            total_tokens=total_tokens,
            content_tokens=content_tokens,
            response_tokens=response_tokens,
            file_tokens=file_tokens,
            history_tokens=history_tokens,
        )

        logger.debug(f"Token allocation for {self.model_name}:")
        logger.debug(f"  Total: {allocation.total_tokens:,}")
        logger.debug(f"  Content: {allocation.content_tokens:,} ({content_ratio:.0%})")
        logger.debug(f"  Response: {allocation.response_tokens:,} ({response_ratio:.0%})")
        logger.debug(f"  Files: {allocation.file_tokens:,} ({file_ratio:.0%} of content)")
        logger.debug(f"  History: {allocation.history_tokens:,} ({history_ratio:.0%} of content)")

        return allocation

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text using model-specific tokenizer.

        For now, uses simple estimation. Can be enhanced with model-specific
        tokenizers (tiktoken for OpenAI, etc.) in the future.
        """
        # TODO: Integrate model-specific tokenizers
        # For now, use conservative estimation
        return len(text) // 3  # Conservative estimate

    @classmethod
    def from_arguments(cls, arguments: dict[str, Any]) -> "ModelContext":
        """Create ModelContext from tool arguments."""
        model_name = arguments.get("model") or DEFAULT_MODEL
        return cls(model_name)

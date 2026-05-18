"""MiniMax model provider implementation."""

import logging
import os
from typing import TYPE_CHECKING, ClassVar, Optional

if TYPE_CHECKING:
    from tools.models import ToolModelCategory

from .openai_compatible import OpenAICompatibleProvider
from .registries.minimax import MiniMaxModelRegistry
from .registry_provider_mixin import RegistryBackedProviderMixin
from .shared import ModelCapabilities, ProviderType

logger = logging.getLogger(__name__)


class MiniMaxModelProvider(RegistryBackedProviderMixin, OpenAICompatibleProvider):
    """Integration for MiniMax models exposed over an OpenAI-compatible API."""

    FRIENDLY_NAME = "MiniMax"

    REGISTRY_CLASS = MiniMaxModelRegistry
    MODEL_CAPABILITIES: ClassVar[dict[str, ModelCapabilities]] = {}

    PRIMARY_MODEL = "MiniMax-M2.7"
    FALLBACK_MODEL = "MiniMax-M2.7"

    def __init__(self, api_key: str, **kwargs):
        # Override via MINIMAX_API_BASE_URL (e.g. https://api.minimaxi.com/v1 for China).
        default_base = os.environ.get("MINIMAX_API_BASE_URL", "https://api.minimax.io/v1")
        kwargs.setdefault("base_url", default_base)
        self._ensure_registry()
        super().__init__(api_key, **kwargs)
        self._invalidate_capability_cache()

    def get_provider_type(self) -> ProviderType:
        return ProviderType.MINIMAX

    def get_preferred_model(self, category: "ToolModelCategory", allowed_models: list[str]) -> Optional[str]:
        if not allowed_models:
            return None
        if self.PRIMARY_MODEL in allowed_models:
            return self.PRIMARY_MODEL
        return allowed_models[0]


MiniMaxModelProvider._ensure_registry()

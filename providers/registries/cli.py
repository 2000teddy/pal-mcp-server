"""Registry loader for subscription-CLI model capabilities."""

from __future__ import annotations

from ..shared import ModelCapabilities, ProviderType
from .base import CAPABILITY_FIELD_NAMES, CapabilityModelRegistry


class CLIModelRegistry(CapabilityModelRegistry):
    """Capability registry backed by ``conf/cli_models.json``.

    Besides the standard capability fields, each entry carries a ``cli`` object
    describing how to invoke the backing subscription CLI (executable, parser,
    prompt mode, model flag). The extras are exposed via :meth:`get_entry` so
    :class:`providers.cli_provider.CLIModelProvider` can build the subprocess
    command without re-reading the JSON.
    """

    def __init__(self, config_path: str | None = None) -> None:
        super().__init__(
            env_var_name="CLI_MODELS_CONFIG_PATH",
            default_filename="cli_models.json",
            provider=ProviderType.CLI,
            friendly_prefix="CLI ({model})",
            config_path=config_path,
        )

    def _extra_keys(self) -> set[str]:
        return {"cli"}

    def _finalise_entry(self, entry: dict) -> tuple[ModelCapabilities, dict]:
        cli_config = entry.get("cli")
        if not isinstance(cli_config, dict) or not cli_config.get("executable"):
            raise ValueError(
                f"CLI model '{entry.get('model_name')}' requires a 'cli' object with at least an 'executable'."
            )
        filtered = {k: v for k, v in entry.items() if k in CAPABILITY_FIELD_NAMES}
        filtered.setdefault("provider", self._provider_default())
        capability = ModelCapabilities(**filtered)
        return capability, {"cli": cli_config}

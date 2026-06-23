import os
from unittest.mock import patch

import pytest

import server


@pytest.mark.no_mock_provider
@patch.dict(os.environ, {"PAL_MCP_ALLOW_KEYFREE_STARTUP": "true", "DEFAULT_MODEL": "auto"}, clear=True)
def test_configure_providers_allows_explicit_keyfree_startup():
    """Server startup may be explicitly allowed with zero providers for CLI-only deployments."""
    server.configure_providers()

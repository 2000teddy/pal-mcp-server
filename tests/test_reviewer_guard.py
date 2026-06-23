"""Reviewer guard (house rule): code review must run over a real subscription CLI.

Christian's rule: ``pal:codereview`` MUST use ``claude``, ``codex`` or ``agy`` as the
reviewer — NEVER MiniMax and NEVER ``pal:chat`` as a stand-in. These tests pin that
invariant so the guard cannot silently regress.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from clink.consensus_backends import (
    CLI_BACKEND_NAMES,
    assert_review_backend,
    default_backends,
    is_valid_review_backend,
)
from tools.codereview import CodeReviewTool


def test_cli_backend_names_are_exactly_the_three_subscription_clis():
    assert CLI_BACKEND_NAMES == {"claude", "codex", "agy"}
    # Single source of truth: the allow-list never drifts from default_backends().
    assert CLI_BACKEND_NAMES == {b.name for b in default_backends()}
    # MiniMax / chat must never be a CLI backend.
    assert "minimax" not in CLI_BACKEND_NAMES
    assert "chat" not in CLI_BACKEND_NAMES


def test_is_valid_review_backend():
    for ok in ("claude", "codex", "agy"):
        assert is_valid_review_backend(ok) is True
    for bad in ("minimax", "chat", "gpt-5", None, ""):
        assert is_valid_review_backend(bad) is False


def test_assert_review_backend_accepts_cli_backends():
    for name in ("claude", "codex", "agy"):
        backend = SimpleNamespace(name=name)
        assert assert_review_backend(backend) is backend


def test_assert_review_backend_rejects_non_cli():
    for bad in ("minimax", "chat", "openai"):
        with pytest.raises(ValueError, match="subscription CLI"):
            assert_review_backend(SimpleNamespace(name=bad), requested_model="some-model")


class TestCodeReviewReviewerGuard:
    def test_codereview_resolves_to_cli_backend(self):
        tool = CodeReviewTool()
        # Typical model names route to the expected CLI backends — all valid reviewers.
        assert tool._resolve_expert_backend("opus").name == "claude"
        assert tool._resolve_expert_backend("gpt-5").name == "codex"
        assert tool._resolve_expert_backend("gemini-2.5-pro").name == "agy"

    def test_codereview_rejects_non_cli_reviewer_backend(self, monkeypatch):
        # Defense-in-depth: if backend selection were ever subverted to a non-CLI
        # backend (e.g. MiniMax), codereview must fail-fast, not review silently.
        fake_minimax = Mock()
        fake_minimax.name = "minimax"
        monkeypatch.setattr(
            "clink.consensus_backends.backend_for_model",
            lambda *a, **k: fake_minimax,
        )
        tool = CodeReviewTool()
        with pytest.raises(ValueError, match="not permitted"):
            tool._resolve_expert_backend("minimax-m3")

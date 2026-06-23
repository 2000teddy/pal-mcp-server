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
    # Hard-coded approved set (not derived) so default_backends() can't silently widen it.
    assert CLI_BACKEND_NAMES == {"claude", "codex", "agy"}
    # default_backends() must never introduce a backend outside the approved set.
    assert {b.name for b in default_backends()} <= CLI_BACKEND_NAMES
    # MiniMax / chat must never be a CLI backend.
    assert "minimax" not in CLI_BACKEND_NAMES
    assert "chat" not in CLI_BACKEND_NAMES


def test_is_valid_review_backend():
    for ok in ("claude", "codex", "agy"):
        assert is_valid_review_backend(ok) is True
    for bad in ("minimax", "chat", "gpt-5", None, ""):
        assert is_valid_review_backend(bad) is False


def test_assert_review_backend_accepts_cli_backends():
    # Canonical executables match the backend name (claude/codex/agy).
    for name in ("claude", "codex", "agy"):
        backend = SimpleNamespace(name=name, executable=name)
        assert assert_review_backend(backend) is backend
    # The real default_backends() instances must pass the guard unchanged.
    for backend in default_backends():
        assert assert_review_backend(backend) is backend


def test_assert_review_backend_rejects_non_cli():
    for bad in ("minimax", "chat", "openai"):
        with pytest.raises(ValueError, match="subscription CLI"):
            assert_review_backend(SimpleNamespace(name=bad, executable=bad), requested_model="some-model")


def test_assert_review_backend_rejects_spoofed_executable():
    # An approved name wrapping a non-CLI executable (e.g. MiniMax-backed) must fail-fast.
    spoofed = SimpleNamespace(name="codex", executable="pal")
    with pytest.raises(ValueError, match="unexpected executable"):
        assert_review_backend(spoofed, requested_model="codex")


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

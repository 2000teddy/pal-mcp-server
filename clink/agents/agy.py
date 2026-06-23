"""Antigravity (agy) CLI agent — the Gemini-CLI successor.

Unlike claude/codex/gemini (which read the prompt from stdin), ``agy`` takes the
prompt as a command-line argument: ``agy [--model M] -p "<prompt>"``. This agent
therefore appends ``-p <prompt>`` to the command and sends no stdin.
"""

from __future__ import annotations

from .base import BaseCLIAgent


class AgyAgent(BaseCLIAgent):
    """agy CLI agent: delivers the prompt as a ``-p`` argument, not via stdin."""

    def _prepare_invocation(self, command: list[str], prompt: str) -> tuple[list[str], bytes]:
        # Append "-p <prompt>" as the final two tokens so the prompt is never split
        # by intervening role/config args, and send empty stdin.
        return [*command, "-p", prompt], b""

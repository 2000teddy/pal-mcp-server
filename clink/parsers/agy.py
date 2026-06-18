"""Parser for Antigravity CLI (`agy`) plain-text output.

Unlike the Claude/Codex/Gemini CLIs, `agy -p/--print` has no structured (JSON)
output mode — it prints the model's answer as plain text on stdout. The parser
therefore returns the trimmed stdout as content and preserves stderr (e.g. quota
warnings) in metadata.
"""

from __future__ import annotations

from .base import BaseParser, ParsedCLIResponse, ParserError


class AgyTextParser(BaseParser):
    """Parse plain-text stdout produced by `agy -p`."""

    name = "agy_text"

    def parse(self, stdout: str, stderr: str) -> ParsedCLIResponse:
        content = (stdout or "").strip()
        stderr_text = (stderr or "").strip()

        metadata: dict[str, object] = {}
        if stderr_text:
            metadata["stderr"] = stderr_text
            # Surface throttling so the backend layer can skip a rate-limited slot.
            lowered = stderr_text.lower()
            if "429" in lowered or "rate limit" in lowered or "quota" in lowered or "resource_exhausted" in lowered:
                metadata["rate_limited"] = True

        if content:
            return ParsedCLIResponse(content=content, metadata=metadata)

        if stderr_text:
            raise ParserError(f"agy CLI returned no stdout. stderr: {stderr_text[:200]}")
        raise ParserError("agy CLI returned empty output")

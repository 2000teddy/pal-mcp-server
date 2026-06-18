"""cli_consensus tool — blinded multi-model consensus over subscription CLIs.

Like the built-in ``consensus`` tool, but each "model" is a local CLI authenticated
via an existing subscription (Claude Max / ChatGPT / Google One) instead of a paid
API key — so it incurs no provider API cost. Backends run in parallel (one-shot),
**blinded** (each sees only the question plus its stance, never the others'
answers), and the calling agent synthesises the final recommendation.

See ``docs/architecture/ADR-001-cli-consensus.md``.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import replace
from typing import Any

from mcp.types import TextContent
from pydantic import BaseModel, Field

from clink.consensus_backends import BackendResult, CliBackend, default_backends
from config import TEMPERATURE_ANALYTICAL
from tools.consensus import ConsensusTool
from tools.models import ToolModelCategory, ToolOutput
from tools.simple.base import SimpleTool

logger = logging.getLogger(__name__)

_VALID_STANCES = ("for", "against", "neutral")
_MAX_BACKENDS = 8  # cap concurrent subprocesses; reject runaway/duplicate specs


class CliConsensusRequest(BaseModel):
    """Request model for the cli_consensus tool."""

    prompt: str = Field(..., description="Exact proposal/question every backend sees (blinded).")
    backends: list[dict] | None = Field(
        default=None,
        description="Optional [{backend, stance, model, stance_prompt}]. Default: claude+codex+agy, neutral.",
    )


class CliConsensusTool(SimpleTool):
    """Blinded multi-model consensus over subscription CLIs (claude / codex / agy)."""

    def __init__(self) -> None:
        # Reuse the consensus tool's stance-enhanced system prompts (for/against/neutral).
        self._stance_source = ConsensusTool()
        super().__init__()

    def get_name(self) -> str:
        return "cli_consensus"

    def get_description(self) -> str:
        return (
            "Multi-model consensus over local subscription CLIs (claude/codex/agy) instead of paid "
            "provider APIs — no API cost. Each backend answers the same question blinded, with an "
            "optional stance (for/against/neutral). Returns each verdict; you synthesise the consensus. "
            "Use for architecture choices, design trade-offs, and proposal evaluation."
        )

    def get_annotations(self) -> dict[str, Any]:
        return {"readOnlyHint": True}

    def requires_model(self) -> bool:
        return False

    def get_model_category(self) -> ToolModelCategory:
        return ToolModelCategory.EXTENDED_REASONING

    def get_default_temperature(self) -> float:
        return TEMPERATURE_ANALYTICAL

    def get_system_prompt(self) -> str:
        return ""

    def get_request_model(self):
        return CliConsensusRequest

    def get_tool_fields(self) -> dict[str, dict[str, Any]]:
        return {}

    def get_input_schema(self) -> dict[str, Any]:
        available = sorted(b.name for b in default_backends())
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The exact question/proposal each backend evaluates (blinded). Phrase as 'Evaluate…'.",
                },
                "backends": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "backend": {"type": "string", "enum": available},
                            "stance": {"type": "string", "enum": list(_VALID_STANCES), "default": "neutral"},
                            "model": {"type": "string", "description": "Optional model override for this backend."},
                            "stance_prompt": {"type": "string", "description": "Optional custom stance instruction."},
                        },
                        "required": ["backend"],
                        "additionalProperties": False,
                    },
                    "description": f"Backends to consult (available: {', '.join(available)}). Default: all three, neutral.",
                },
            },
            "required": ["prompt"],
            "additionalProperties": False,
        }

    async def prepare_prompt(self, request) -> str:  # noqa: ARG002
        # Workflow handled in execute(); per-backend prompts are built there.
        return ""

    def _blinded_prompt(self, question: str, stance: str, stance_prompt: str | None) -> str:
        system = self._stance_source.get_stance_enhanced_prompt(stance, stance_prompt)
        return (
            f"{system}\n\n"
            f"=== QUESTION ===\n{question}\n\n"
            "Provide your assessment now. Do not ask for clarification; state assumptions instead."
        )

    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            request = CliConsensusRequest(**arguments)
        except Exception as exc:  # noqa: BLE001 - surface validation errors as tool errors
            return self._error(f"Invalid arguments: {exc}")

        defaults = {b.name: b for b in default_backends()}
        specs = request.backends or [{"backend": name, "stance": "neutral"} for name in defaults]

        if len(specs) > _MAX_BACKENDS:
            return self._error(f"Too many backends ({len(specs)}); maximum is {_MAX_BACKENDS}.")

        jobs: list[tuple[str, CliBackend, str]] = []
        seen: set[tuple[str, str]] = set()
        for spec in specs:
            name = (spec.get("backend") or "").strip()
            if name not in defaults:
                return self._error(f"Unknown backend '{name}'. Available: {', '.join(sorted(defaults))}.")
            stance = (spec.get("stance") or "neutral").lower()
            if stance not in _VALID_STANCES:
                return self._error(f"Invalid stance '{stance}'. Use one of {_VALID_STANCES}.")
            key = (name, stance)
            if key in seen:
                return self._error(f"Duplicate backend+stance combination: {name}/{stance}.")
            seen.add(key)
            backend = defaults[name]
            if spec.get("model"):
                backend = replace(backend, model=spec["model"])
            prompt = self._blinded_prompt(request.prompt, stance, spec.get("stance_prompt"))
            jobs.append((stance, backend, prompt))

        if not jobs:
            return self._error("No backends to consult.")

        # return_exceptions=True is defence-in-depth: run() already never raises.
        raw = await asyncio.gather(*(backend.run(prompt) for _stance, backend, prompt in jobs), return_exceptions=True)
        results: list[BackendResult] = []
        for (_stance, backend, _prompt), r in zip(jobs, raw):
            if isinstance(r, BaseException):
                results.append(BackendResult(backend.name, backend.model, "error", error=f"unexpected: {r}"))
            else:
                results.append(r)

        responses = []
        for (stance, _backend, _prompt), result in zip(jobs, results):
            responses.append(
                {
                    "backend": result.name,
                    "stance": stance,
                    "model": result.model,
                    "status": result.status,
                    "verdict": result.content or None,
                    "error": result.error,
                    "duration_seconds": round(result.duration_seconds, 1),
                }
            )

        successful = sum(1 for r in results if r.ok)
        payload = {
            "status": "consensus_complete",
            "question": request.prompt,
            "backends_consulted": len(jobs),
            "successful": successful,
            "skipped_or_failed": [r["backend"] for r in responses if r["status"] != "success"],
            "responses": responses,
            "next_steps": (
                "CONSENSUS GATHERED. Synthesise now: (1) points of AGREEMENT, (2) points of "
                "DISAGREEMENT and why, (3) your consolidated recommendation, (4) key risks. "
                "Explicitly note any backend that was skipped, errored, or rate-limited."
            ),
            "note": "Ran over subscription CLIs (claude/codex/agy) — no provider API cost.",
        }

        tool_output = ToolOutput(
            status="success" if successful else "error",
            content=json.dumps(payload, indent=2, ensure_ascii=False),
            content_type="text",
            metadata={
                "tool_name": "cli_consensus",
                "backends_consulted": len(jobs),
                "successful": successful,
            },
        )
        return [TextContent(type="text", text=tool_output.model_dump_json())]

    def _error(self, message: str) -> list[TextContent]:
        tool_output = ToolOutput(
            status="error",
            content=message,
            content_type="text",
            metadata={"tool_name": "cli_consensus"},
        )
        return [TextContent(type="text", text=tool_output.model_dump_json())]

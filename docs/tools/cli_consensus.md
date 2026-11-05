# cli_consensus

Blinded multi-model consensus over **local subscription CLIs** — `claude`, `codex`, `agy` — plus
**MiniMax** over its capped/prepaid API. The three CLIs run over your existing subscriptions (Claude Max /
ChatGPT / Google One) at no API cost. MiniMax has no CLI, so it uses the MiniMax provider.
Rationale: [`docs/architecture/ADR-001-cli-consensus.md`](../architecture/ADR-001-cli-consensus.md).

## How it works

- Each backend answers the **same question blinded** — it sees only the question plus its stance,
  never the other backends' answers.
- Backends run **in parallel** (one-shot). The calling agent then **synthesises** the recommendation.
- **Partial-failure safe:** if a backend errors or is rate-limited (e.g. agy quota), its slot is
  skipped and the consensus continues with the rest.
- **No key, no MiniMax:** without `MINIMAX_API_KEY` the `minimax` slot reports `status: "skipped"` and
  appears in `skipped_or_failed`. No other model takes its place.
- **Read-only:** the CLIs are invoked with safe flags (no `--yolo` / `acceptEdits` / `--dangerously-bypass`).
  The model only *answers*; it does not touch the filesystem.

## Backends (default panel)

| backend | invocation | billed through | default model |
|---------|------------|----------------|---------------|
| `claude` | `claude --print --output-format json` (stdin) | Claude Max | `opus` |
| `codex`  | `codex exec --skip-git-repo-check --sandbox read-only --json -m <m>` (stdin) | ChatGPT | `gpt-6.1-sol` |
| `agy`    | `agy --model "<m>" -p "<prompt>"` (arg) | Google One AI Pro | `Gemini 4 Argon (High)` |
| `minimax` | `providers/minimax.py` (no CLI) | MiniMax capped/prepaid API | `MiniMax-M3.1-Flash` |

The default models are configured in one place, `conf/cli_consensus_panel.json`. Point
`CLI_CONSENSUS_PANEL_CONFIG_PATH` at another file to override it. A missing or invalid file is a tool
error, not a silent switch to other models.

> `agy` (Antigravity CLI) replaces the discontinued consumer `gemini` CLI and exposes Gemini, Claude
> and GPT-OSS through Google One. It takes the prompt as an **argument** (not stdin) and emits
> plain text (no JSON mode) — handled by `clink/parsers/agy.py`.

## Parameters

- `prompt` (required) — the exact question/proposal every backend evaluates. Phrase as "Evaluate…".
- `backends` (optional) — list of `{backend, stance, model, stance_prompt}`. Default: all four, neutral.
  - `stance`: `for` | `against` | `neutral` (stance system-prompts reused from the `consensus` tool).
  - `model`: optional per-backend model override.
  - `stance_prompt`: optional custom stance instruction.

## Example

```json
{
  "prompt": "Evaluate: should we adopt approach X for the cache layer?",
  "backends": [
    {"backend": "claude", "stance": "against", "model": "opus"},
    {"backend": "codex",  "stance": "for"},
    {"backend": "agy",    "stance": "neutral"},
    {"backend": "minimax", "stance": "neutral"}
  ]
}
```

## Output

Structured JSON: per backend `{backend, stance, model, status, verdict, error, duration_seconds}`,
plus `successful`, `skipped_or_failed`, and a `next_steps` instruction to synthesise
agreement / disagreement / recommendation / risks. `status` is `success` | `error` | `rate_limited` | `skipped`.

## Cost rule

The three CLI backends use subscriptions and touch no provider API key. MiniMax is the one deliberate API
exception and is part of the default panel when `MINIMAX_API_KEY` is set. No other API provider is used.

## Implementation

- `clink/consensus_backends.py` — `CliBackend` (one short-lived async subprocess per call, safe flags,
  partial-failure, throttle-awareness), `MiniMaxBackend` (same contract over the provider),
  `load_panel_models()` and `default_backends()`.
- `conf/cli_consensus_panel.json` — default model per backend.
- `clink/parsers/agy.py` — plain-text parser for `agy`.
- `tools/cli_consensus.py` — the MCP tool (`CliConsensusTool`).
- Tests: `tests/test_cli_consensus.py`, `tests/test_cli_consensus_backends.py`.

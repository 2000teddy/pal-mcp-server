# cli_consensus

Blinded multi-model consensus over **local subscription CLIs** — `claude`, `codex`, `agy` — instead
of paid provider APIs. No API cost: it runs over your existing subscriptions (Claude Max / ChatGPT /
Google One). Rationale: [`docs/architecture/ADR-001-cli-consensus.md`](../architecture/ADR-001-cli-consensus.md).

## How it works

- Each backend answers the **same question blinded** — it sees only the question plus its stance,
  never the other backends' answers.
- Backends run **in parallel** (one-shot). The calling agent then **synthesises** the recommendation.
- **Partial-failure safe:** if a backend errors or is rate-limited (e.g. agy quota), its slot is
  skipped and the consensus continues with the rest.
- **Read-only:** the CLIs are invoked with safe flags (no `--yolo` / `acceptEdits` / `--dangerously-bypass`).
  The model only *answers*; it does not touch the filesystem.

## Backends (default panel)

| backend | CLI invocation | subscription | default model |
|---------|----------------|--------------|---------------|
| `claude` | `claude --print --output-format json` (stdin) | Claude Max | `sonnet` |
| `codex`  | `codex exec --skip-git-repo-check --sandbox read-only --json` (stdin) | ChatGPT | CLI default |
| `agy`    | `agy --model "<m>" -p "<prompt>"` (arg) | Google One AI Pro | `Gemini 3.1 Pro (Low)` |

> `agy` (Antigravity CLI) replaces the discontinued consumer `gemini` CLI and exposes Gemini, Claude
> and GPT-OSS through Google One. It takes the prompt as an **argument** (not stdin) and emits
> plain text (no JSON mode) — handled by `clink/parsers/agy.py`.

## Parameters

- `prompt` (required) — the exact question/proposal every backend evaluates. Phrase as "Evaluate…".
- `backends` (optional) — list of `{backend, stance, model, stance_prompt}`. Default: all three, neutral.
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
    {"backend": "agy",    "stance": "neutral"}
  ]
}
```

## Output

Structured JSON: per backend `{backend, stance, model, status, verdict, error, duration_seconds}`,
plus `successful`, `skipped_or_failed`, and a `next_steps` instruction to synthesise
agreement / disagreement / recommendation / risks. `status` is `success` | `error` | `rate_limited`.

## Cost rule

The default panel uses subscription CLIs only — no provider API key is touched. Keep the API
provider keys out of `.env` so there is **no silent fallback** to a paid API. MiniMax stays the one
deliberate API exception if you configure it.

## Implementation

- `clink/consensus_backends.py` — `CliBackend` (one short-lived async subprocess per call, safe flags,
  partial-failure, throttle-awareness) + `default_backends()`.
- `clink/parsers/agy.py` — plain-text parser for `agy`.
- `tools/cli_consensus.py` — the MCP tool (`CliConsensusTool`).
- Tests: `tests/test_cli_consensus.py`, `tests/test_cli_consensus_backends.py`.

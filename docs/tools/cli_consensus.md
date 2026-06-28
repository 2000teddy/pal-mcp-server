# cli_consensus

Blinded multi-model consensus over **local subscription CLIs** — `claude`, `codex`, `agy` — instead
of paid provider APIs. No API cost: it runs over your existing subscriptions (Claude Max / ChatGPT /
Google One). Rationale: [`docs/architecture/ADR-001-cli-consensus.md`](../architecture/ADR-001-cli-consensus.md).

> Historical design notes also live in [`docs/cli_consensus_plan.md`](../cli_consensus_plan.md) —
> note it predates the final panel and still mentions other backends (e.g. `minimax-m3`); the shipped
> default panel is **claude / codex / agy** as described here and in ADR-001.

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

## Limits & validation

- **Max 8 backends** per call (concurrent-subprocess cap); more → error.
- `backend` must be one of the default panel (`claude`, `codex`, `agy`); unknown → error.
- `stance` must be `for` | `against` | `neutral`; invalid → error.
- A `(backend, stance)` pair must be **unique** per call; duplicates → error (consult the same
  backend twice only with *different* stances).
- Omitting `backends` **or** passing an empty list → the **default panel** (claude + codex + agy,
  neutral) is used.
- Per-backend timeout **300 s**; on timeout, empty output, a parser failure or a detected rate-limit
  the slot degrades to `error` (or `rate_limited`) and the remaining backends still produce a
  consensus. (A non-zero CLI exit code with usable parsed output may still count as `success`.)

## Output

A single structured JSON payload (in the tool result's `content`):

- **Top level:** `status: "consensus_complete"`, `question`, `backends_consulted`,
  `successful` (count of usable answers), `skipped_or_failed` (backend names), `responses[]`,
  `next_steps`, `note`.
- **Each `responses[]` entry:** `{backend, stance, model, status, verdict, error, duration_seconds}`,
  where the per-backend `status` is `success` | `error` | `rate_limited`.

The tool's overall result status is `success` when at least one backend answered, otherwise `error`.
You then synthesise agreement / disagreement / recommendation / risks from `responses`.

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

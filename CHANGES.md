# CHANGES — PAL MCP Server (ThinkHub-Fork)

> Manuelles **Fork**-Changelog (Keep a Changelog) für ThinkHub-spezifische Änderungen.
> Das automatische **Upstream**-Changelog ist `CHANGELOG.md` (semantic-release) — hier NICHT duplizieren.

## [Unreleased]

### Added
- **`cli_consensus`** tool (Build 2): blinded multi-model consensus over subscription CLIs
  (claude/codex/agy) — no provider API cost. New `clink/consensus_backends.py` (CliBackend layer:
  read-only flags, partial-failure, throttle-awareness, ARG_MAX guard, process-group cleanup),
  `clink/parsers/agy.py` (Antigravity plain-text parser), `tools/cli_consensus.py`,
  `docs/architecture/ADR-001-cli-consensus.md`, `docs/tools/cli_consensus.md`, and 21 unit tests.
  Registered in `server.py` / `tools/__init__.py`. Adds public `ConsensusTool.get_stance_enhanced_prompt()`.
- ThinkHub-Doku-Gerüst (Build 1): `DEVELOPMENT-WORKFLOW.md` (pal-angepasst), `HISTORY.md`,
  `TODO.md`, `CHANGES.md`, `APP_VERSION.md`, `BUILD_NUMBER.md`, `CONTRIBUTING.md`,
  `COMPLIANCE-TABLE.md` (Template), `docs/architecture/` (ADR-Konvention).

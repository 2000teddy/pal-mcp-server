# CHANGES — PAL MCP Server (ThinkHub-Fork)

> Manuelles **Fork**-Changelog (Keep a Changelog) für ThinkHub-spezifische Änderungen.
> Das automatische **Upstream**-Changelog ist `CHANGELOG.md` (semantic-release) — hier NICHT duplizieren.

## [Unreleased]

### Changed
- **`expert_analysis` läuft über Subscription-CLI-Backends statt Provider-API** (ADR-002 Phase A,
  Build 4). `tools/workflow/workflow_mixin.py:_call_expert_analysis` awaitet jetzt
  `clink/consensus_backends.py` (`backend.run`) statt sync `provider.generate_content` — ein
  zentraler Hebel für alle 9 Workflow-Tools (analyze, codereview, debug, thinkdeep, precommit,
  refactor, secaudit, testgen, docgen), 0 API-Kosten. Neues schlankes Modell→Backend-Mapping
  (`select_expert_backend_name`, `backend_for_model`; claude/codex/agy, Default per
  `PAL_EXPERT_CLI_DEFAULT_BACKEND`). Graceful Degradation bei rate_limited/error/empty bleibt
  erhalten; natives CLI-Timeout deckt den bisher fehlenden expert-Timeout. Tests:
  `tests/test_expert_cli_backend.py` (neu), `tests/test_workflow_utf8.py` (auf Backend-Seam umgestellt).
  `chat` + `consensus` folgen in Phase B.

### Added
- **ADR-002** (`docs/architecture/ADR-002-api-cli-migration.md`, Build 3): Entscheidung, den
  gemeinsamen synchronen `expert_analysis`-Pfad der Workflow-Tools auf die async CLI-Backend-Schicht
  (`clink/consensus_backends.py`) zu migrieren — Subscription-CLIs statt kostenpflichtiger Provider-APIs.
  Konsens-gehärtet via `cli_consensus` (3/3, $0 API). Deployment (Docker/Sidecar) als separate
  ThinkHub-Core-Entscheidung ausgeklammert. Code-Änderung folgt erst nach Schritt-1-Verifikation.
- **`cli_consensus`** tool (Build 2): blinded multi-model consensus over subscription CLIs
  (claude/codex/agy) — no provider API cost. New `clink/consensus_backends.py` (CliBackend layer:
  read-only flags, partial-failure, throttle-awareness, ARG_MAX guard, process-group cleanup),
  `clink/parsers/agy.py` (Antigravity plain-text parser), `tools/cli_consensus.py`,
  `docs/architecture/ADR-001-cli-consensus.md`, `docs/tools/cli_consensus.md`, and 21 unit tests.
  Registered in `server.py` / `tools/__init__.py`. Adds public `ConsensusTool.get_stance_enhanced_prompt()`.
- ThinkHub-Doku-Gerüst (Build 1): `DEVELOPMENT-WORKFLOW.md` (pal-angepasst), `HISTORY.md`,
  `TODO.md`, `CHANGES.md`, `APP_VERSION.md`, `BUILD_NUMBER.md`, `CONTRIBUTING.md`,
  `COMPLIANCE-TABLE.md` (Template), `docs/architecture/` (ADR-Konvention).

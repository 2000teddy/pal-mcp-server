# CHANGES — PAL MCP Server (ThinkHub-Fork)

> Manuelles **Fork**-Changelog (Keep a Changelog) für ThinkHub-spezifische Änderungen.
> Das automatische **Upstream**-Changelog ist `CHANGELOG.md` (semantic-release) — hier NICHT duplizieren.

## [Unreleased]

### Changed
- **`chat` + `consensus` laufen über Subscription-CLI-Backends statt Provider-API** (ADR-002 Phase B,
  Build 5). `tools/simple/base.py` (chat/simple-Tools) nutzt den neuen Helfer `_run_cli_backend`
  (faltet System-Prompt, verwirft Bilder, speist via Shim `backend_result_to_model_response()` in die
  bestehende Response-Verarbeitung); `tools/consensus.py:_consult_model` mappt jedes Modell via
  `backend_for_model()` und awaitet `backend.run` (Konsens bleibt geblendet + partial-failure-safe).
  Geteilter Shim/Selektor in `clink/consensus_backends.py` — kein Duplikat. Tests:
  `tests/test_phase_b_cli_backends.py` (neu), bestehende `generate_content`-Mocks auf den Backend-Seam
  umgestellt (`tests/mock_helpers.create_mock_cli_backend`). 5 Provider-Replay-/Routing-Integrationstests,
  die das ersetzte Provider-Routing prüfen, sind mit ADR-002-Begründung `@pytest.mark.skip` markiert.
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

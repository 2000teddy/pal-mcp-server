# CHANGES — PAL MCP Server (ThinkHub-Fork)

> Manuelles **Fork**-Changelog (Keep a Changelog) für ThinkHub-spezifische Änderungen.
> Das automatische **Upstream**-Changelog ist `CHANGELOG.md` (semantic-release) — hier NICHT duplizieren.

## [Unreleased]

### Added
- **`PAL_BACKEND` globaler Backend-Schalter** (ADR-002, #1): alle modellrufenden Tools laufen
  standardmäßig über den neuen `CLIModelProvider` (Abo-CLIs claude/codex/agy); `api` bleibt als
  Notfall-Rückfall. Offene Per-Token-Provider werden im Subscription-Modus nicht registriert
  (MiniMax ausgenommen). Kernstücke: `providers/cli_provider.py`, `providers/registries/cli.py`,
  `clink/cli_invoke.py`, `conf/cli_models.json`, `server.py::_configure_subscription_backend`.
- **Reviewer-Guard** (#2): Code-Review nur über claude/codex/agy erzwungen; optionaler key-freier
  Startup (Subscription-Modus ohne API-Keys).
- **`agy` als vollwertiger clink-Client** (#4, prompt-as-arg) — AgyAgent fürs `clink`-Tool.

### Changed
- **Hermetischer Unit-Gate** (#3): `conftest` unterbindet echte CLI-Subprozesse in Unit-Tests.
- **Lizenz: Apache 2.0 → Elastic License 2.0 (ELv2)** (#10, #11): source-available; NOTICE +
  LICENSE-APACHE-2.0 erhalten die Beehive-Innovations-Ursprungsattribution (Apache-2.0 §4);
  README/SECURITY/Dockerfile-Label/Workflow-Doku auf „source-available" umgestellt.
  Siehe `changes/2026-07-07_elv2-license.md`, `changes/2026-07-07_elv2-security-wording.md`.

### Docs
- **Hub-Deploy-Runbook** (#5) — später in ADR-002 §"Hub-Deploy" eingearbeitet.
- **Abnahme-Regel & DoD** (#6, #7): „fertig" = echter Testbeleg; MCP = Zwei-Peer-Beleg; Testbeleg
  möglichst lebensnah (`DEVELOPMENT-WORKFLOW.md`).
- **CLAUDE.md ThinkHub-Lese-Reihenfolge** (#8) + DEVELOPMENT-WORKFLOW-Pointer.
- **`cli_consensus` Nutzer-Doku** (#9): Limits/Validation, Output-Felder, Plan-Verweis.
- **Warn-Modus MD-Compliance-Gate relandet** (#14): `.github/workflows/md-compliance.yml` nach geschlossenem Stack-PR #13 unverändert sauber auf `main` erneut aufgelegt; lokal verifiziert mit `git diff --check`, YAML-Parse und `bash -n` des Workflow-Skripts.

### Earlier (Build 1–2, vor #1)
- **`cli_consensus`** tool (Build 2): blinded multi-model consensus over subscription CLIs
  (claude/codex/agy) — no provider API cost. New `clink/consensus_backends.py` (CliBackend layer:
  read-only flags, partial-failure, throttle-awareness, ARG_MAX guard, process-group cleanup),
  `clink/parsers/agy.py` (Antigravity plain-text parser), `tools/cli_consensus.py`,
  `docs/architecture/ADR-001-cli-consensus.md`, `docs/tools/cli_consensus.md`, and 21 unit tests.
  Registered in `server.py` / `tools/__init__.py`. Adds public `ConsensusTool.get_stance_enhanced_prompt()`.
- ThinkHub-Doku-Gerüst (Build 1): `DEVELOPMENT-WORKFLOW.md` (pal-angepasst), `HISTORY.md`,
  `TODO.md`, `CHANGES.md`, `APP_VERSION.md`, `BUILD_NUMBER.md`, `CONTRIBUTING.md`,
  `COMPLIANCE-TABLE.md` (Template), `docs/architecture/` (ADR-Konvention).

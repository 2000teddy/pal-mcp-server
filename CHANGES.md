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

### Fixed
- **`mcp` nach oben begrenzt** (#20): `requirements.txt:1` **und** `pyproject.toml:7` → `mcp>=1.0.0,<2`. Ohne Obergrenze
  installierte CI inzwischen mcp **2.3.0**, wo die lowlevel-Dekorator-API entfallen ist →
  `AttributeError` an `server.py:731` beim Modul-Import und **9 Collection-Errors** auf allen drei
  Matrix-Versionen. Der Pin hält die Auflösung in der 1er-Reihe (frische venv: **mcp 1.30.0**,
  `list_tools` vorhanden) und lässt Patch-/Minor-Updates weiter zu. Die Migration auf die
  mcp-2.x-API bleibt eine offene ADR-Frage. Siehe `changes/2026-10-26_mcp-pin-upper-bound.md`.
  Im selben PR nachgezogen: `TODO.md:47` ist abgehakt (der Rebase hatte das Dokument nicht
  angefasst, Watchdog-Befund 26.10.), und die beiden Punkte, die der Pin **nicht** erledigt —
  ungeprüfte Restfläche (`requirements.txt:2-4`, alle acht Zeilen `requirements-dev.txt`) und
  mcp-2.x-Migration — stehen jetzt als eigene offene Backlog-Einträge statt als Nebensatz unter
  einem Häkchen.

### Docs
- **Hub-Deploy-Runbook** (#5) — später in ADR-002 §"Hub-Deploy" eingearbeitet.
- **Abnahme-Regel & DoD** (#6, #7): „fertig" = echter Testbeleg; MCP = Zwei-Peer-Beleg; Testbeleg
  möglichst lebensnah (`DEVELOPMENT-WORKFLOW.md`).
- **CLAUDE.md ThinkHub-Lese-Reihenfolge** (#8) + DEVELOPMENT-WORKFLOW-Pointer.
- **`cli_consensus` Nutzer-Doku** (#9): Limits/Validation, Output-Felder, Plan-Verweis.
- **Warn-Modus MD-Compliance-Gate relandet** (#14): `.github/workflows/md-compliance.yml` nach geschlossenem Stack-PR #13 unverändert sauber auf `main` erneut aufgelegt; lokal verifiziert mit `git diff --check`, YAML-Parse und `bash -n` des Workflow-Skripts.
- **TODO.md-Status-Kopfzeile auf KW44-Stand** (#19): ehrliche Ein-Zeile „Build 2 fertig; CO-01 core-gegated" plus Scope-Abgrenzung (Christian-Gate-Liste liegt in `~/thinkhub-administrator/FREIGABEN-OFFEN-CHRISTIAN.md`, hier nur Bauplan-Punkte). Backlog-Körper unverändert. Präzisierung gegenüber der Watchdog-Vorlage: das MD-Compliance-Gate blockiert seit 21.07., ist aber **nicht** als *required status check* eingetragen (`main` ohne Branch-Protection, 404) — das Follow-up bleibt offen. Siehe `changes/2026-10-26_todo-kw44-status-kopfzeile.md`.

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

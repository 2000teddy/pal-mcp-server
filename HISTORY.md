# HISTORY — PAL MCP Server (ThinkHub-Fork)

> Chronologischer Fließtext-Verlauf der Fork-Arbeit, **neuestes oben**. Kontext für Agenten.
> Upstream-Changelog: `CHANGELOG.md` (auto, semantic-release). Fork-Changelog: `CHANGES.md`.

## 2026-06-17 — cli_consensus gebaut + selbst-reviewt (Build 2)

`cli_consensus` implementiert (ADR-001, „Option 1.5"): neues Tool + `CliBackend`-Schicht
(`clink/consensus_backends.py`), die claude/codex/agy als read-only Subprozesse über die Abos
befragt — geblendet, Stance-Prompts aus `consensus.py` (jetzt public `get_stance_enhanced_prompt`),
Ein-Schuss-parallel, Partial-Failure + Drossel-Awareness. agy (Antigravity, Gemini-CLI-Nachfolger)
nimmt den Prompt als **Argument** (nicht stdin) + liefert Plain-Text → eigener `agy_text`-Parser.
Eigener schlanker async-Runner (nicht der clink-Agent, dessen stdin-Zwang + agentische Flags wie
`--yolo` unpassend sind); clink-**Parser** wiederverwendet.

**Selbst-Review per Dogfooding** (cli_consensus auf eigenen Code, 3/3 Backends, 8–9/10 Confidence)
fand echte HIGH-Bugs: `gather` ohne `return_exceptions` + Parser-Exceptions außer `ParserError`
brachen die „never-raises"-Garantie; agy-ARG_MAX-Crash bei langen Prompts; Post-kill-Hang +
verwaiste Kinder; non-zero Exit ignoriert. **Alle gefixt** (top-level no-raise, broaden except,
ARG_MAX-Guard, `start_new_session`+killpg, bounded reap, dedup + Backend-Cap).

**21 Unit-Tests grün, ruff/black/isort grün, Backend- + Tool-Smoke grün** (3/3, echter Dissens
claude→Click vs. codex/agy→argparse). Dev-Deps (pytest/ruff/black/isort) waren nicht installiert →
in `.pal_venv` nachgezogen. Vorbestehend (NICHT cli_consensus): 45 Gemini-Alias-Test-Fehler
(`flash→flash2.5`), per `git stash` verifiziert, als separater Task geflaggt.

## 2026-06-17 — ThinkHub-Doku-Gerüst eingeführt (Build 1)

pal in das ThinkHub-Doku-Regime integriert, als Vorbereitung für das `cli_consensus`-Vorhaben.
Angelegt: `DEVELOPMENT-WORKFLOW.md` (pal-angepasst — semantic-release/Conventional-Commits/
`code_quality_checks.sh` gewahrt, DB-/Multi-VM-Ballast des Musters weggelassen), `HISTORY.md`,
`TODO.md`, `CHANGES.md` (getrennt vom Upstream-`CHANGELOG.md`), `APP_VERSION.md` (Spiegel von
config.py), `BUILD_NUMBER.md`, `CONTRIBUTING.md`, `COMPLIANCE-TABLE.md` (Template, aktiv ab Phase 2),
`docs/architecture/` für ADRs.

**Nächstes:** ADR-001 (cli_consensus — Multi-Modell-Konsens über Abo-CLIs claude/codex/agy statt
bezahlter Provider-APIs; Architektur „Option 1.5" = Tool + wiederverwendbare CliBackend-Schicht),
dann Implementierung.

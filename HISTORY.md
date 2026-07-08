# HISTORY — PAL MCP Server (ThinkHub-Fork)

> Chronologischer Fließtext-Verlauf der Fork-Arbeit, **neuestes oben**. Kontext für Agenten.
> Upstream-Changelog: `CHANGELOG.md` (auto, semantic-release). Fork-Changelog: `CHANGES.md`.

## 2026-07-07 — MD-Pflege: Altlasten nachgezogen + Rollen/Phasen geklärt

Rückstand aus Christians MD-Pflege-Audit (`~/hermes/reference/2026-07-07_MD-Pflege-Audit-…`)
aufgeholt: CHANGES.md und HISTORY.md waren seit dem 18.06. eingeschlafen (PRs #1–#11 ohne Spur),
COMPLIANCE-TABLE.md verwaist. Diese Erzählung + die Änderungshistorie sind jetzt bis #11 nachgetragen,
die Compliance-Tabelle rückwirkend befüllt. Der **Phasen-Schalter ist gestrichen**: COMPLIANCE-TABLE
ist ab sofort in **jedem** PR Pflicht (nicht mehr „ab Phase 2" — der Trigger, den nie jemand ausrief,
war genau der Grund fürs Einschlafen). Die **Rollen der fünf Doku-Dateien** sind in `CONTRIBUTING.md`
festgeschrieben (changes/ = je PR granular · CHANGES.md = technische Programm-Historie · HISTORY.md =
Agenten-Erzählung, bleibt · COMPLIANCE-TABLE.md = immer Pflicht · TODO.md = Backlog + Fortschritt).
Folge-PR baut das warnende CI-Gate (Ebene 1: `changes/`-Eintrag + COMPLIANCE-Zeile je PR, 2 Wochen
warnend, dann blockierend).

## 2026-06-19…07-07 — Nachtrag: was zwischen Build 2 und der MD-Pflege lief (#1–#11)

Für die Lücke, die das Audit fand, hier die Erzählung in Kürze:

- **ADR-002 — der globale Subscription-Backend-Schalter (#1).** Der in ADR-001 verworfene
  „CLI-*Provider* für alle Tools" wurde bewusst revidiert: `PAL_BACKEND=subscription` ist jetzt der
  Normalbetrieb, alle Tools laufen über einen regulären `CLIModelProvider` hinter dem Standard-Interface
  (kein Tool angefasst/dupliziert), synchron via subprocess (löst das alte Deadlock-Argument), mit
  Alias-Spiegelung, damit kein Modellwunsch unauflösbar ist. `api` bleibt als Notfall. Auf main
  gelandet als „ours-merge" (7887dd7), der Minimacs CLI-Provider-Variante als Zielarchitektur adoptierte.
- **Härtung drumherum:** Reviewer-Guard (#2, Review nur claude/codex/agy) + key-freier Startup;
  hermetischer Unit-Gate (#3, keine echten CLI-Subprozesse im Test); `agy` als vollwertiger
  clink-Client (#4, prompt-as-arg).
- **Doku-Welle:** Hub-Deploy-Runbook (#5, später in ADR-002 gefaltet), Abnahme-Regel/DoD „echter
  Testbeleg = fertig", MCP = Zwei-Peer-Beleg (#6/#7), CLAUDE.md-Lese-Reihenfolge (#8),
  cli_consensus-Nutzer-Doku (#9).
- **ELv2-Relicense (#10/#11):** Apache 2.0 → Elastic License 2.0; Sonderfall ggü. den Geschwister-Repos,
  weil pal Apache-Fremdcode (Beehive Innovations) derivativ nutzt → NOTICE + erhaltene Apache-Kopie.
  Beide PRs haben eigene `changes/`-Einträge.

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

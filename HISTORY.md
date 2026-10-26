# HISTORY — PAL MCP Server (ThinkHub-Fork)

> Chronologischer Fließtext-Verlauf der Fork-Arbeit, **neuestes oben**. Kontext für Agenten.
> Upstream-Changelog: `CHANGELOG.md` (auto, semantic-release). Fork-Changelog: `CHANGES.md`.

## 2026-10-26 — Die Abhängigkeit, die drei Monate lang unbemerkt weggelaufen ist

Der Bookkeeping-PR #19 hat nebenbei etwas aufgedeckt, das wichtiger ist als sein eigener Inhalt:
`requirements.txt:1` stand auf `mcp>=1.0.0` **ohne Obergrenze**. Upstream ist inzwischen bei
**mcp 2.3.0**, und dort sind die lowlevel-Dekoratoren weg — `server.py:731` nutzt
`@server.list_tools()`, also bricht schon der Modul-Import, und 9 Test-Dateien scheitern bei der
Collection, auf allen drei Matrix-Versionen.

**Warum es niemand gemerkt hat, ist die eigentliche Lehre.** Zwei Dinge mussten zusammenkommen:
`test.yml` triggert ausschließlich auf `pull_request`, es gibt also **nie** einen CI-Lauf auf
`main`; und in diesem Repo ist zwischen dem 15.07. und dem 26.10. kein PR geöffnet worden. Drei
Monate ohne einen einzigen CI-Lauf bei gleichzeitig offenen Versionsbereichen heißt: der Zustand
„grün" war schlicht nicht mehr gemessen, nur erinnert. Lokal fiel es auch nicht auf, weil
`.pal_venv` seit Juli auf mcp 1.27.2 steht — ein installiertes venv friert die Auflösung ein und
verdeckt damit genau die Drift, die ein frischer Install sofort zeigt.

Behoben mit dem kleinsten Eingriff, der den Bruch ausschließt: `mcp>=1.0.0,<2` — und zwar in
**beiden** Deklarationen, `requirements.txt:1` *und* `pyproject.toml:7`. Die zweite hatte der erste
Anlauf übersehen; die Review hat sie als High-Befund hereingeholt. Das war wichtiger als es klingt:
`pyproject.toml` ist die Metadaten-Quelle für Wheel und sdist, und `semantic-release.yml` hätte nach
dem `fix(deps)`-Titel genau dieses Artefakt veröffentlicht — ein Release, der einen Fix behauptet,
den er nicht enthält. **Lehre fürs nächste Mal:** bei einem Dependency-Pin immer
`git ls-files | xargs grep -lE 'mcp[>=<~]'` fahren, nicht nur `requirements.txt` ansehen. Eine frische venv
aus `requirements.txt` + `requirements-dev.txt` löst damit auf **mcp 1.30.0** auf — also nicht
zurück auf die alte 1.27.2, sondern auf den aktuellen Stand der 1er-Reihe, in der die Dekoratoren
existieren. Patch- und Minor-Updates bleiben erlaubt, Sicherheitsfixes kommen weiter an.

**Merge-Reihenfolge, nicht beliebig:** `TODO.md:47` — die Checkbox für genau diesen Pin — liegt im
Branch von PR #19, nicht auf `main`. **#19 muss zuerst**, sonst führt `TODO.md` nach dem Merge einen
erledigten Punkt als offen. Umgekehrt bleibt #19 bis dahin CI-rot, weil der Pin erst mit diesem PR
kommt; das ist die beabsichtigte Reihenfolge, kein Widerspruch. Die beiden PRs ergänzen zudem
dieselben Dateien (`COMPLIANCE-TABLE.md`, `HISTORY.md`) — der zweite Merge braucht eine
Konfliktauflösung von Hand.

**Offen geblieben, bewusst:** die Migration auf die mcp-2.x-API (`add_request_handler` /
`get_request_handler` / `middleware` statt der Dekoratoren) ist ein Umbau, keine Umbenennung, und
gehört in ein ADR. Und `mcp` war nur die Zeile, die zuerst gebrochen ist: `requirements.txt:2-4`
und **alle acht** Zeilen in `requirements-dev.txt` haben ebenfalls keine Obergrenze. Die Lehre aus
diesem PR ist deshalb nicht „mcp war schuld", sondern: offene Versionsbereiche plus ein CI, das nur
auf PRs läuft, ergeben eine Zeitbombe mit unbekannter Laufzeit.

## 2026-10-26 — 13 Wochen Stillstand als Stillstand benannt (TODO-Kopfzeile KW44)

Zwischen dem 15.07. und heute ist in diesem Repo **nichts** passiert — `main` stand die ganze Zeit
auf `fd0b91f`, kein offener PR, Working-Tree clean. Das war kein Versehen: die PAL-Lane ist im
Wochenplan bewusst sekundär, und der einzige große Punkt (CO-01 pal-Rebuild) hängt an einem
Core-/Hub-Fenster, das diese Lane nicht öffnen darf. Fertig gebaut ist alles, was PAL-seitig
zu bauen war.

Was dabei kaputt ging, war nur die **Lesbarkeit**: `TODO.md` hatte keine Status-Zeile, also musste
man 48 Zeilen Backlog lesen, um zu erkennen, dass hier nichts wartet außer einer fremden
Entscheidung. Genau das hat der Wochenplan KW44 als „Bookkeeping-Nachholbedarf" eingetragen
(§4 Gate 9, drei TODO-Dateien, 12–13 Wochen alt). Behoben mit einer Kopfzeile, nicht mit einer
Umschreibung: **„Build 2 fertig; CO-01 core-gegated"**, plus der Abgrenzung, dass die vollständige
Christian-Gate-Liste in `~/thinkhub-administrator/FREIGABEN-OFFEN-CHRISTIAN.md` steht und hier nur
bauplan-relevante Punkte geführt werden.

**Dabei aufgefallen (für die Agenten wichtiger als die Kopfzeile selbst):** die Vorlage-Zeile des
Watchdogs sagte „MD-Pflege abgeschlossen (CI-Gate #14)". Live ist das zu optimistisch. Das Gate
liegt auf `main` und blockiert auch wirklich (`WARN_UNTIL=2026-07-21` ist seit Juli abgelaufen),
aber `main` trägt **überhaupt keine Branch-Protection** — `gh api …/branches/main/protection`
antwortet 404. Der Check läuft also, ohne irgendetwas verhindern zu können, und das seit drei
Monaten unbemerkt. Das ist exakt das Repo-Admin-Follow-up, das `TODO.md` seit dem 08.07. als offen
führt; es bleibt offen und steht jetzt auch in der Kopfzeile. Wer „kein Selbst-Merge" für
technisch erzwungen hielt: es ist eine Hausregel (`CONTRIBUTING.md`), keine Wand.

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

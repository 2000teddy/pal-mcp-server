# HISTORY — PAL MCP Server (ThinkHub-Fork)

> Chronologischer Fließtext-Verlauf der Fork-Arbeit, **neuestes oben**. Kontext für Agenten.
> Upstream-Changelog: `CHANGELOG.md` (auto, semantic-release). Fork-Changelog: `CHANGES.md`.

## 2026-10-28 — Der `agy`-Backend war tot, und niemand hat es gemerkt (Modellname)

Seit dem agy-Modellwechsel beim Anbieter war der PAL-CLI-Backend `cli-agy-gemini-pro`
**komplett tot** — mit einer Fehlermeldung, die man als „kaputtes Modell" abtun könnte:
`error: model Gemini 3.1 Pro (Low) is not recognized as a known model or custom model in settings`.
Der Name stand **hartcodiert** an zwei Stellen (`conf/cli_models.json` → `cli_model`,
`clink/consensus_backends.py` → `model=`) plus in einer Test-Assertion. Fix: auf den live
getesteten Namen `Gemini 4 Argon (Low)` umgestellt — 3 Ein-Zeilen-Änderungen, sonst nichts.

Der interessante Teil ist nicht der Fix, sondern **wie er gefunden wurde**. Der übliche
Health-Check wäre grün gewesen: `mcporter list` meldet alle 9 Server als „healthy", PAL
mit 19 Tools. Nur ein **echter Aufruf** deckt den Totalausfall auf. Dasselbe Muster hat
Christian am selben Tag in den anderen beiden CLI-Backends erwischt — `cli-claude-sonnet`
und `cli-claude-opus` scheitern mit „OAuth session expired", `cli-codex-gpt` mit 401, und
**beide** maskieren den Fehler als `continuation_available`. Zusammen mit dem am selben
Tag abgelaufenen Claude-OAuth (10:34 UTC) und dem nicht angemeldeten `codex` bleibt als
einziger **funktionierender** PAL-Backend `agy` übrig — genau der, der den Fix gebaut hat.
**Merksatz: ein Health-Signal, das den Fehlerpfad nicht abbildet, ist kein Health-Signal.**

Der Fix sitzt bewusst auf einem **eigenen Branch direkt auf `origin/main`** (`5d41a7c`),
nicht auf dem PR-#20-Branch: der ursprüngliche Fix-Commit hatte dessen 12 Commits
geerbt, und ein PR von dort hätte PR #20 dupliziert. Der 3-Zeilen-Diff wurde gegen die
Originalfassung byte-identisch verifiziert.

Zur Testlage: die Gesamtsuite meldet `5 failed, 966 passed` — **das ist nicht dieser
Fix**, sondern das bereits in PR #19 belegte `.env`-Artefakt. Gegenprobe auf unverändertem
`origin/main` mit identischer Dateikombination ergibt dieselben 5 Failures; im Einzelruf
sind die Tests grün (Reihenfolge-/Pollution-Effekt der Suite). Der relevante Beleg ist der
Zieldatei-Lauf (`tests/test_cli_provider.py` → 47/47 grün) plus die Live-Probe:
`mcporter call pal chat model="cli-agy-gemini-pro"` liefert wieder content (`CLEAN_BASE_OK`),
vorher lieferte derselbe Aufruf `error`.

**Nicht getan:** kein Merge. Ein Push auf `main` löst `semantic-release` aus
(9.9.0 → 9.9.1, `ghcr.io`-Image, Repo `PUBLIC`) — das ist ein Christian-Gate, keine
Lautionsentscheidung.
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

**Offen geblieben, bewusst:** die Migration auf die mcp-2.x-API ist ein Umbau, keine Umbenennung,
und gehört in ein ADR. (Nachtrag, am Paket geprüft: in 2.3.0 gehen die Handler als
`on_list_tools=` / `on_call_tool=` / `on_list_prompts=` / `on_get_prompt=` in den `Server`-
Konstruktor, eigene Methoden über `add_request_handler`; `middleware` ist **nicht** der
Dekorator-Ersatz, sondern eine eigene Schicht. Die erste Fassung dieses Absatzes hat das
zusammengeworfen.) Und `mcp` war nur die Zeile, die zuerst gebrochen ist: `requirements.txt:2-6`,
die vier Spiegelzeilen `pyproject.toml:8-11` und **alle acht** Zeilen in `requirements-dev.txt` haben
ebenfalls keine Obergrenze. Die Lehre aus
diesem PR ist deshalb nicht „mcp war schuld", sondern: offene Versionsbereiche plus ein CI, das nur
auf PRs läuft, ergeben eine Zeitbombe mit unbekannter Laufzeit.

**Nachtrag am selben Tag — die Checkbox, die der Rebase vergessen hat.** Der Watchdog-Sweep
(15:05 UTC in der Lane eingegangen) hat gemeldet, dass `git diff origin/main..origin/fix/mcp-pin-upper-bound -- TODO.md`
**leer** ist: der Pin war gesetzt, aber `TODO.md:47` führte ihn im Branch weiter als offene
🔴-Sofortmaßnahme. Nachgeprüft, trifft zu. Die Ursache ist lehrreicher als der Fehler: die Anweisung
„`TODO.md:47` bleibt offen" war **richtig**, solange die Zeile zu #19 gehörte und #20 noch rot war —
und ist mit dem Merge von #19 um 07:39 UTC ungültig geworden, ohne dass jemand sie neu bewertet hat.
Ein Reconcile-Punkt, der an einer Merge-Reihenfolge hängt, ist nach dem ersten Merge **erneut**
fällig; genau diesen zweiten Blick hat der Rebase nicht gemacht.

Abgehakt wurde nicht einfach das Kästchen. Der Punkt enthielt zwei Dinge, die der Pin **nicht**
erledigt — die ungeprüfte Restfläche (`requirements.txt:2-6`, `pyproject.toml:8-11` und alle acht
Zeilen in `requirements-dev.txt`) und die mcp-2.x-Migration. Als Nebensatz unter einem `[x]` wären
beide verschwunden. Sie stehen deshalb jetzt zusätzlich als eigene offene Einträge unter
„🟡 Offen" — kopiert, nicht verschoben, damit der Original-Text wörtlich erhalten bleibt. Dass
die Restfläche dabei erst **falsch gezählt** war (`2-4`, ohne `python-dotenv`,
`importlib-resources` und die ganze `pyproject.toml`-Seite), hat die Review gefunden: ein
kopierter Fehler wird durch das Kopieren nicht richtiger, er bekommt nur eine zweite Stelle.

**Und noch ein Nachtrag, der die eigentliche Lehre endlich an die richtige Stelle bringt.** Dass
`test.yml` nur auf `pull_request` läuft, stand bis heute **nur in diesem Fließtext** — als
Erkenntnis also, nicht als Aufgabe. Dasselbe beim Repo-Admin-Follow-up zum MD-Gate: es hing als
Unterzeile unter einem abgehakten `[x]`, wo es in einer Checkliste niemand sieht. Beides steht
jetzt als benannter offener Punkt im Backlog (CI-Gate-1: `main` ohne Branch-Protection, deshalb
ist kein Check *required*; CI-Gate-2: kein `push`-/`schedule`-Trigger, deshalb entsteht ohne PR
gar kein Check). Es sind **zwei** Lücken, nicht eine, und das ist der Punkt: eine
Branch-Protection hätte die `mcp`-Drift nicht gefunden, weil ohne PR nichts läuft — und ein
nächtlicher Testlauf hätte sie gezeigt, aber niemanden am Merge gehindert. Die eine macht rote
Checks verbindlich, die andere lässt überhaupt erst welche entstehen. Und der zweite Fix hat eine
Pointe, die man kennen muss, bevor man ihn für erledigt hält: GitHub schaltet geplante Workflows
in öffentlichen Repos nach 60 Tagen Repo-Stille **automatisch ab** — der nächtliche Lauf, der
diese Drift gefunden hätte, wäre in genau diesem Repo nach zwei Monaten Stille selbst verstummt,
lautlos. Ein Wächter, der einschläft, wenn nichts passiert, bewacht die Lage nicht, in der er
gebraucht wird. Beide Punkte sind Repo-Admin auf einem öffentlichen Repo und damit Christians
Entscheidung — das Lane-Token hätte `admin=true`,
was die Sache technisch möglich und trotzdem nicht erlaubt macht. **Die allgemeinere Lehre:** eine
Lehre, die nur in `HISTORY.md` steht, ist Prosa; erst der Backlog-Eintrag macht sie zur Arbeit. **Die Lehre für
Reconcile-Arbeit:** ein Häkchen gilt für genau das, was belegt ist; alles andere, was im selben
Absatz mitgeschleppt wurde, muss vorher heraus.

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

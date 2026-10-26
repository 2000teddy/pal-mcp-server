# 2026-10-26 — TODO-Reconcile: ehrliche Status-Kopfzeile (KW44-Stand)

Reiner Doku-/Bookkeeping-Nachtrag (Ebene-2-Reconcile), angefordert vom Workday-Watchdog
(`~/hermes/reports/AUFTRAG-PALDEV-TODO-KONSOLIDIERUNG-20261026.md`, Wochenplan KW44 §4 Gate 9).
`TODO.md` hatte mtime **2026-07-15** — 13 Wochen ohne Stand-Zeile. Wer die Datei aufschlug,
musste 48 Zeilen Backlog lesen, um zu sehen, dass die Lane technisch fertig und nur noch
fremd-gegatet ist.

## Was
- **TODO.md, Kopfblock:** Status-Block vor der bestehenden `**Rolle:**`-Zeile ergänzt (12 Zeilen added,
  0 removed). Inhalt:
  - **Status-Kurzzeile** wortwörtlich aus dem Wochenplan KW44 (§4 Gate 9, Tabellenzeile
    `pal-mcp-server/TODO.md`): „Build 2 fertig; CO-01 core-gegated".
  - **Scope-Abgrenzung:** dieses File ist das Bauplan-Backlog der PALDEV-Lane, **nicht** die
    Freigaben-Liste; die vollständige Christian-Gate-Liste steht in
    `~/thinkhub-administrator/FREIGABEN-OFFEN-CHRISTIAN.md`.
  - **Klartext-Zeilen:** Build 2 (`cli_consensus` + `PAL_BACKEND`, #1–#9) gebaut/getestet/gemergt;
    MD-Pflege bis auf ein Repo-Admin-Follow-up erledigt; Hauptpunkt CO-01 ist Fremd-Lane.
- **Kein** Umsortieren, **kein** Löschen, **kein** Archivieren. Backlog-Körper unverändert:
  die `.env`-Backups (Christians Wort) und das optionale `AGY.md` bleiben stehen wie sie waren.

## Warum jetzt
Die einzige „was kommt / was ist erledigt"-Quelle des Repos las sich wie ein offener Bauplan,
obwohl der Bauteil seit Mitte Juli fertig ist und der Rest an einem Core-Fenster hängt. Das ist
genau der Effekt, den der Wochenplan als „Bookkeeping-Nachholbedarf" benennt: fertige Arbeit
sieht alt aus, weil die Status-Zeile fehlt.

## Belegte Abweichung von der Vorlage-Zeile
Die Watchdog-Tabelle fasst die Lage als „MD-Pflege abgeschlossen (CI-Gate #14)" zusammen. Live
geprüft am 26.10. ist das **eine Stufe zu optimistisch** und wurde darum in der Kopfzeile präzisiert:
- `gh api repos/2000teddy/pal-mcp-server/branches/main/protection` → **HTTP 404, „Branch not protected"**.
- Das Gate selbst ist da und blockiert (`.github/workflows/md-compliance.yml:25`,
  `WARN_UNTIL="2026-07-21"` → seit dem 21.07. `::error::` statt `::warning::`), aber es ist
  **nicht** als *required status check* eingetragen — genau das Follow-up, das `TODO.md`
  (Abschnitt „🟠 In Arbeit") seit dem 08.07. als offen führt. Der Backlog-Punkt bleibt also zu Recht
  offen; die Kurzzeile „Build 2 fertig" wurde entsprechend nicht zu „alles fertig" ausgeweitet.

Die Kurzzeile selbst ist faktisch korrekt: Build 2 ist in `CHANGES.md` („Earlier (Build 1–2, vor #1)"
+ `[Unreleased]/Added`) und in `TODO.md` §„✅ cli_consensus + Subscription-Backend" vollständig
abgehakt; CO-01 steht unverändert unter „⏸️ Blockiert (extern)".

## Validierung
Reine MD-Änderung, **kein** Python/Dockerfile/CI-Delta → kein Test-/Build-Delta
(`./code_quality_checks.sh` nicht betroffen, wie bei #16–#18). Lokal: `git diff --check` sauber.
`BUILD_NUMBER.md` **nicht** gebumpt — Hauspraxis: Bookkeeping-PRs (#15–#18) bumpen nicht, nur
echte Arbeitsschritte. Gebumpt haben bisher genau zwei Commits: `1e2838d` (`cli_consensus`, Build 2)
und `291e3f9` (PR #12, MD-Pflege).
`/opt/thinkhub` nicht angefasst, CO-01 nicht berührt, kein Christian-Gate angefasst.

## CI-Stand (vorbestehend rot, nicht aus diesem PR)

Dieser PR fasst ausschließlich `*.md` an (`git diff main...HEAD --name-only` → 5 MD-Dateien,
0 Python/CI). Trotzdem sind die `test`-Jobs rot — das ist **Fäule, die dieser PR nur aufdeckt**,
weil seit dem 15.07. kein CI-Lauf mehr stattgefunden hat. Der letzte grüne `Tests`-Run lief am
2026-07-15 11:09 auf dem PR-Branch `docs/adr-003-host-cli-runner-20260715` — **nicht** auf dem
Merge-Commit `fd0b91f` selbst, denn `test.yml:3-5` triggert ausschließlich auf `pull_request`, auf
`main` läuft **nie** ein `test`-Job. Inhaltlich deckungsgleich: `git diff --stat f21b9d3 fd0b91f`
ist leer, identischer Tree. „main ist auch rot" ist damit ein gültiger **lokaler** Kontrollbefund,
kein CI-Beleg — einen CI-Beleg dafür kann es bauartbedingt nicht geben.

- **Symptom:** 9 Collection-Errors auf 3.10/3.11/3.12, jeweils
  `AttributeError: 'Server' object has no attribute 'list_tools'` an `server.py:731`.
- **Ursache:** `requirements.txt:1` pinnt `mcp>=1.0.0` **ohne Obergrenze**. CI installiert
  inzwischen **mcp 2.3.0**; die Dekorator-API `Server.list_tools()` existiert dort nicht mehr.
  Lokal läuft `.pal_venv` noch auf **mcp 1.27.2**, dort ist `hasattr(Server, 'list_tools') == True`
  — darum fällt es beim lokalen Arbeiten nicht auf.
- **Grün geblieben:** `lint`, `md-compliance`, `Validate PR`.
- **Lokale Testlage — vier Läufe, der Scope entscheidet** (26.10., mcp 1.27.2 außer Lauf 1):
  1. CI-Scope `-m "not integration"`, mcp **2.3.0**, kein `.env` → **9 Collection-Errors** (rot).
  2. CI-Scope, `.env` **vorhanden** → `966 passed, 5 failed, 4 skipped, 16 deselected`.
  3. **Volle** Suite ohne `-m`-Filter, `.env` vorhanden → `971 passed, 15 failed, 5 skipped`.
  4. `fd0b91f` via `git archive`, CI-Scope, **ohne** `.env` → **`971 passed, 0 failed`**, 4 skipped.

  Lauf 2 und 3 widersprechen sich nicht: `966+5+4+16 = 991 = 971+15+5`. Die 16 deselektierten
  Integrationstests liefern in Lauf 3 genau `5 passed + 10 failed + 1 skipped`. Maßgeblich ist
  Lauf 2/4, weil `-m "not integration"` der CI-Scope ist (`.github/workflows/test.yml:32`).

  **Die 15 Failures aus Lauf 3 sind kein Code-Defekt**, sondern zwei Gruppen:
  - **5 = `.env`-Artefakt.** Lauf 4 ist der Kontrollversuch: derselbe Commit, dieselbe mcp-Version,
    nur ohne `.env` → 0 Failures. Betroffen: `test_gemini_restriction_policy_alias_allows_canonical`,
    `test_service_alias_allows_canonical_gemini`, `test_tool_schema_in_normal_mode`,
    `test_model_field_schema_generation`, `test_image_validation_model_specific_limits`. Die
    geladenen Keys ändern die erlaubten Modell-Aliasse und damit die erwarteten Schemata.
  - **10 = `integration`-markiert**, brauchen `CUSTOM_API_URL`/Ollama (`CLAUDE.md`): 9 ×
    `test_prompt_regression.py` + 1 × `test_clink_integration.py::test_clink_claude_single_digit_sum`.
    CI deselektiert sie, sie gehen ins CI-Verdikt nicht ein.

  **Konsequenz, mit der Grenze des Belegs:** Lauf 4 entspricht der CI-Konfiguration (kein `.env`,
  mcp 1.x) und ist dort **lokal reproduziert grün** — allerdings nur auf **Python 3.12.3**, während
  CI die Matrix 3.10/3.11/3.12 fährt, und `requirements.txt:2-4` sowie **alle** Zeilen in
  `requirements-dev.txt` sind ebenfalls ohne Obergrenze, können also mitgedriftet sein. Ein
  `mcp<2`-Pin ist damit die belegte nächste Maßnahme, **kein garantiert grüner CI-Lauf**; das zeigt
  erst der Folge-PR. Frühere Formulierung in diesem Eintrag („die 5 sind die bekannten
  Gemini-Alias-Fehler aus `HISTORY.md`") war im Mechanismus falsch: die Testnamen überlappen, aber
  es sind Umgebungsartefakte, keine latenten Code-Fehler. Korrigiert nach Watchdog-Nachmessung,
  unabhängig nachgestellt.
- **Prä-Existenz gemessen (26.10.):** `git archive fd0b91f` in ein Scratchpad-Verzeichnis (kein
  Repo-State angefasst), frisches venv mit `mcp==2.3.0` + `requirements.txt`, dann
  `pytest tests/ -q -m "not integration"` → **dieselben 9 Collection-Errors**
  (`9 errors in 2.35s`), ohne eine Zeile aus diesem PR. Zusätzlich im isolierten venv:
  `mcp 2.3.0` → `hasattr(Server('probe'), 'list_tools') == False`; die Instanz bietet statt der
  Dekoratoren jetzt `add_request_handler` / `get_request_handler` / `middleware`. Es ist also ein
  API-Wechsel, kein Umbenennen — `mcp<2` stellt die CI-Aussagekraft her, erledigt aber die
  2.x-Migration nicht (`server.py` nutzt die lowlevel-Dekoratoren an mehreren Stellen).
  Der Workday-Watchdog hat denselben Kontroll-Lauf unabhängig mit demselben Ergebnis gefahren.
- **Nicht hier behoben:** ein `mcp<2`-Pin (oder die Migration auf die 2.x-API) ist eine
  Code-Änderung und gehört in einen eigenen PR. Dieser PR ist Bookkeeping; ihn mit einem
  Dependency-Pin zu mischen würde beides schlechter reviewbar machen.

## Review

`pal clink` · `cli_name=claude` · `role=codereviewer` → **`claude-sonnet-5-5`** (das Preset pinnt
`--model sonnet`), 2026-10-26 07:40 CET. **Votum: APPROVE**, Nachbesserungen nicht blockierend.
Der ursprünglich angewiesene Reviewer `codex` ist nicht einholbar (`~/.codex/auth.json` vom 08.07.,
`auth_mode: chatgpt`, Token nicht refreshbar → 401 auf allen Codex-Pfaden); die Hausregel erlaubt
`claude`/`codex`/`agy`, `pal:chat` bleibt gesperrt. Alle vier Reviewer-Befunde wurden nachgemessen
und halten — sie sind in diesem Eintrag und in `TODO.md` eingearbeitet (Kopfblock-Zählung,
`mcp<2` als Backlog-Punkt, „lokal grün ≠ CI grün", Merge-Commit-vs-Branch-Head-Präzisierung).
Reviewer-Wortlaut zum roten Job: „kein Grund gegen den Merge-Inhalt, sondern ein repo-weites
Vorproblem." Kommentar: PR #19, `issuecomment-6409932957`.

## Status
Kein Selbst-Merge (`CONTRIBUTING.md` §Branch-Strategie). Auf Feature-Branch
`docs/todo-kw44-status-kopfzeile-20261026`, wartet auf Review-Freigabe über claude/codex/agy
(nie MiniMax/pal:chat).

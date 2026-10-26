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
`BUILD_NUMBER.md` **nicht** gebumpt — Hauspraxis: Bookkeeping-PRs (#15–#18) bumpen nicht,
nur echte Arbeitsschritte (#12, `cli_consensus`).
`/opt/thinkhub` nicht angefasst, CO-01 nicht berührt, kein Christian-Gate angefasst.

## CI-Stand (vorbestehend rot, nicht aus diesem PR)

Dieser PR fasst ausschließlich `*.md` an (`git diff main...HEAD --name-only` → 5 MD-Dateien,
0 Python/CI). Trotzdem sind die `test`-Jobs rot — das ist **Fäule, die dieser PR nur aufdeckt**,
weil seit dem 15.07. kein CI-Lauf mehr stattgefunden hat (letzter grüner `Tests`-Run:
`docs/adr-003-host-cli-runner-20260715`, 2026-07-15 11:09).

- **Symptom:** 9 Collection-Errors auf 3.10/3.11/3.12, jeweils
  `AttributeError: 'Server' object has no attribute 'list_tools'` an `server.py:731`.
- **Ursache:** `requirements.txt:1` pinnt `mcp>=1.0.0` **ohne Obergrenze**. CI installiert
  inzwischen **mcp 2.3.0**; die Dekorator-API `Server.list_tools()` existiert dort nicht mehr.
  Lokal läuft `.pal_venv` noch auf **mcp 1.27.2**, dort ist `hasattr(Server, 'list_tools') == True`
  — darum fällt es beim lokalen Arbeiten nicht auf.
- **Grün geblieben:** `lint`, `md-compliance`, `Validate PR`.
- **Lokal am Branch-HEAD** (mcp 1.27.2): `966 passed, 5 failed, 4 skipped`. Die 5 Fehler sind die
  bekannten Gemini-Alias-Fehler (`test_alias_target_restrictions`, `test_auto_mode`,
  `test_image_support_integration`) — in `HISTORY.md` (2026-06-18) als vorbestehend und
  cli_consensus-fremd geflaggt, nicht aus diesem PR.
- **Nicht hier behoben:** ein `mcp<2`-Pin (oder die Migration auf die 2.x-API) ist eine
  Code-Änderung und gehört in einen eigenen PR. Dieser PR ist Bookkeeping; ihn mit einem
  Dependency-Pin zu mischen würde beides schlechter reviewbar machen.

## Status
Kein Selbst-Merge (`CONTRIBUTING.md` §Branch-Strategie). Auf Feature-Branch
`docs/todo-kw44-status-kopfzeile-20261026`, wartet auf Review-Freigabe über claude/codex/agy
(nie MiniMax/pal:chat).

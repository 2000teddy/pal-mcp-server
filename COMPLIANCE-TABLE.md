# COMPLIANCE-TABLE — PAL MCP Server

> **Immer Pflicht — je PR eine Zeile.** Der frühere „ab Phase 2"-Schalter ist ersatzlos gestrichen
> (Christians Beschluss 2026-07-07): ein Trigger, den nie jemand ausrief, war der Grund, dass die
> Tabelle einschlief. Ab sofort führt **jeder** PR hier eine Zeile; das warnende CI-Gate (Ebene 1)
> und der Reconcile-Wächter (Ebene 2) machen Lücken sichtbar.

**Legende:** `ok` eingehalten · `--` nicht anwendbar · `!!` nicht eingehalten (blockiert Merge) · `~~` nachgeholt

**Spalten:** CO Konsens · DOC ADR/Doku · TS Tests · CR Code-Review · PP Pre-Push · DO Doku-Update

| # | PR | Beschreibung | Datum | CO | DOC | TS | CR | PP | DO | Findings |
|---|----|--------------|-------|----|-----|----|----|----|----|----------|
| 1 | #1 | PAL_BACKEND / CLIModelProvider (ADR-002) | 2026-06-19 | ok | ok | ok | ok | ok | ~~ | Doku hier nachgetragen (MD-Pflege) |
| 2 | #2 | Reviewer-Guard + key-freier Startup | 2026-06-23 | -- | ok | ok | ok | ok | ~~ | " |
| 3 | #3 | Hermetischer Unit-Gate (conftest) | 2026-06-23 | -- | ok | ok | ok | ok | ~~ | " |
| 4 | #4 | agy als vollwertiger clink-Client | 2026-06-23 | -- | ok | ok | ok | ok | ~~ | " |
| 5 | #5 | Hub-Deploy-Runbook (→ ADR-002) | 2026-06-24 | -- | ok | -- | ok | ok | ~~ | Doc-only |
| 6 | #6 | Abnahme-Regel „echter Testbeleg" | 2026-06-26 | -- | ok | -- | ok | ok | ~~ | Doc-only |
| 7 | #7 | DoD-Zusatz Testbeleg lebensnah | 2026-06-26 | -- | ok | -- | ok | ok | ~~ | Doc-only |
| 8 | #8 | CLAUDE.md ThinkHub-Lese-Reihenfolge | 2026-06-26 | -- | ok | -- | ok | ok | ~~ | Doc-only |
| 9 | #9 | cli_consensus Nutzer-Doku-Politur | 2026-06-28 | -- | ok | -- | ok | ok | ~~ | Doc-only |
| 10 | #10 | ELv2-Relicense | 2026-07-07 | -- | ok | ok | ok | ok | ok | changes/ vorhanden; NOTICE-Sonderfall |
| 11 | #11 | ELv2-Wording source-available | 2026-07-07 | -- | ok | -- | ok | ok | ok | changes/ vorhanden |
| 12 | #12 | MD-Pflege: Altlasten + Rollen + Phasen-Schalter streichen | 2026-07-07 | -- | ok | ok | ok | ok | ok | changes/ vorhanden |
| 14 | #14 | Ebene 1: warnendes MD-Compliance CI-Gate (Reland auf main) | 2026-07-08 | -- | ok | -- | ok | ok | ok | changes/ vorhanden; CI-only, Inhalt von #13 sauber auf main erneut gelandet |
| 15 | #15 | MD-Nachtrag: PR #14 in CHANGES/COMPLIANCE dokumentiert | 2026-07-09 | -- | ok | -- | ok | ok | ok | changes/ vorhanden; reiner MD-Nachtrag zu #14 |
| 16 | #16 | TODO-Reconcile: Ebene-1-CI-Gate als gelandet abgehakt | 2026-07-10 | -- | ok | -- | ok | ok | ok | changes/ vorhanden; reiner TODO-Reconcile (Ebene 2) |
| 17 | #17 | TODO-Reconcile: CO-01-Blocker auf Realität umgeschrieben (TL-07 erbracht → Core-Fenster + ADR-003) | 2026-07-15 | -- | ok | -- | ok | ok | ok | changes/ vorhanden; reiner Doku-Reword, Zeiger auf Bridge-Runner-Report |
| 18 | #18 | ADR-003 PAL-Repo-Referenzspiegel + CO-01-Rebuild-Konformitäts-Checkliste | 2026-07-15 | -- | ok | -- | ok | ok | ok | changes/ vorhanden; Referenz auf Core-Vertrag, /opt read-only, kein Rebuild |
| 19 | #19 | TODO-Reconcile: ehrliche Status-Kopfzeile KW44 („Build 2 fertig; CO-01 core-gegated") | 2026-10-26 | -- | ok | -- | ok | ok | ok | changes/ vorhanden; Backlog-Körper unverändert (+12/−0). Review: `pal clink` claude/codereviewer (`claude-sonnet-5-5`) → APPROVE. Zwei Nebenbefunde im changes/-Eintrag belegt: `main` ohne Branch-Protection (404) und CI-`test` rot durch ungepinntes `mcp` (→ Backlog-Punkt unter „🟡 Offen") |
| 20 | #20 | `mcp` nach oben begrenzen (`mcp>=1.0.0,<2`) — behebt 9 CI-Collection-Errors | 2026-10-26 | -- | ok | ok | ok | ok | ok | changes/ vorhanden; Zwei-Zeiler (`requirements.txt:1` + `pyproject.toml:7`) + CI-Nachweis. Review `claude-sonnet-5-5`: erst CHANGES-NEEDED (High: `pyproject.toml` übersehen), Befund nachgeprüft und behoben. Frische venv aus requirements.txt+dev → **mcp 1.30.0**, `list_tools` vorhanden, **keine Collection-Errors**. 2.x-Migration und die übrigen ungepinnten Zeilen bleiben offen. `BUILD_NUMBER` 3 → 4 (`fix`-PR = ein Arbeitsschritt, `CONTRIBUTING.md:44`); der Doku-Nachtrag bumpt **nicht** weiter, er korrigiert denselben Schritt. Nachtrag 26.10. (Commits 15:07/15:13 UTC + Korrekturrunde): Watchdog-Befund bestätigt — der Rebase hatte `TODO.md` nicht angefasst (`git diff origin/main..origin/fix/mcp-pin-upper-bound -- TODO.md` leer); Checkbox `TODO.md:47` abgehakt, Restfläche und mcp-2.x-Migration zusätzlich als eigene offene Punkte geführt, Platzhalter `(dieser PR)` in Zeile 19/20 auf `#19`/`#20` gesetzt. Zwei weitere Review-Runden (`claude-sonnet-5-5`, `pal clink` `role=codereviewer`): Runde 2 → CHANGES-NEEDED, sechs Doku-Befunde, alle nachgeprüft, alle zutreffend, alle behoben (unvollständige Restfläche; `middleware` als 2.x-Dekorator-Ersatz falsch — am Paket `mcp==2.3.0` nachgesehen; BUILD-Doppelzählung; Kopfzeilen-Zählung; Formulierung „herausgelöst"; Platzhalter-Uhrzeiten). Runde 3 → CHANGES-NEEDED, drei Befunde, ebenfalls alle zutreffend und behoben (`pyproject.toml:8-12` → `8-11`, vier statt fünf Spiegelzeilen; Uhrzeiten lagen in der Zukunft; Befund-Zählung). Runde 4 (Gegenprüfung) → **APPROVE**, keine neuen Fehler. Ein Layout-Hinweis (abgehakter Punkt nach „✅" verschieben) bewusst nicht übernommen, Begründung im changes/-Eintrag. Nicht reviewer-bestätigt (ohne Paket-Download nicht prüfbar, von dieser Lane belegt): die mcp-2.3.0-API-Details |

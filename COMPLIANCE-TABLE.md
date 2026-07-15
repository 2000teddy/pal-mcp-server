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
| 18 | (dieser PR) | ADR-003 PAL-Repo-Referenzspiegel + CO-01-Rebuild-Konformitäts-Checkliste | 2026-07-15 | -- | ok | -- | ok | ok | ok | changes/ vorhanden; Referenz auf Core-Vertrag, /opt read-only, kein Rebuild |

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
| 12 | (dieser PR) | MD-Pflege: Altlasten + Rollen + Phasen-Schalter streichen | 2026-07-07 | -- | ok | ok | ok | ok | ok | changes/ vorhanden |

# Architecture Decision Records (ADRs) — PAL MCP Server

Eine ADR pro Architektur-Entscheidung. Sie ist zugleich die **Übergabe-Doku**: Der Hub-Agent liest
nach `git pull` zuerst die jüngste ADR, um zu verstehen, was sich geändert hat und wie es weitergeht.

## Format (aus ThinkHub `DEVELOPMENT-WORKFLOW.md` §8)

```markdown
# ADR-NNN: Titel
**Status:** Proposed | Accepted | Implemented | Deprecated
**Datum:** YYYY-MM-DD

## Kontext
Warum die Entscheidung nötig ist.

## Entscheidung
Was entschieden wurde und warum.

## Alternativen
Was verworfen wurde und warum.

## Konsequenzen
Positiv, negativ, Risiken.
```

## Index

| ADR | Titel | Status |
|-----|-------|--------|
| 001 | cli_consensus — Multi-Modell-Konsens über Abo-CLIs | Implemented |
| 002 | Globaler CLI-Backend-Schalter (`PAL_BACKEND`) | Implemented |
| 003 | Keyfree Host-CLI-Runner — Draht-Vertrag & CO-01-Rebuild-Konformität (Referenz-Spiegel; Eigentum Core) | Reference |

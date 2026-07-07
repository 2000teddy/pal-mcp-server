# 2026-07-07 — MD-Pflege: Altlasten nachziehen + Rollen/Phasen klären (PR A)

Umsetzung von Christians Beschluss (`~/hermes/reference/2026-07-07_MD-Pflege-Audit-und-Durchsetzungssystem.md`)
für die pal-Lane, Teil A. Teil B (warnendes CI-Gate) folgt als separater PR.

## Altlasten bereinigt
- **CHANGES.md:** PRs #1–#11 nachgetragen (ADR-002/PAL_BACKEND, Reviewer-Guard, hermetischer
  Unit-Gate, agy-clink-Client, Doku-Welle, ELv2) — war seit 18.06. eingeschlafen.
- **HISTORY.md:** Erzähl-Nachtrag für die Lücke #1–#11 + Eintrag zu dieser MD-Pflege (neuestes oben).
- **COMPLIANCE-TABLE.md:** rückwirkend mit Zeilen #1–#12 befüllt (war verwaist/Template).
- **TODO.md:** 3+ erledigte Punkte abgehakt (Hub-Deploy-Smoke, OAuth-CLIs, agy-clink-Client,
  CLAUDE.md-Lese-Reihenfolge, cli_consensus-Nutzerdoc), Rolle „Backlog + Fortschritt" festgeschrieben.

## Phasen-Schalter gestrichen
COMPLIANCE hängt nirgends mehr an „ab Phase 2" — ab sofort **immer Pflicht je PR**. Betroffene
Stellen bereinigt: `COMPLIANCE-TABLE.md`, `CONTRIBUTING.md` (Branch-Strategie), `DEVELOPMENT-WORKFLOW.md`
(§2 + Doku-Familie-Tabelle), `TODO.md` (Sektion „Später / Phase 2" entfernt).

## Rollen festgeschrieben
`CONTRIBUTING.md` trägt jetzt die kanonische 5-Datei-Rollen-Tabelle (changes/ = je PR granular ·
CHANGES.md = technische Programm-Historie · HISTORY.md = Agenten-Erzählung, bleibt ·
COMPLIANCE-TABLE.md = immer Pflicht · TODO.md = Backlog + Fortschritt).

## Validierung
Reine Doku-/Governance-Änderung, **kein Python/Dockerfile** → kein Test-/Build-Delta. `code_quality_checks.sh`
unverändert relevant (Lint/Tests unberührt).

## Status
Kein Selbst-Merge. Review nur über claude/codex/agy (nie MiniMax/pal:chat).

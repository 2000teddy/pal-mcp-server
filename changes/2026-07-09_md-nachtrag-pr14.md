# 2026-07-09 — MD-Nachtrag: PR #14 in CHANGES/COMPLIANCE dokumentiert

Reiner Doku-Nachtrag. Schließt den Compliance-Drift, den der Reland-PR #14
(warnendes MD-Compliance-Gate) offen gelassen hatte: Der Merge landete auf
`main`, ohne dass CHANGES.md und COMPLIANCE-TABLE.md die finale #14-Realität
trugen.

## Was
- **CHANGES.md:** Eintrag „Warn-Modus MD-Compliance-Gate relandet (#14)" ergänzt —
  Workflow nach geschlossenem Stack-PR #13 unverändert erneut auf `main` aufgelegt.
- **COMPLIANCE-TABLE.md:** Platzhalter-Zeile `13 | (dieser PR)` durch die faktische
  Zeile `14 | #14` (Reland, Datum 2026-07-08) ersetzt und um die Selbstzeile für
  **diesen** Nachtrags-PR ergänzt (Regel „je PR eine Zeile", keine Ausnahme).

## Warum getrennt vom Reland
Der Reland-PR #14 war CI-only und wurde gemergt, bevor die MD-Familie nachgezogen
war — genau die Lücke, die das neue Gate (warnend bis 2026-07-21) sichtbar macht.
Dieser Folge-PR zieht sie sauber nach.

## Validierung
Reine MD-/Governance-Änderung, **kein Python/Dockerfile** → kein Test-/Build-Delta.
`code_quality_checks.sh` unberührt. Lokal: `git diff --check` sauber.

## Status
Kein Selbst-Merge. Review nur über claude/codex/agy (nie MiniMax/pal:chat).

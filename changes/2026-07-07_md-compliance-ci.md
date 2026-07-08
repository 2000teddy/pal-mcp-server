# 2026-07-07 — Ebene 1: warnendes MD-Compliance CI-Gate (PR B)

Zweiter Teil der MD-Pflege (Christians Beschluss 2026-07-07). Baut die CI-Wand
(Ebene 1) auf Teil A (Rollen/Phasen) auf.

## Was
Neuer GitHub-Actions-Workflow `.github/workflows/md-compliance.yml`, der je PR prüft:
- **changes/-Eintrag** im Diff (ausnahmefähig via Titel-Präfix `docs:`/`chore:` oder Label
  `no-doc-needed`),
- **COMPLIANCE-TABLE.md-Zeile** im Diff (**immer Pflicht, keine Ausnahme** — entspricht dem
  gestrichenen Phasen-Schalter).

## Rollout
- **2 Wochen warnend** (bis `WARN_UNTIL=2026-07-21`): Verstöße erzeugen `::warning::`, Check bleibt grün.
- **Danach blockierend**: automatische Umschaltung über das Datum, kein zweiter Commit nötig.
- Damit der Check tatsächlich merge-blockierend wird, muss er nach dem Fenster in den
  **Branch-Protection-Rules als required status check** eingetragen werden (Repo-Setting, Admin) —
  in der PR-Beschreibung als Follow-up vermerkt.

## Validierung
- YAML-Syntax lokal geprüft (`python -c yaml.safe_load`).
- Reine CI-/Doku-Änderung, kein Produktcode → kein Test-/Build-Delta.

## Status
Stacked auf PR A (`chore/md-pflege-altlasten-rollen`); nach dessen Merge auf main rebasen.
Kein Selbst-Merge. Review nur über claude/codex/agy (nie MiniMax/pal:chat).

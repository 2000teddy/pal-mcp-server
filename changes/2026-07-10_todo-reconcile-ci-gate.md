# 2026-07-10 — TODO-Reconcile: Ebene-1-CI-Gate als gelandet abgehakt

Reiner Doku-/Bookkeeping-Nachtrag (Ebene-2-Reconcile). Der Reconcile-Wächter
verlangt, dass der TODO-Stand nicht hinter den Merge-Stand fällt.

## Was
- **TODO.md:** Sub-Item „Ebene 1: warnendes CI-Gate … (Folge-PR)" von `[ ]` auf `[x]`
  gesetzt — das Gate ist mit **#14** gelandet (`.github/workflows/md-compliance.yml`,
  `WARN_UNTIL=2026-07-21`, Flip auf blockierend automatisch per Datum). Parent-Item
  „MD-Pflege / Durchsetzungssystem" damit auf `[x]` (alle Sub-Items erledigt).
- Verbleibender **Repo-Admin-Follow-up** im TODO benannt: Check nach dem Warn-Fenster
  in Branch-Protection als *required status check* eintragen (Admin-Setting, kein Code).

## Warum jetzt
Nach Merge von #14/#15 war die TODO-Checkbox veraltet; faktisch verifiziert, dass
der Workflow auf `main` liegt und WARN_UNTIL korrekt gesetzt ist.

## Validierung
Reine MD-Änderung, **kein Python/Dockerfile** → kein Test-/Build-Delta.
Lokal: `git diff --check` sauber.

## Status
Kein Selbst-Merge, kein PR ohne echten Review (claude/codex/agy, nie MiniMax/pal:chat).
Auf Feature-Branch vorbereitet, wartet auf Review-Freigabe.

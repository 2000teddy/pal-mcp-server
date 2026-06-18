# CONTRIBUTING — PAL MCP Server

> Ergänzt `AGENTS.md` (Repository Guidelines) und `DEVELOPMENT-WORKFLOW.md`.
> pal nutzt **`semantic-release`** — die Commit-Form steuert die Versionierung, daher verbindlich.

## Commits — Conventional Commits (PFLICHT, semantic-release-kritisch)

```
type(scope): summary
```

- `type` ∈ `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
- `feat:` → Minor-Bump · `fix:` → Patch · `feat!:` / `BREAKING CHANGE:` → Major
- **Nicht** das ThinkHub-`[agent-typ] scope:`-Format verwenden — es bricht die Changelog-Generierung.
- Agent-Attribution als Trailer:
  ```
  Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
  ```
- Git-Identität einheitlich: `Christian Ullmann <teddy2000@me.com>`.

## Vor jedem Push (Pre-Push-Checkpoint)

Siehe `DEVELOPMENT-WORKFLOW.md` §3: kein `.env`/Secret im Commit · `./code_quality_checks.sh` grün ·
nicht hinter `origin` (sonst erst rebasen).

## Branch-Strategie

- **Phase 1 (aktuell):** direkter Push auf `main` erlaubt (Solo-Bootstrap), Pre-Push-Check ist das Gate.
- **Phase 2+:** Branch Protection, Feature-Branches + PR.

## Doku-Pflicht nach jeder Änderung

`CHANGES.md` (Fork-Änderung, sofort) · `HISTORY.md` (am Aufgabenende) · `TODO.md` (laufend) ·
`BUILD_NUMBER.md` +1. Architektur-Entscheidungen als **ADR** unter `docs/architecture/`.

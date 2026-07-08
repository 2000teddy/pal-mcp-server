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

Feature-Branch + PR; Review nur über **claude/codex/agy** (nie MiniMax/pal:chat); **kein Selbst-Merge**,
Merge-Bit erst nach grüner unabhängiger Review. (Der frühere „Phase 1 = direkter Push auf main"-Modus
ist gestrichen — es gibt keinen Phasen-Schalter mehr.)

## Doku-Rollen (verbindlich, je PR) — Christians Beschluss 2026-07-07

Die fünf Pflege-Dateien haben **verschiedene Leser** und sind **keine Redundanz**:

| Datei | Leser | Inhalt | Takt | Durchsetzung |
|---|---|---|---|---|
| `changes/<datum>_*.md` | Review/Audit | **je PR** ein granularer Eintrag (was, warum, Tests, Status) | **jeder PR** | CI-Wand (Ebene 1), blockierend |
| `CHANGES.md` | Nutzer / Versionsstand | die **technische** Programm-Historie, konsolidiert, sauber versioniert | je PR/Release | CI-Wand |
| `HISTORY.md` | **die Agenten** | die **Erzählung fürs Team** — Kontext, Warum, Entscheidungen (Agentenwissen, das nicht in CLAUDE.md gehört) | fortlaufend, **narrativ** (nicht zwingend je PR) | Wächter (Ebene 2), soft — nicht > 5 PRs einschlafen |
| `COMPLIANCE-TABLE.md` | Prozess-Nachweis | wurde der Ablauf (CO/DOC/TS/CR/PP/DO) je PR eingehalten | **jeder PR — IMMER Pflicht** | CI-Wand, blockierend |
| `TODO.md` | nächste Arbeit | Backlog **und** Fortschritt (offen/erledigt) | fortlaufend | Wächter (Ebene 2), soft — Sync-Abweichung wird gemeldet |

Zusätzlich: `BUILD_NUMBER.md` +1 pro Arbeitsschritt · Architektur-Entscheidungen als **ADR** unter
`docs/architecture/` · `CHANGELOG.md` ist **Upstream-auto** (semantic-release) — nicht manuell anfassen.

**COMPLIANCE-TABLE ist ab sofort in JEDEM PR Pflicht** (kein „ab Phase 2" mehr). Ein warnendes
CI-Gate prüft je PR mindestens `changes/`-Eintrag + COMPLIANCE-Zeile (2 Wochen warnend, dann blockierend);
Ausnahme nur mit Label `no-doc-needed` **mit Begründung** oder Titel-Präfix `docs:`/`chore:`.

# Entwicklungs-Workflow — PAL MCP Server

> Übernommen aus dem ThinkHub-Muster (`thinkhub/DEVELOPMENT-WORKFLOW.md` v2.0, abgeleitet aus
> `_muster-mcp`) und **angepasst an pal**: zen-mcp-Fork, Python, v9.8.2, `semantic-release`,
> Conventional Commits, eigener Test-Workflow (`code_quality_checks.sh`).
>
> **Ergänzt** die bestehende `AGENTS.md` (Repository Guidelines) und `CLAUDE.md` (Dev-Guide) —
> ersetzt sie nicht. Bei Überschneidung gilt der pal-spezifische Stand dort.
> Stand: 2026-06-17.

---

## 0. Wie zu lesen

pal ist ein **reifes** source-available Repo (ELv2), das in den **ThinkHub-Verbund** integriert wird (zentral
auf dem Hub hinter mcporter + Bridge, von dort an die Mesh-Agenten verteilt). Dieser Workflow bringt
die ThinkHub-Konventionen — Phasen-Modell, Doku-Pflege, PR-Reihenfolge, ADRs — auf pal, **unter
Wahrung von pal's Eigenheiten** (`semantic-release`, Conventional Commits, `code_quality_checks.sh`).
Das DB-/Postgres-/Multi-VM-Material des ThinkHub-Musters ist hier bewusst weggelassen (pal ist ein
stdio-MCP-Server, kein DB-Backend).

---

## 1. Grundprinzipien

- **Agent ist Chefentwickler** — Implementierungsentscheidungen eigenständig.
- **Multi-Modell** — Architektur-Fragen per Konsens (künftig `cli_consensus`); Code-Review durch ein
  *anderes* Modell als das implementierende.
- **Tests sind Pflicht** — explizit getrackt, nicht „selbstverständlich".
- **Author once, deploy per Hub-pull** — Code/Doku an EINER Stelle erzeugen (Mac
  `/Users/chris/pal-mcp-server`), der Hub zieht per `git pull`. Nie dieselbe Datei auf zwei Maschinen
  parallel erzeugen.
- **Phasen-Bewusstsein** — die Strenge skaliert mit der Phase (§6).

---

## 2. Reihenfolge pro Feature/Fix (verbindlich)

```
1.  CO    — Konsens:     Bei Architektur-Fragen 2-3 Modelle (künftig cli_consensus)
2.  DOC   — Design-Doku:  ADR (docs/architecture/ADR-NNN-*.md) VOR dem Code
3.  CODE  — Implementierung
4.  TS    — Tests:        ./code_quality_checks.sh (Ruff+Black+isort+pytest) muss grün sein
5.  CR    — Code Review:  Externes Modell (nicht das implementierende)
6.  FIX   — Findings:     HIGH/CRITICAL sofort fixen, nie als TODO verschieben
7.  TS    — Tests erneut: Nach Fixes nochmal grün
8.  PP    — Pre-Push:     Secret-Scan + Remote-Sync-Check (§3)
9.  COMMIT — Conventional Commits + Co-Authored-By (§5)
10. PUSH
11. DO    — Doku:         CHANGES.md + HISTORY.md + TODO.md + BUILD_NUMBER +1
```

In **Phase 1** (aktuell) gibt es keine Compliance-Tabelle und keinen zweiten Reviewer-Zwang —
der Pre-Push-Checkpoint (§3) ist das Minimal-Gate.

---

## 3. Pre-Push-Checkpoint

Letzter Moment, an dem ein Fehler *gratis* korrigierbar ist. Vor JEDEM Push:

```bash
# 1. Kein Secret/.env im Staging?
git diff --cached --name-only | grep -qE '(^|/)\.env$' && echo "STOP: .env im Commit!" && exit 1
git diff --cached -U0 | grep -iE '(password|secret|api[_-]?key|token).*=.*[A-Za-z0-9]{16,}' && echo "WARN: möglicher Secret-Literal"

# 2. Kein Build-Müll?
git status --porcelain | grep -E '(__pycache__|\.pal_venv/|\.pyc$|logs/)' && echo "WARN: Artefakt im Tree"

# 3. Remote nicht divergiert?
git fetch origin && git status -sb | grep -q 'behind' && echo "STOP: erst rebasen, origin ist voraus"
```

Relevant v.a. bei der **Kostenregel-Migration** (API-Keys aus `.env`) — Keys dürfen nie ins Repo.

---

## 4. Doku-Familie (pal)

| Datei | Zweck | Aktualisieren |
|-------|-------|---------------|
| `README.md` | Einstieg, Architektur, Quick-Start | bei größeren Releases |
| `CHANGELOG.md` | **Upstream-auto** (semantic-release) — **NICHT manuell anfassen** | automatisch beim Release |
| `CHANGES.md` | **Fork**-Changelog (ThinkHub-Änderungen, Keep-a-Changelog) | bei jeder Fork-Änderung |
| `HISTORY.md` | Fließtext-Verlauf der Fork-Arbeit (Kontext für Agenten) | am Ende jeder Aufgabe |
| `TODO.md` | Priorisierte Aufgaben, einzige „was kommt"-Quelle | laufend |
| `CLAUDE.md` / `AGENTS.md` | Dev-Guide / Repository Guidelines (bestehend) | bei Workflow-Änderung |
| `APP_VERSION.md` | Spiegel der App-Version; **SSOT = config.py/pyproject** | bei Release (mit config.py) |
| `BUILD_NUMBER.md` | Fork-Iterationszähler, +1 pro Arbeitsschritt | laufend |
| `COMPLIANCE-TABLE.md` | PR-Compliance-Tracking | **ab Phase 2** |
| `docs/architecture/ADR-*.md` | eine ADR pro Architektur-Entscheidung | bei Entscheidung |

---

## 5. Commit-Konventionen (pal: Conventional Commits — semantic-release-kritisch)

```
type(scope): summary
```

`type` ∈ `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.
`feat:` → Minor-Bump · `fix:` → Patch · `feat!:` / `BREAKING CHANGE:` → Major.

**NICHT** das ThinkHub-`[agent-typ] scope:`-Format verwenden — es bricht die Changelog-Generierung.
Agent-Attribution als Trailer:

```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

---

## 6. Projekt-Phasen-Modell

| Phase | Charakter | Branch | Compliance-Tabelle | Gate |
|-------|-----------|--------|--------------------|------|
| **1 — Bootstrap (AKTUELL)** | Solo + Agenten, ThinkHub-Integration | direkter Push auf `main` | nein | Pre-Push-Check (§3) |
| 2 — Hardening/Multi-Agent | mehrere Agenten/Maschinen | Branch + PR | **Pflicht** | CI + Compliance |
| 3 — Production | produktiv im Mesh | geschützt | Pflicht | voll |

---

## 7. Agent-Lese-Reihenfolge bei Session-Start

Bevor du handelst, lies aus dem Repo (nicht aus altem Chat-Kontext):

```
AGENTS.md / CLAUDE.md  →  TODO.md  →  HISTORY.md  →  DEVELOPMENT-WORKFLOW.md
→  docs/architecture/  →  task-spezifische Docs
```

---

## 8. ThinkHub-Integration (Deploy-Pfad)

```
AUTHOR (hier, Mac /Users/chris/pal-mcp-server):
  Code/Doku erzeugen → Tests grün → commit → push

DEPLOY (Hub TH01):
  git pull → .env-Anpassung (Kostenregel) → Dienst-/Bridge-Neustart → Smoke-Test
  → mcporter + Bridge (supergateway, stdio→Port) exponieren pal wieder im Mesh
```

Der TH-Agent liest nach dem Pull zuerst die **Übergabe-ADR** unter `docs/architecture/`.

---

*Lebendes Dokument — fortschreiben, wenn neue Patterns entstehen. Übernommen aus ThinkHub v2.0, pal-angepasst 2026-06-17.*

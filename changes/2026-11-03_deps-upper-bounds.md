# 2026-11-03 — Dependency-Drift, Restfläche: Obergrenze je Zeile mit Testnachweis

Folge-PR zum TODO-Punkt „🟡 Dependency-Drift, Restfläche — noch ungeprüft" (eröffnet mit #20, der nur
`mcp` begrenzt hat). Methode wie im TODO beschrieben: **je Zeile eine frische venv + Testlauf**. Eine
Zeile gilt nur als begrenzt, wenn die Suite mit der Obergrenze grün läuft.

## Was
Obergrenze = nächstes Major oberhalb dessen, was ein ungepinnter Install **heute** auflöst
(Ausnahme `ruff`: 0.x, dort ist jede Minor potenziell regel-brechend → `<0.18`; `black`: CalVer,
Stil-Änderungen nur im ersten Release eines Jahres → `<27`). Untergrenzen bleiben unverändert.

- `requirements.txt:2-5` **und** `pyproject.toml:8-11` — dieselben vier Pakete, **derselbe** Bereich
  in beiden Dateien: `google-genai>=1.19.0,<3`, `openai>=1.55.2,<4`, `pydantic>=2.0.0,<3`,
  `python-dotenv>=1.0.0,<2`.
- `requirements-dev.txt:1-8` — alle acht Zeilen begrenzt.
- `requirements.txt:6` (`importlib-resources`) **bewusst offen**, siehe unten.

## Beweistabelle
Verfahren je Zeile: sauberer `git archive HEAD`-Export (kein `.env`), frische venv (Python 3.12,
`uv`), **nur diese eine Zeile** begrenzt, alle anderen wie auf `main`; dann CI-Kommando
`pytest tests/ --ignore=simulator_tests/ -m "not integration"`.

| Datei:Zeile | Paket | Obergrenze | aufgelöst (ungepinnt = begrenzt) | Suite (3.12, nur diese Zeile begrenzt) |
|---|---|---|---|---|
| `requirements.txt:2` / `pyproject.toml:8` | google-genai | `<3` | 2.34.0 (3.10: 2.33.0) | grün — 971 passed |
| `requirements.txt:3` / `pyproject.toml:9` | openai | `<4` | 3.42.1 | grün — 971 passed |
| `requirements.txt:4` / `pyproject.toml:10` | pydantic | `<3` | 2.14.2 | grün — 971 passed |
| `requirements.txt:5` / `pyproject.toml:11` | python-dotenv | `<2` | 1.2.4 | grün — 971 passed |
| `requirements.txt:6` | importlib-resources | — (offen) | nicht installiert (Marker `<3.9`) | n.a. |
| `requirements-dev.txt:1` | pytest | `<10` | 9.2.0 | grün — 971 passed |
| `requirements-dev.txt:2` | pytest-asyncio | `<2` | 1.4.1.post1 | grün — 971 passed |
| `requirements-dev.txt:3` | pytest-mock | `<4` | 3.17.0 | grün — 971 passed |
| `requirements-dev.txt:4` | black | `<27` | 26.10.1 | grün — 971 passed; `black --check` 263 unverändert |
| `requirements-dev.txt:5` | ruff | `<0.18` | 0.17.3 | grün — 971 passed; `ruff check` „All checks passed!" |
| `requirements-dev.txt:6` | isort | `<10` | 9.0.2 | grün — 971 passed; `isort --check-only` Exit 0 |
| `requirements-dev.txt:7` | python-semantic-release | `<11` | 10.7.0 | grün — 971 passed |
| `requirements-dev.txt:8` | build | `<2` | 1.6.1 | grün — 971 passed |

Alle „971 passed" = `971 passed, 4 skipped, 16 deselected`, 0 failed. Lint-/Format-Checks liefen mit
den CI-Kommandos aus `test.yml:54/57` in einer venv mit genau den begrenzten Tool-Versionen.

**Kombination (alle Grenzen gleichzeitig), CI-identisch** — `pip` statt `uv`, beide Dateien vom
Branch, CI-Matrix:

| Python | `pip check` | Suite |
|---|---|---|
| 3.10 | No broken requirements | 971 passed, 4 skipped, 16 deselected |
| 3.11 | No broken requirements | 971 passed, 4 skipped, 16 deselected |
| 3.12 | No broken requirements | 971 passed, 4 skipped, 16 deselected |

**Vorher/nachher:** ungepinnte Baseline von heute (frische venv, 3.12) → **971 passed, 0 failed**;
mit allen Grenzen → **971 passed, 0 failed**. Die aufgelösten Versionen sind **identisch** — der PR
ändert heute keine installierte Version, er verhindert nur den nächsten ungeprüften Major-Sprung.

## Bewusst offen
- **`importlib-resources` (`requirements.txt:6`)**: Marker `python_version<"3.9"`, das Projekt verlangt
  `requires-python >=3.9`, die CI-Matrix ist 3.10–3.12. Die Zeile wird in **keiner unterstützten
  Umgebung** installiert (CI 3.10–3.12, `Dockerfile` 3.11), also gibt es keinen Testlauf, der eine
  Obergrenze belegen könnte → keine Grenze ohne Nachweis. `requirements.txt` selbst trägt kein
  `requires-python` — auf 3.8 würde pip die Zeile installieren, aber 3.8 ist laut `pyproject.toml` nicht
  unterstützt. Ob die Zeile entfernt wird, ist eine eigene Aufräumfrage, nicht Teil dieses PRs.

## Begründung, warum auch `openai` und `google-genai` begrenzt sind
Die naheliegende Gegenposition („breite SDK-Familien offen lassen, eine Grenze kastet den
Produktpfad") wurde geprüft und verworfen: `openai` ist **unbemerkt bereits einen Major gesprungen**
— ein ungepinnter Install löst heute **3.42.1** auf, die lokale Lane-venv hat noch 2.38.0. Das ist
exakt die Mechanik, die `mcp` gebrochen hat (#20). Die Suite ist mit 3.x grün, deshalb `<4` und nicht
`<3`; beim nächsten Major entscheidet ein eigener Test-PR, statt dass CI ihn still einsammelt.
Einschränkung, ehrlich benannt: die Unit-Suite mockt die SDK-Aufrufe weitgehend; „grün" belegt
Import- und Schnittstellen-Verträglichkeit, nicht jeden Live-Pfad.

## Nebenbefunde (nicht in diesem PR geändert)
- **Lokale Lane-venv (`.pal_venv`) läuft hinter CI her:** black 26.5.1 (CI 26.10.1), ruff 0.15.18
  (0.17.3), isort 8.0.1 (9.0.2), openai 2.38.0 (3.42.1), google-genai 2.7.0 (2.34.0), mcp 1.27.2
  (1.30.0); `pytest-mock` ist dort gar nicht installiert (kein Test nutzt `mocker`, daher folgenlos).
  `code_quality_checks.sh` bevorzugt `.pal_venv`-Binaries → lokaler Check ≠ CI-Check. Lokale
  Umgebung, kein Repo-Inhalt.
- `semantic-release.yml:34` installiert `python-semantic-release` ohne Grenze; Zeile 39 installiert
  danach `requirements-dev.txt`. Erscheint ein PSR 11, wird es dort durch `<11` also **still auf 10.x
  zurückgesetzt** (Downgrade, gewollt: Release-Werkzeug bleibt auf der geprüften Major). Workflow unverändert.
- **`.pre-commit-config.yaml` ist eine dritte, abweichende Versionsquelle** (Review-Befund, nachgeprüft):
  exakte `rev:`-Pins `black 25.1.0` (`:5`), `isort 6.0.1` (`:10`), `ruff v0.12.8` (`:16`) — deutlich
  älter als CI (26.10.1 / 9.0.2 / 0.17.3). Driftet nicht (exakt gepinnt), ist aber weder in CI noch in
  `code_quality_checks.sh` verdrahtet; wer die Hooks lokal nutzt, formatiert/lintet gegen andere
  Versionen als CI. Angleichen wäre ein eigener PR mit eigenem Format-Lauf.
- **Release-Build übergeht `build<2`** (Review-Runde 3, nachgeprüft): `pyproject.toml:105`
  (`[tool.semantic_release] build_command`) führt `python -m pip install --upgrade build && python -m build`
  aus — dieses Upgrade ignoriert `requirements-dev.txt:8`. Erscheint `build` 2.x, baut der Release-Pfad
  damit, obwohl `<2` deklariert ist; die Beweistabelle belegt `build<2` nur für die Requirements-Installation
  (CI-Testpfad). Nicht angefasst (Release-Konfiguration); Angleichen hieße dort `"build>=1.0.0,<2"` —
  eigener PR.
- `run-server.sh:1028` (Hinweistext für manuelle Installation) und `:1037` (Rückfall-Install von
  `python-dotenv`) nennen Pakete ohne Version — Rückfallpfade, nicht angefasst.

## Release-Effekt
`main` ist ungeschützt (CI-Gate-1), ein Merge landet direkt und `semantic-release.yml` läuft auf
`push: main`. Ob ein Release entsteht, entscheidet der **Commit-Typ** des Squash-Titels
(`pyproject.toml`: `patch_tags = ["fix","perf"]`, `minor_tags = ["feat"]`):
- Der Workflow **läuft** bei jedem Merge (`push: main`) — auch ohne Release: Tests, `semantic-release
  version` ohne Bump, und der Bot-Commit `chore: sync version to config.py [skip ci]` (aktualisiert
  `__updated__`, so beobachtet nach #24).
- PR-Titel **`build(deps): …`** → `build` ist erlaubter Typ, aber kein Release-Trigger → **kein Release**.
  Gewählt, weil heute keine installierte Version wechselt.
- Falls ein Release gewünscht ist (damit `pyproject.toml`-Metadaten/Docker-Image die Grenzen tragen):
  Squash-Titel auf `fix(deps): …` ändern → Patch-Release, ausgehend vom aktuellen Tag `v9.9.2`
  (Stand 2026-11-03) also **v9.9.3** — vorausgesetzt, der Squash übernimmt den Titel als Commit-Subject
  (so bei #20 → v9.9.1 und #23 → v9.9.2 beobachtet).

## Review
Runde 1: `pal clink` claude/codereviewer (`claude-sonnet-5-5`) → **CHANGES-NEEDED**, nur Doku: (1) MEDIUM
`.pre-commit-config.yaml` als Versionsquelle fehlte — nachgeprüft (`:5/:10/:16`), zutreffend, ergänzt;
(2) MEDIUM Release-Absatz unvollständig (Workflow läuft auch ohne Release; PSR-Downgrade; v9.9.3 nur
bei Tag v9.9.2) — präzisiert; (3) LOW COMPLIANCE-Platzhalter „Review: siehe PR“ — ersetzt; (4) LOW
`TODO.md`-Kopfzählung „sechs Punkte“ — im datierten Nachtrag auf fünf gestellt; (5) LOW
`importlib-resources` „nie installiert“ nur auf ≥3.9 — präzisiert. Code-Diff vom Reviewer als korrekt
und konservativ bestätigt; Testzahlen und Paket-Semantik vom Reviewer **nicht** selbst nachgeprüft
(stammen aus den Läufen der Lane).

Runde 2 (Gegenprüfung, gleicher Reviewer) → **APPROVE**: alle 5 Befunde korrekt behoben, kein neuer
Fehler; Fakten zu `.pre-commit-config.yaml:5/:10/:16`, Tags, Bot-Commit und PSR-Downgrade
(`semantic-release.yml:34/39/48`) selbst nachgeprüft. Zwei nicht blockierende LOW-Hinweise umgesetzt:
offener Verweis „Runde 2: siehe changes/“ in COMPLIANCE durch das Ergebnis ersetzt; „wird nie
installiert“ bei `importlib-resources` überall zu „in keiner unterstützten Umgebung“ präzisiert.

Runde 3 (unabhängiges Review, Implementierer ≠ Reviewer): `pal:codereview` mit `model=cli-codex-gpt`
auf HEAD `0b30091` → Freigabe mit **1 LOW-Doku-Befund**: `build`-Grenze gilt nicht für den Release-Build
(`pyproject.toml:105`) — nachgeprüft, zutreffend, oben unter „Nebenbefunde“ ergänzt (nur Doku). Verworfen:
„nie greift“ in `HISTORY.md` (Satz ist bereits auf `requires-python >=3.9` eingeschränkt) und fehlendes
Python 3.9 in der CI-Matrix (bestand vorher, nicht durch diesen PR eingeführt).

## Was dieser PR ausdrücklich NICHT tut
Keine mcp-2.x-Migration, `mcp`-Pin unverändert, keine Untergrenzen geändert, kein Workflow-,
Branch-Protection- oder `schedule:`-Eingriff, kein `.env`/`AGY.md`. **Kein Merge durch die Lane** —
Merge über Christian bzw. den Approve-of-Record-Pfad.

# 2026-11-03 — Release-Build: `build<2` im semantic-release-`build_command` wirksam machen

Folge-PR zum TODO-Punkt „🟢 Release-Build übergeht `build<2`“ (Nebenbefund aus #25, als TODO
eingetragen mit #26).

## Was
`pyproject.toml:105` (`[tool.semantic_release] build_command`):

- vorher: `python -m pip install --upgrade build && python -m build`
- nachher: `python -m pip install "build>=1.0.0,<2" && python -m build`

Der Bereich ist **wörtlich** der aus `requirements-dev.txt:8` (dort seit #25 / `ea267af`).
Ursache der Lücke war der **fehlende Specifier** im separaten Install-Aufruf: `--upgrade build` holte
schlicht die neueste Version. Jetzt setzt der explizite Specifier die Grenze auch im Release-Build durch.
`--upgrade` ist zusätzlich entfernt (Vorgabe aus dem Auftrag). Damit bleibt eine bereits installierte,
passende Version erhalten (in CI hat `semantic-release.yml:39` den Bereich schon installiert). Eine
unpassende Version, etwa ein künftiges vorinstalliertes 2.x, ersetzt pip durch eine passende. `requirements-dev.txt` und alle anderen Grenzen bleiben unverändert.

## Weitere Stellen, an denen `build` installiert wird (geprüft, nicht geändert)
`git grep` nach `pip/uv … install … build`, `python -m build`, `pypa/build` (ohne `*.md`): **einzige**
Fundstelle ist `pyproject.toml:105`. `.pre-commit-config.yaml`, die Workflows unter `.github/`,
`scripts/` und `Makefile` (existiert nicht) installieren `build` nicht. `semantic-release.yml:39`
installiert `requirements-dev.txt` (also `build<2`) bereits vor `semantic-release version`.

## Quoting-Nachweis
`semantic-release` 10.7.0 führt `build_command` in
`semantic_release/cli/commands/version.py:301` über `shell()` aus, und zwar als
`subprocess.run([shell, "-c", cmd])` (Shell per `shellingham` erkannt, `version.py:182-206`). Das
Kommando geht also als **ein** String an eine echte Shell. Die doppelten Anführungszeichen halten
`>=1.0.0,<2` als ein Argument zusammen, und `<` wird nicht als Umleitung gelesen. TOML-seitig ergibt
`tomllib` den Wert `python -m pip install "build>=1.0.0,<2" && python -m build`.

## Beweis (Release-Pfad selbst, nicht nur das Kommando)
Wegwerf-Klon in Scratch, frische venv (Python 3.11 wie `semantic-release.yml`, `uv`, nur
`python-semantic-release>=10.3.0,<11`, **kein** `build` vorinstalliert), Remote-URL auf GitHub
gesetzt, aber **ohne Token**. Aufruf jeweils
`semantic-release -v version --patch --no-commit --no-tag --no-push --no-changelog --no-vcs-release`.
`--patch` erzwingt den Build-Schritt, obwohl seit v9.9.2 kein Release-Commit da ist. Es entstand kein
Commit, kein Tag, kein Push und kein Release; der Klon wurde verworfen.

| Lauf | `build_command` | pip-Auflösung | Ergebnis |
|---|---|---|---|
| neu (dieser Branch) | `pip install "build>=1.0.0,<2" && python -m build` | `Collecting build<2,>=1.0.0` → build 1.6.1 | Exit 0, `pal_mcp_server-9.9.3` sdist + wheel gebaut |
| Gegenprobe (`main` `3fc17c1`) | `pip install --upgrade build && python -m build` | `Collecting build` → build 1.6.1 | Exit 0, sdist + wheel gebaut |

**Grenze der Aussage, ehrlich:** `build` 2.x **existiert heute nicht**. `pip index versions build`
liefert als höchste Version **1.6.1**. Beide Pfade lösen deshalb heute identisch 1.6.1 auf. Die
Gegenprobe belegt, dass die Änderung den Release-Build nicht kaputtmacht. Dass das alte Kommando
bei einem künftigen 2.x die Grenze **überspringen** würde, lässt sich heute nicht live zeigen. Ersatzweise ist
belegt, dass der Specifier tatsächlich begrenzt: `pip install --dry-run "build>=1.0.0,<1.6"` löst
**1.5.0** statt 1.6.1 auf. Dieselbe Mechanik greift bei `<2`, sobald 2.x erscheint.

## Tests
Sauberer `git archive HEAD`-Export (ohne `.env`), frische venv (3.12) aus `requirements.txt` und
`requirements-dev.txt`:
- `pytest tests/ --ignore=simulator_tests/ -m "not integration"` → **971 passed, 4 skipped, 16 deselected**
  (vorher auf `main` ebenso 971; unverändert).
- `ruff check .` → „All checks passed!“; `black --check .` → 263 unverändert; `isort --check-only .` → Exit 0.

## Release-Effekt
`[tool.semantic_release.commit_parser_options]`: `patch_tags = ["fix","perf"]`,
`minor_tags = ["feat"]`, `build` ist nur in `allowed_tags`. PR-Titel **`build: …`** → **kein Release**.
Beim Merge läuft der Workflow trotzdem (`push: main`): Tests, `semantic-release version` ohne
Bump. So beobachtet bei #25 (`build(deps)`, Lauf `41632488399` grün, kein Release, kein Bot-Commit).
Da kein Release entsteht, wird der neue `build_command` erst beim nächsten echten Release ausgeführt.

## Review
`pal:codereview` mit `model=cli-codex-gpt` (Implementierer Opus ≠ Reviewer) → **Freigabe**, keine
funktionalen Befunde. Bestätigt wurden TOML-Maskierung und Shell-Semantik (`[shell, -c, cmd]`, `&&`),
das pip-Verhalten ohne `--upgrade` und die Release-Sicherheit (`build` ∉ `patch_tags`/`minor_tags`).
1 LOW-Doku-Befund: die Ursache war ungenau als „`--upgrade`“ beschrieben, tatsächlich fehlte der
Specifier. Oben unter „Was“ präzisiert. Einschränkung: Der Reviewer konnte wegen eines Sandbox-Fehlers
nicht lokal nachmessen. Er prüfte die bereitgestellten Inhalte; Testzahlen, `git grep` und
PSR-Läufe stammen aus den Läufen der Lane.

## Was dieser PR ausdrücklich NICHT tut
Keine Änderung an `requirements-dev.txt`, `mcp<2`, `google-genai<3`, `python-semantic-release<11` oder
einer anderen Grenze. Kein Workflow-Eingriff (auch nicht am ungepinnten
`pip install python-semantic-release` in `semantic-release.yml:34`, das ist dokumentiert seit #25).
Kein Release, kein Deploy, kein `.env`.

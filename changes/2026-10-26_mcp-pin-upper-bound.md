# 2026-10-26 — `mcp` nach oben begrenzen (`mcp>=1.0.0,<2`)

Folge-PR zum Review-of-Record von PR #19 (`claude-sonnet-5-5`, APPROVE,
`issuecomment-6409932957`). Dort war der Befund: `requirements.txt:1` pinnte `mcp>=1.0.0` **ohne
Obergrenze**, CI installierte inzwischen mcp **2.3.0**, und dort ist die lowlevel-Dekorator-API
entfallen → `AttributeError: 'Server' object has no attribute 'list_tools'` an `server.py:731`
beim Modul-Import → **9 Collection-Errors** auf allen drei Matrix-Versionen.

Dieser PR ist **ein Einzeiler plus Nachweis**. Er fasst bewusst nichts anderes an.

## Was
**Beide** Versionsdeklarationen des Repos, gleich gezogen:
- `requirements.txt:1`: `mcp>=1.0.0` → **`mcp>=1.0.0,<2`**
- `pyproject.toml:7`: `"mcp>=1.0.0"` → **`"mcp>=1.0.0,<2"`**

`pyproject.toml` war im ersten Anlauf übersehen und kam über die Review herein (High-Befund). Das
war kein Schönheitsfehler: `pyproject.toml` ist die Metadaten-Quelle für Wheel und sdist, also
hätten `pip install .` und jeder Install des veröffentlichten Pakets weiter auf mcp 2.x aufgelöst
und am Import gebrochen — während `semantic-release.yml:48-49` nach einem `fix(deps)`-Titel genau
dieses Artefakt veröffentlicht. Der Release hätte einen Fix behauptet, den sein Artefakt nicht
enthält. `git ls-files | xargs grep -lE 'mcp[>=<~]'` bestätigt, dass es **keine weiteren**
Deklarationen gibt (kein Lockfile, kein `setup.py`, kein `setup.cfg`); `test.yml:25` und
`Dockerfile:24` lesen `requirements.txt`.

## Warum eine Obergrenze und nicht ein exakter Pin
`mcp 1.x` enthält die Dekoratoren, die `server.py` nutzt; innerhalb der 1er-Reihe sind
Patch-/Minor-Updates gewollt (Sicherheitsfixes). Ein exakter Pin (`==1.27.2`) würde die Drift
anhalten, aber auch jedes Sicherheitsupdate blockieren. `<2` ist die kleinste Änderung, die den
tatsächlichen Bruch ausschließt.

## Was dieser PR ausdrücklich NICHT tut
- **Keine Migration auf die mcp-2.x-API.** `server.py` nutzt die lowlevel-Dekoratoren an mehreren
  Stellen; in 2.x heißen die Einstiegspunkte `add_request_handler` / `get_request_handler` /
  `middleware`. Das ist ein Umbau, keine Umbenennung → bleibt eine **ADR-Frage** und ein offener
  TODO-Punkt.
- **Keine Obergrenzen für die übrigen Abhängigkeiten.** `requirements.txt:2-4`
  (`google-genai`, `openai`, `pydantic`) und **alle acht Zeilen** in `requirements-dev.txt`
  (`pytest`, `pytest-asyncio`, `pytest-mock`, `black`, `ruff`, `isort`,
  `python-semantic-release`, `build`) sind ebenfalls nur nach unten begrenzt. Der Auftrag verlangt
  ausdrücklich, das hier **nicht** mitzunehmen; es bleibt ein eigener offener Punkt. Dieser PR
  fasst `requirements-dev.txt` **nicht** an.

## Validierung
Siehe PR-Body für die vollständigen Läufe. Kurzform: frische venv aus
`requirements.txt` + `requirements-dev.txt`, dann der exakte CI-Befehl
(`pytest tests/ -v --ignore=simulator_tests/ -m "not integration"`), einmal CI-treu ohne `.env`
und einmal im Repo-Verzeichnis mit `.env`. Erfolgsmetrik ist **„keine Collection-Errors"** —
die 5 Failures, die nur mit `.env` auftreten, sind das in PR #19 belegte Umgebungsartefakt und
nicht Gegenstand dieses PRs.

## Bekannte Sequenz-Abhängigkeit zu PR #19
Der Backlog-Punkt, den dieser PR erledigt, steht in `TODO.md:47` **des #19-Branches** — auf `main`
existiert er noch nicht. Dieser PR ist von `main` gebranched (so beauftragt) und kann die Checkbox
deshalb nicht abhaken, ohne denselben Textblock ein zweites Mal anzulegen. Darum bleibt `TODO.md`
hier **unangetastet**; das Abhaken gehört in den PR, der als **zweiter** merged. Wird das
vergessen, führt `TODO.md` einen erledigten Punkt als offen — deshalb steht es hier, im PR-Body
und im Watchdog-Bericht.

## Offen geblieben (bewusst, mit Begründung)
- **Untergrenze `>=1.0.0` ist unrealistisch.** `server.py:31-43` importiert `ToolAnnotations`,
  `PromptsCapability` und `ToolsCapability` und übergibt `instructions=` an `InitializationOptions`
  (`server.py:1605-1607`) — Symbole, die mcp 1.0.0 noch nicht hatte. Die Untergrenze ist damit eine
  Zusage, die der Code nicht hält. Die **echte** Mindestversion zu bestimmen heißt bisecten
  (frische venv pro Kandidat) und ist ein eigener Schritt; dieser PR behebt den real auftretenden
  Bruch nach oben, nicht die theoretische Lücke nach unten. Als Folgepunkt notiert, nicht geraten.
- **`APP_VERSION.md` ist aus dem Takt:** `pyproject.toml:3` steht auf **9.9.0**, `APP_VERSION.md`
  auf **9.8.2**. Die Datei soll laut ihrem eigenen Kommentar die Version spiegeln. Nebenbefund
  dieses PRs, hier **nicht** mitgeändert (eigener Punkt).
- **`BUILD_NUMBER.md` nicht gebumpt** — so beauftragt. Hinweis: `CONTRIBUTING.md:44` sagt „+1 pro
  Arbeitsschritt" ohne Ausnahme für `fix`-PRs, und dies *ist* ein Arbeitsschritt, kein Doku-PR.
  Die Review hat das als Regel-Unklarheit markiert: entweder bumpen oder die Ausnahme in
  `CONTRIBUTING.md` festschreiben. Entscheidung liegt nicht in diesem PR.

## Review
`pal clink` · `cli_name=claude` · `role=codereviewer` → **`claude-sonnet-5-5`**, 2026-10-26.
Erstes Votum **CHANGES-NEEDED** mit einem High-Befund (`pyproject.toml` nicht mitgezogen) — der
Befund wurde nachgeprüft, traf zu und ist in diesem PR behoben.

## Status
Kein Selbst-Merge (`CONTRIBUTING.md` §Branch-Strategie). Review über `claude`
(`pal clink`, `role=codereviewer`); `codex` ist nicht einholbar (Token 08.07. abgelaufen, 401),
`pal:chat` ist für Reviews gesperrt.

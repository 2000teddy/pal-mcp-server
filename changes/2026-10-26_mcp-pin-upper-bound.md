# 2026-10-26 — `mcp` nach oben begrenzen (`mcp>=1.0.0,<2`)

Folge-PR zum Review-of-Record von PR #19 (`claude-sonnet-5-5`, APPROVE,
`issuecomment-6409932957`). Dort war der Befund: `requirements.txt:1` pinnte `mcp>=1.0.0` **ohne
Obergrenze**, CI installierte inzwischen mcp **2.3.0**, und dort ist die lowlevel-Dekorator-API
entfallen → `AttributeError: 'Server' object has no attribute 'list_tools'` an `server.py:731`
beim Modul-Import → **9 Collection-Errors** auf allen drei Matrix-Versionen.

Dieser PR ist **ein Einzeiler plus Nachweis**. Er fasst bewusst nichts anderes an.

## Was
- `requirements.txt:1`: `mcp>=1.0.0` → **`mcp>=1.0.0,<2`**.

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

## Status
Kein Selbst-Merge (`CONTRIBUTING.md` §Branch-Strategie). Review über `claude`
(`pal clink`, `role=codereviewer`); `codex` ist nicht einholbar (Token 08.07. abgelaufen, 401),
`pal:chat` ist für Reviews gesperrt.

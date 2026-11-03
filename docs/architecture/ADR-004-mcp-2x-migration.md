# ADR-004: Migration auf die mcp-2.x-API

**Status:** Proposed
**Datum:** 2026-11-03

> **Entwurf zur Entscheidung.** Dieses ADR implementiert nichts und ändert keine Grenze: `mcp>=1.0.0,<2`
> (`requirements.txt:1`, `pyproject.toml:7`) bleibt, bis es angenommen ist. Quelle der Fakten:
> `TODO.md` (Punkt „Migration auf die mcp-2.x-API“), `server.py`, und eine frische venv mit `mcp==2.3.0`
> (Stand 2026-11-03, `uv`, Python 3.12). Dort wurde jede Aussage über 2.x unten nachgeprüft.

## Kontext

Im Oktober installierte CI ungepinnt mcp 2.3.0. Dort sind die lowlevel-Dekoratoren entfallen. Der
Modul-Import von `server.py` scheiterte mit `AttributeError`, und 9 Test-Dateien brachen bei der
Collection ab. Die Sofortmaßnahme war #20 (`mcp<2`). Sie hält das Fenster offen, löst die Frage aber
nicht. Heute löst `mcp<2` 1.30.0 auf; die lokale `.pal_venv` hat 1.27.2.

**Betroffene Fläche in diesem Repo (am Dateistand gezählt):**

| Stelle | 1.x-Nutzung | In 2.3.0 |
|---|---|---|
| `server.py:166` | `server: Server = Server("pal-server")` | Konstruktor bleibt, nimmt aber die Handler als Keyword-Argumente |
| `server.py:731` | `@server.list_tools()` → `handle_list_tools() -> list[Tool]` | **entfallen** → `on_list_tools(ctx, params) -> ListToolsResult` |
| `server.py:793` | `@server.call_tool()` → `handle_call_tool(name, arguments) -> list[TextContent]` | **entfallen** → `on_call_tool(ctx, CallToolRequestParams) -> CallToolResult \| InputRequiredResult` |
| `server.py:1392` | `@server.list_prompts()` → `handle_list_prompts() -> list[Prompt]` | **entfallen** → `on_list_prompts(ctx, params) -> ListPromptsResult` |
| `server.py:1442` | `@server.get_prompt()` → `handle_get_prompt(name, arguments) -> GetPromptResult` | **entfallen** → `on_get_prompt(ctx, GetPromptRequestParams) -> GetPromptResult \| InputRequiredResult` |
| `server.py:1601-1614` | `stdio_server()` + `server.run(r, w, InitializationOptions(...))` | unverändert vorhanden, gleiche `run`-Signatur |
| `server.py:31-44` + 13 weitere Dateien | `from mcp.types import …` (`TextContent`, `Tool`, `ToolAnnotations`, `Prompt`, `PromptMessage`, `GetPromptResult`, `ServerCapabilities`, `ToolsCapability`, `PromptsCapability`, `CallToolRequest`, `CallToolRequestParams`) | alle Namen in 2.3.0 vorhanden |

Nachgeprüft in 2.3.0: `hasattr(Server, "list_tools"|"call_tool"|"list_prompts"|"get_prompt")` ist jeweils
`False`. `Server.__init__` hat `on_list_tools`, `on_call_tool`, `on_list_prompts` und `on_get_prompt`.
`Server.add_request_handler` existiert für eigene Methoden. `middleware` ist **kein** Ersatz für die
Dekoratoren, sondern eine eigene Schicht: `ServerMiddleware` ist in `mcp/server/context.py:146` definiert
und wird in `mcp/server/runner.py` (`_apply_middleware`) angewendet.

**Nur `server.py` importiert aus `mcp.server`.** Die Tools (`tools/…`) nutzen ausschließlich `mcp.types`.
Die direkten SDK-Einstiegspunkte liegen deshalb voraussichtlich in einer Produktionsdatei. Das belegt
aber noch keine Verhaltensgleichheit, und es ist keine Umbenennung: Signatur und Rückgabetyp ändern sich
bei allen vier Handlern.

**Python-Untergrenze:** mcp 2.3.0 verlangt `Requires-Python >=3.10`. Das Projekt deklariert
`requires-python = ">=3.9"` (`pyproject.toml:5`). Eine Migration auf 2.x hebt die Untergrenze also
zwangsläufig auf 3.10. CI (3.10–3.12) und `Dockerfile` (3.11) sind davon nicht betroffen, 3.9-Nutzer schon.

**Tests, die die Handler direkt aufrufen** (müssen bei einer Migration mit umgebaut werden):
`tests/test_server.py` (5 Treffer), `tests/test_auto_mode_model_listing.py` (2) und
`tests/test_consensus_integration.py` (2).

## Alternativen

### A — Pin `mcp<2` beibehalten
Nichts ändern. Kosten: null. Risiko: 1.x bekommt irgendwann keine Fixes mehr. Clients, die nur noch
2.x-Protokollfeatures sprechen, könnten abweichen. Das Fenster bleibt offen, ohne dass es jemand misst.

### B — Auf mcp 2.x migrieren (einmaliger Schnitt)
Die vier Handler werden auf die `on_*`-Konstruktor-Argumente umgestellt. Die Rückgaben werden in die
typisierten `*Result`-Objekte gewickelt. Der Pin wird auf `mcp>=2.3.0,<3` gesetzt, `requires-python`
auf `>=3.10`. Kosten: voraussichtlich eine Produktionsdatei (`server.py`), drei bekannte Test-Dateien sowie die
Metadaten (`requirements.txt:1`, `pyproject.toml:5` und `:7`). Weitere Anpassungen können sich aus den
Protokolltests ergeben; die Tool-Schicht bleibt nach heutigem Stand unberührt. Risiko:
Verhaltensänderungen im Protokoll-Handling (`ServerRequestContext`, `InputRequiredResult`), die die
gemockte Unit-Suite nicht sieht.

### C — Beide Linien per Abstraktionsschicht stützen
Ein dünner Adapter (etwa `server_compat.py`) erkennt die mcp-Version und registriert dieselben
Kern-Funktionen entweder per Dekorator (1.x) oder per `on_*` (2.x). Die Kern-Funktionen arbeiten mit
neutralen Typen. Kosten: zusätzlicher Code und eine doppelte CI-Matrix (1.x und 2.x), dauerhaft. Nutzen:
ein gleitender Übergang ohne harten Schnitt bei Nutzern auf 3.9.

## Entscheidung (Vorschlag — offen bis zur Annahme)

**Kurzfristig A, B als vorbereiteter, eigener PR; C wird verworfen.**

- A bleibt, bis einer der **Auslöser** eintritt:
  1. Ein Sicherheits-Fix erscheint nur noch in 2.x.
  2. Ein relevanter Client (Claude Code, Codex, agy) setzt ein 2.x-only-Protokollfeature voraus.
  3. mcp 1.x wird offiziell eingestellt.
  4. Christian entscheidet aktiv für B.
- B ist mit voraussichtlich einer Produktionsdatei plus Metadaten klein genug für einen einmaligen Schnitt. Eine Übergangsschicht (C) würde mehr
  Code und eine doppelte CI-Matrix dauerhaft mitschleppen, nur um 3.9 zu halten. 3.9 ist seit Oktober 2025
  End-of-Life und in CI ohnehin nicht getestet.

Offen und **nicht** Teil dieses ADR: ob `requires-python >=3.10` auch ohne Migration angehoben wird.

## Testplan (für B, vor dem Merge)

1. **Ausgangsstand unter 1.x festhalten:** frische venv auf `main` mit `mcp<2`.
   - Unit-Suite: `pytest tests/ --ignore=simulator_tests/ -m "not integration"`. Stand heute 971 passed,
     4 skipped, 16 deselected.
   - **stdio-Baseline:** derselbe Protokoll-Smoke wie in Schritt 4, ausgeführt unter 1.x. Requests und
     Antworten werden als JSON gespeichert, mit fester Konfiguration (gleiche `.env`-freie Umgebung,
     gleiches `PAL_BACKEND`) und festen Prompt-Argumenten. Diese Datei ist die Referenz für Schritt 4.
2. **Import-Gate:** frische venv mit `mcp>=2.3.0,<3` → `python -c "import server"` ohne Fehler und
   pytest **ohne** Collection-Error.
3. **Unit-Suite unter 2.x:** dieselbe Zahl grüner Tests wie im ersten Schritt. Umgebaut werden nur die
   Handler-Aufrufe in den drei oben genannten Test-Dateien. Keine Tests löschen; Abweichungen einzeln
   begründen.
4. **Protokoll-Smoke über echten stdio-Transport unter 2.x**, mit denselben Requests wie die Baseline aus
   Schritt 1: `initialize` → `tools/list` → `tools/call` für `version` und `listmodels` → `prompts/list`
   und `prompts/get`. Dazu zwei Fehlerfälle: `tools/call` mit unbekanntem Tool-Namen und `prompts/get` mit
   unbekanntem Prompt.
   - **Verglichen werden:** Tool-Namen und Anzahl, `inputSchema` je Tool, Prompt-Namen und
     Prompt-Inhalte, die Erfolgs-/Fehlerstruktur jeder Antwort (Ergebnis vs. Fehler, `isError`).
   - **Erwartete Unterschiede, ausgenommen:** SDK- und Paketversionen (etwa in der `version`-Antwort),
     Zeitstempel, Request-IDs und `protocolVersion` im `initialize`-Ergebnis.
5. **Simulator-Quick-Mode:** `python communication_simulator_test.py --quick` grün.
6. **Zwei-Peer-DoD** (Repo-Regel, `DEVELOPMENT-WORKFLOW.md` §2): je ein echter Tool-Call von einem
   macOS- und einem Linux-Peer, jeweils mit Auszug als Beleg.
7. **CI-Matrix** 3.10, 3.11 und 3.12 grün; `pip check` sauber; ruff, black und isort grün.

## Abbruchkriterien (B wird zurückgestellt, A bleibt)

- Der Vergleich aus Testplan-Schritt 4 zeigt in einem der benannten Vergleichsfelder eine Abweichung von der
  1.x-Baseline, deren Ursache nach einem Debug-Durchgang nicht geklärt ist. Die dort ausgenommenen
  Unterschiede zählen nicht.
- Der Umbau greift über `server.py` und die drei Test-Dateien hinaus in die Tool-Schicht (`tools/…`).
  Dann stimmt die Annahme „eine Datei“ nicht mehr, und das ADR muss neu bewertet werden.
- Testplan-Schritte 4 bis 6 sind nicht grün erreichbar, oder ein angebundener Client bricht.
- Eine Abhängigkeit (`google-genai`, `openai`, `pydantic`) kollidiert unter 2.x und lässt sich nicht
  innerhalb ihrer bestehenden Grenzen auflösen.

## Konsequenzen

- **A (heute):** keine Änderung; das Risiko bleibt sichtbar statt still, weil die Auslöser benannt sind.
- **B (bei Annahme):** ein `feat`- oder `fix`-PR löst einen Release aus. Die Python-Untergrenze steigt
  auf 3.10 (Breaking für 3.9-Nutzer, im Release-Text zu nennen). Der CO-01-Rebuild (`thinkhub-pal`)
  bekommt dann einen geänderten Server, Core muss ihn kennen.
- **C (verworfen):** wäre nur neu zu prüfen, falls ein Downstream nachweislich auf 3.9 angewiesen ist.

## Verweise
`TODO.md` (Punkt „Migration auf die mcp-2.x-API“), `changes/2026-10-26_mcp-pin-upper-bound.md` (#20),
`changes/2026-11-03_deps-upper-bounds.md` (#25).

# 2026-11-05 — PAL-Rat: MiniMax als viertes Backend, Standard-Modelle an einer Stelle

Auftrag des Administrators im Sinne von Christian (05.11.2026). Der Standard-Rat von `cli_consensus` ist
jetzt claude=`opus`, codex=`gpt-6.1-sol`, agy=`Gemini 4 Argon (High)`, minimax=`MiniMax-M3.1-Flash`.

## Was
- `conf/minimax_models.json`: neuer Eintrag `MiniMax-M3.1-Flash`.
- `clink/consensus_backends.py`: `MiniMaxBackend` (nutzt `providers/minimax.py`, kein CLI) und
  `load_panel_models()`. `default_backends()` liest alle Modelle aus der Konfiguration.
- `conf/cli_consensus_panel.json`: die **eine** Stelle für die Standard-Modelle, überschreibbar über
  `CLI_CONSENSUS_PANEL_CONFIG_PATH`.
- `tools/cli_consensus.py`: vier Backends. Das Eingabe-Schema hängt nicht an der Konfigurationsdatei, damit
  eine kaputte Datei nicht die Tool-Liste und damit den Server mitreißt.
- `pyproject.toml`: `minimax_models.json` und die Panel-Datei in die `data-files`. Ohne das fehlten beide
  im Wheel (am gebauten Wheel geprüft, siehe Tests).
- ADR-001 (Nachtrag), ADR-002 (Punkt 7), `docs/tools/cli_consensus.md`, `docs/configuration.md`, `.env.example`.

## Entscheidungen
- **Aliase:** Bestehende Aliase bleiben, wie sie sind: `minimax`, `minimax-m3`, `m3` und `minimax3` zeigen weiter
  auf `MiniMax-M3`. `PRIMARY_MODEL` bleibt `MiniMax-M2.7`. Neu sind nur `minimax-m3.1-flash`, `m3.1-flash` und
  `minimax3.1-flash`. Der Rat nennt das Modell über die volle ID, er braucht also keinen umgebogenen Alias.
- **`intelligence_score` 18:** Das ist **kein Messwert**, sondern die interne Rangzahl dieses Repos, unterhalb von
  M3 (19), damit sich die Reihenfolge nicht verschiebt. Der effektive Rang liegt bei beiden am Deckel 100;
  ein Test hält fest, dass M3 vor M3.1-Flash bleibt.
- **Kein Ersatz bei kaputter Konfiguration:** Fehlt die Panel-Datei oder ist sie ungültig, meldet das Tool
  einen Fehler. Eine eingebaute Liste wäre eine zweite Stelle und würde still andere Modelle befragen.
- **`cli_models.json` bleibt unverändert:** Der `CLIModelProvider` (ADR-002) und sein Katalog sind ein anderer
  Pfad. `cli-claude-sonnet` & Co. bleiben dort wie sie sind.

## Specs `MiniMax-M3.1-Flash` (Quellen, nicht geschätzt)
| Feld | Wert | Quelle |
|---|---|---|
| Modell-ID | `MiniMax-M3.1-Flash` | `GET /v1/models` (created 2026-09-16) |
| `context_window` | 1.000.000 | offizielle Doku `platform.minimax.io/docs/api-reference/text-openai-api` |
| `max_output_tokens` | 524.288 | gemessen: 524.288 → 200, 524.289 → 400 „does not support max tokens > 524288“ |
| `supports_temperature` | false | Doku: „any value passed has no effect“; Parameter wird daher nicht gesendet |
| `supports_images` / `max_image_size_mb` | true / 10 | gemessen (rotes PNG → „Red“); Grenze laut Doku |
| `supports_function_calling` | true | gemessen (`finish_reason=tool_calls`) |
| `supports_streaming` | true | gemessen (SSE-Chunks) |
| `supports_system_prompts` | true | gemessen |
| `supports_json_mode` | false | gemessen: `response_format=json_object` liefert bei Prosa-Prompt weiter Prosa |
| `supports_extended_thinking` | true | Doku: Thinking lässt sich nicht abschalten; Antwort im Feld `reasoning_content` |

Das Kontextfenster wurde **nicht** durch einen 1-Mio.-Token-Request nachgemessen (unnötige Kosten).

## Beobachtungen, die den Code bestimmen
- M3.1-Flash und M3 liefern `content` ohne Reasoning. **M2.7 schreibt `<think>…</think>` in `content`.** Der
  Backend entfernt diesen Block, sonst stünde bei `model`-Override das Reasoning im Votum.
- Thinking zählt zum Output-Limit: `max_tokens=1` ergab `finish_reason=length` und `content=None`. Der
  Backend meldet das als Fehler mit `finish_reason` und setzt selbst kein Limit.
- Fehlertexte laufen durch eine Key-Maskierung, ein 401 kann den Key nicht ins Tool-Ergebnis tragen.
- **Timeout und Abbruch:** `wait_for` kann den blockierenden Aufruf im Worker-Thread nicht abbrechen. Die laufende
  Anfrage endet über `read_timeout`, und `client.close()` verhindert, dass die Retries des Providers danach noch
  etwas senden. `client.close()` beendet **nicht** das bereits laufende `recv`; das zeigte der erste Fix-Versuch
  im Test gegen einen hängenden lokalen Socket. Schlimmster Fall: Der Thread läuft bis zu zwei `read_timeout` plus
  Retry-Pausen weiter, aber ohne neue Anfrage nach dem Abbruch.

## Beweis: echter Lauf
Über echten MCP-stdio-Transport gegen `server.py` dieses Branches, ohne `backends`-Angabe (Standard-Rat):

| Backend | Modell | Status | Dauer |
|---|---|---|---|
| claude | `opus` | success | 11,4 s |
| codex | `gpt-6.1-sol` | success | 14,0 s |
| agy | `Gemini 4 Argon (High)` | success | 44,8 s |
| minimax | `MiniMax-M3.1-Flash` | success | 7,1 s |

Wiederholt auf dem Stand nach Review-Runde 1: 4/4 `success` (11,6 s / 13,3 s / 33,6 s / 10,7 s).

`backends_consulted=4`, `successful=4`, `skipped_or_failed=[]`. Jedes Votum endete wie verlangt mit einer
`VERDICT`-Zeile (claude yes, die anderen drei no), die Antworten waren also eigenständig und vollständig.

**Überspringen ohne Key, live:** Export ohne `.env`, `MINIMAX_API_KEY` nicht gesetzt: `status=skipped`,
`skipped_or_failed=["minimax"]`, `error="MINIMAX_API_KEY not set: backend skipped, no fallback"`.
Der erste Versuch mit leerer Umgebungsvariable griff nicht, weil die lokale `.env`
`PAL_MCP_FORCE_ENV_OVERRIDE=true` setzt und der Key damit gewinnt. Das ist das vorgesehene Verhalten.

## Tests
Sauberer Export ohne `.env`, frische venv (3.12): `pytest tests/ --ignore=simulator_tests/ -m "not integration"`
→ **1002 passed, 4 skipped, 16 deselected** (vorher 971, 31 neu). ruff, black (263 unverändert), isort grün.
Wheel gebaut und in eine leere venv installiert: `load_panel_models()` liefert die vier Modelle,
der MiniMax-Katalog enthält M3.1-Flash.

Nicht gelaufen: `run_integration_tests.sh` und der Simulator-Quick-Mode. An deren Stelle steht der echte
Vier-Backend-Lauf oben. Die Zwei-Peer-DoD (macOS + Linux) ist hier nicht belegt: Der Lauf fand auf TH01 statt.

## Nebenbefunde (nicht in diesem PR geändert)
- **Der Reviewer-Guard fehlt im Code.** `CHANGES.md` (#2) und `CHANGELOG.md` nennen ihn, aber
  `assert_review_backend`, `CLI_BACKEND_NAMES`, `_resolve_expert_backend` und `tests/test_reviewer_guard.py`
  existieren auf `main` nicht. Der Commit `6577bc5` ist zwar Vorfahre von `main`, der Inhalt fehlt aber im
  Dateistand. Die Hausregel gilt also nur als Prozess, nicht als Code-Sperre.
- **`conf/cli_models.json` fehlt im Wheel** (`data-files` führt sie nicht auf). Docker ist nicht betroffen
  (`COPY . .`), eine Wheel-Installation im Subscription-Modus schon.

## Release und Deploy
Titel `chore:`, kein Release beim Merge. Inhaltlich ist es eine Erweiterung: Soll sie als Release erscheinen,
muss der Titel vor dem Merge auf `feat:` wechseln, das entscheidet Christian. Die ThinkHub-Container sind nicht
angefasst. Dort wirkt die Änderung erst mit einem Rebuild, im Container ohne die CLIs und ohne Key entsprechend
eingeschränkt. Der Deploy ist separat und braucht Christians Freigabe.

## Review
`codex exec -m gpt-6.1-sol` (Implementierer Opus, also anderes Modell), nicht über MiniMax oder `pal:chat`.
- Runde 1, MEDIUM: Timeout beendet den MiniMax-Aufruf nicht. Behoben, Test gegen hängenden Socket (ohne Fix 3 statt 1 Verbindung).
- Runde 2, MEDIUM: Dasselbe bei `CancelledError`. Behoben, eigener Test.
- Runde 3: APPROVE. Sie bekam nur Code-Diff und `clink/consensus_backends.py`; Katalog, Packaging und ADRs lagen in Runde 1 und 2 im Diff.

Einschränkung: Die codex-Sandbox konnte lokal keine Dateien lesen (`bwrap: … Operation not permitted`). Der
Reviewer prüfte Diff und die mitgelieferten Quellen; Testzahlen und Läufe stammen aus den Läufen der Lane.

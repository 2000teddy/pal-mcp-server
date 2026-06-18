# ADR-001: cli_consensus — Multi-Modell-Konsens über Abo-CLIs

**Status:** Implemented
**Datum:** 2026-06-17 21:27 (implementiert + selbst-reviewt 22:15, Build 2)

> Diese ADR ist zugleich die **Übergabe-Doku** für den Hub-Agenten: nach `git pull` zuerst lesen,
> um Änderung, Begründung und Folge-Schritte zu verstehen.

## Kontext

pals Modell-Aufrufe laufen über bezahlte Provider-APIs (OpenAI, Google, Anthropic, …). Im letzten
Monat verursachten allein GPT- und Gemini-API-Keys **~800 €**, während nur **~12 %** der Arbeit über
pal-Konsens läuft (≈80 % über den tmux-Orchestrator). Die Kosten stehen in keinem Verhältnis zum Nutzen.

Gleichzeitig existieren lokale CLI-Agenten, die über **bestehende Abos** statt API-Keys laufen:

| Backend | CLI | Auth / Abo |
|---------|-----|------------|
| `claude` | `claude --print --output-format json` | Claude Max (OAuth) |
| `codex` | `codex exec --skip-git-repo-check --sandbox read-only --json` | ChatGPT-Abo (OAuth) |
| `agy` | `agy -p --model <m>` (Plain-Text) | Google One AI Pro (OAuth) |

`agy` (Antigravity CLI) **ersetzt die `gemini`-CLI**, deren Consumer-Support eingestellt wird. agy ist
Multi-Modell (Gemini Flash/Pro, Claude Opus/Sonnet, GPT-OSS) mit **zwei getrennten Quota-Töpfen**
(Gemini · Claude/GPT). pal bringt mit `clink` bereits eine CLI-Subprozess-Brücke mit (Configs, Runner, Parser).

## Entscheidung

Ein neues Tool **`cli_consensus`** plus eine wiederverwendbare interne **`CliBackend`-Schicht**
(„Option 1.5"):

1. **Geblendet** wie das bestehende `consensus`: jedes Backend sieht nur die Originalfrage (+ Stance),
   nicht die Antworten der anderen. Stance-Prompts (for/against/neutral) aus `consensus.py` wiederverwendet.
2. **Ein-Schuss-parallel** — alle Backends gleichzeitig; der aufrufende Agent synthetisiert.
3. **Backend-Diversität** über drei getrennte Abo-Töpfe — Lastverteilung + Resilienz.
4. **Partial-Failure + Drossel-Awareness** — fällt ein Backend aus (ToS, Interface-Bruch, agy-429/Cap),
   wird der Slot übersprungen; der Konsens läuft mit den übrigen weiter.
5. **Kostenregel** — Backends über Abos; API-Provider standardmäßig aus (Keys aus `.env` →
   `get_provider()`=None → **kein stiller Fallback**). MiniMax als einzige bewusste API-Ausnahme
   (quota-limitiert, kostengünstig).

## Alternativen

- **Option 2 — CLI-*Provider*** (in `ModelProvider.generate_content` einklinken, alle Tools profitieren):
  **verworfen.** `generate_content()` ist synchron, die CLI-Aufrufe async → sync/async-Brücke mit
  Deadlock-Risiko in laufendem Event-Loop; ein Provider-Bruch träfe *alle* Tools. Unverhältnismäßig für
  12 % Nutzung (Konsens 3/3 + Code-Review). **Revisionsauslöser:** CLI-Last > ~40 % der Gesamtnutzung.
- **tmux-Agenten-Pool** (persistente Sessions): **verworfen für v1.** Geblendeter Konsens ist stateless →
  ein kurzlebiger Subprozess pro Anfrage genügt; Watchdog/Session-Pflege lösen ein hier nicht existentes Problem.

## Konsequenzen

**Positiv:** API-Konsens-Kosten entfallen; Modell-Diversität (Claude+GPT+Gemini); Resilienz durch drei
Töpfe; isolierter Blast-Radius (CLI-Bruch trifft nur `cli_consensus`, nicht chat/codereview/debug).

**Negativ / Risiken:**
- CLI-Output-Formate können sich mit CLI-Updates ändern → Adapter bewusst dünn + austauschbar.
- Abo-Nutzung zur Automatisierung ist ToS-Grauzone (privat, kein Reselling — bewusst akzeptiert).
- agy-Quota ist geteilt (Terminal + Web), rollierende 5h-/Wochen-Caps → Drossel-Awareness Pflicht.

## Hub-Deploy (Folge-Schritte für den TH-Agenten)

1. `git pull` (Author-once auf dem Mac → Hub zieht).
2. `.env`: API-Keys der zu deaktivierenden Provider entfernen/leeren (Kostenregel). MiniMax-Key bleibt erlaubt.
3. CLIs auf dem Hub verfügbar + per OAuth angemeldet (`claude`, `codex`, `agy`).
4. Dienst-/Bridge-Neustart (supergateway) → mcporter exponiert pal wieder im Mesh.
5. Smoke: ein `cli_consensus`-Lauf.

## Referenzen
- Architektur-Konsens (PoC, 3 Modelle, 2026-06-17): einstimmig Option 1.5.
- Verwandte Module: `tools/consensus.py`, `clink/` (Runner/Parser), `providers/registry.py`.

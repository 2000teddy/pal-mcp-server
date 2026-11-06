# ADR-001: cli_consensus — Multi-Modell-Konsens über Abo-CLIs

**Status:** Implemented — *superseded in part by [ADR-002](ADR-002-global-cli-backend.md)*
(die hier verworfene „Option 2 — CLI-Provider" wurde mit ADR-002 unter geänderten
Rahmenbedingungen bewusst umgesetzt; `cli_consensus` selbst bleibt unverändert bestehen)
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

## Nachtrag 2026-11-05: MiniMax als viertes Backend, Standard-Modelle an einer Stelle

Punkt 3 und 5 der Entscheidung gelten erweitert. Der Standard-Rat hat jetzt vier Backends:

| Backend | Standard-Modell | Weg |
|---------|-----------------|-----|
| `claude` | `opus` | Abo-CLI |
| `codex` | `gpt-6.1-sol` | Abo-CLI |
| `agy` | `Gemini 4 Argon (High)` | Abo-CLI |
| `minimax` | `MiniMax-M3.1-Flash` | API über `providers/minimax.py`, es gibt keine CLI |

- **Geblendet wie die anderen:** `minimax` bekommt denselben Prompt und sieht keine andere Antwort.
- **Kostenregel:** MiniMax bleibt die bewusste API-Ausnahme (gedeckelt/prepaid). „Keine API-Kosten" gilt
  damit nur noch für die drei CLI-Backends. Offene Per-Token-Provider nutzt das Tool weiterhin nicht.
- **Ohne Key:** `status="skipped"`, Eintrag in `skipped_or_failed`, kein Ersatzmodell.
- **Konfiguration:** Die Modelle stehen nur in `conf/cli_consensus_panel.json`, überschreibbar über
  `CLI_CONSENSUS_PANEL_CONFIG_PATH`. Fehlt die Datei oder ist sie ungültig, meldet das Tool einen Fehler.
  Eine eingebaute Ersatzliste gibt es bewusst nicht: Sie wäre eine zweite Stelle und würde bei kaputter
  Konfiguration still andere Modelle befragen.
- **Abgrenzung:** Die Hausregel „Code-Review nie über MiniMax" bleibt. Der Rat ist für Entscheidungsfragen
  da, ein MiniMax-Votum ersetzt kein Review über claude/codex/agy.

Beleg: `changes/2026-11-05_cli-consensus-minimax-panel.md`.

## Referenzen
- Architektur-Konsens (PoC, 3 Modelle, 2026-06-17): einstimmig Option 1.5.
- Verwandte Module: `tools/consensus.py`, `clink/` (Runner/Parser), `providers/registry.py`.

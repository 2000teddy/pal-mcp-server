# PAL MCP `cli_consensus` Plan

## Ziel

PAL MCP soll einen neuen provider-neutralen `cli_consensus` bekommen.

Nicht:

```text
PAL consensus
  -> Gemini API / OpenAI API / Anthropic API
  -> Pay-as-you-go-Kosten
```

Sondern:

```text
PAL cli_consensus
  -> agy / Antigravity CLI      -> Google OAuth / bestehende Subscription
  -> claude / Claude Code CLI   -> Claude-Login / bestehende Subscription
  -> codex / Codex CLI          -> OpenAI/Codex-Login / bestehende Subscription
  -> minimax-m3                 -> bewusst erlaubter API-Key, weil subscription-/quota-limitiert
```

`agy` ist nicht die Speziallösung, sondern nur ein CLI-Backend unter mehreren. Die Architektur muss generisch sein: CLI-Agenten plus explizit erlaubte API-Ausnahmen.

## Bereits Vorhanden

```text
PAL MCP
  ├─ consensus
  │  └─ existiert bereits, nutzt aber API-Provider über ModelProviderRegistry
  │
  ├─ clink
  │  └─ existiert bereits als CLI-Brücke
  │
  ├─ CLI-Configs
  │  ├─ gemini
  │  ├─ claude
  │  └─ codex
  │
  ├─ CLI-Runner
  │  └─ Subprozess pro Anfrage
  │
  ├─ Parser
  │  ├─ gemini JSON
  │  ├─ claude JSON
  │  └─ codex JSONL
  │
  └─ MiniMax
     └─ MiniMax-M3 ist bereits als API-Provider konfiguriert
```

## Neu Zu Bauen

Ein neues Tool:

```text
cli_consensus
```

Ablauf:

```text
User-Frage / Proposal
  -> cli_consensus
  -> baut pro Agent einen geblendeten Prompt
  -> Agent 1: agy, z.B. neutral
  -> Agent 2: claude, z.B. kritisch
  -> Agent 3: codex, z.B. planner/reviewer
  -> Agent 4: minimax-m3, z.B. supportive oder neutral
  -> sammelt alle Antworten
  -> gibt strukturierte Konsensdaten zurück
  -> Hauptagent synthetisiert daraus die finale Empfehlung
```

## Kostenregel

Default:

```text
CLI/OAuth ist bevorzugt.
MiniMax-M3 API ist als explizite Ausnahme erlaubt.
Alle anderen API-Key-Provider sind standardmäßig aus.
```

Kein stiller Fallback:

```text
Wenn agy nicht geht:
  -> nicht heimlich GEMINI_API_KEY nutzen
  -> klare Fehlermeldung

Wenn codex CLI nicht geht:
  -> nicht heimlich OPENAI_API_KEY nutzen
  -> klare Fehlermeldung

Wenn claude CLI nicht geht:
  -> nicht heimlich ANTHROPIC_API_KEY nutzen
  -> klare Fehlermeldung
```

## Technische Umsetzung v1

```text
cli_consensus
  -> nutzt bestehende clink-Subprozess-Infrastruktur
  -> agy als neuer CLI-Client
  -> claude und codex über vorhandene CLI-Configs
  -> minimax-m3 über explizit erlaubten API-Provider
```

Das ist einfacher, testbarer und passt zur vorhandenen PAL-Codebasis.

## Technische Umsetzung v2

Optionaler TMUX-Pool für persistente Agenten:

```text
tmux: pal-agy-neutral
tmux: pal-claude-critical
tmux: pal-codex-reviewer
```

Dafür braucht es zusätzlich:

```text
Session starten
Prompt senden
Output erfassen
Antwortende erkennen
Timeout behandeln
Session resetten
```

TMUX ist Performance-Ausbau, nicht Voraussetzung für die erste Version.

## Kurzfassung

```text
Baue cli_consensus als provider-neutrale Konsensschicht für PAL MCP.

Default:
  CLI/OAuth-Agenten statt API-Key-Provider.

Backends:
  agy, claude, codex über CLI.
  minimax-m3 als explizit erlaubte API-Key-Ausnahme.

Verboten:
  stille Fallbacks auf Gemini/OpenAI/Anthropic API-Keys.

v1:
  Subprozess über bestehendes clink.

v2:
  TMUX-Pool für persistente Agenten.
```

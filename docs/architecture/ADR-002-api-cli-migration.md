# ADR-002: API-Token-Tools auf Subscription-CLIs migrieren

- **Status:** Accepted (Konsens-gehärtet 2026-06-18 via cli_consensus; claude 8/10, agy 9/10, codex 8/10 — 3/3, $0 API)
- **Repo:** pal-mcp-server (Fork)
- **Verwandt:** ADR-001 (cli_consensus), `clink/consensus_backends.py`
- **Orchestrator:** Minimac/Desktop-Claude · **Umsetzung:** Claude-Pal-Dev (TH01)

## Kontext

pals „denkende" Tools rufen Provider-Modelle über kostenpflichtige API-Keys. Bei den
Workflow-Tools (analyze, codereview, debug, thinkdeep, precommit, refactor, secaudit,
testgen, docgen) läuft das über EINEN gemeinsamen Pfad: den **`expert_analysis`-Schritt**
(`should_call_expert_analysis` → `prepare_expert_analysis_context` →
`provider.generate_content()`, **synchron**). `chat` und `consensus` rufen Modelle
direkter. Insgesamt ~11 Tools sind API-abhängig; clink, cli_consensus, planner, tracer,
apilookup, challenge, listmodels, version sind es NICHT.

Ziel (Christian): die ~800 €/Monat API-Kosten eliminieren — pal nutzt die Modelle über
bereits bezahlte SUBSCRIPTION-CLIs (`claude --print` / `codex exec` / `agy -p`). Die async
CLI-Backend-Schicht (`clink/consensus_backends.py`) existiert und ist via `cli_consensus`
erprobt (live, 3/3).

## Entscheidung 1 — sync `expert_analysis` → async CLI-Backends

**`expert_analysis`-Pfad durchgängig async machen** und direkt die
`consensus_backends.py`-Schicht awaiten.

Begründung (Konsens):
- MCP-Tool-Handler laufen BEREITS in einem asyncio-Event-Loop. Jede naive Sync-Bridge
  (`asyncio.run()` im laufenden Loop) ist ein **garantierter Deadlock / RuntimeError**
  (alle 3 Modelle einig). `run_coroutine_threadsafe` nur über einen dedizierten
  Worker-Loop — unnötige Komplexität, wenn der Pfad async werden kann.
- `consensus_backends.py` ist bereits das richtige Interface; `expert_analysis` muss nur
  mit `await` draufzeigen — kein neues Abstraktionslayer.
- Native Timeout-/Cancel-Kontrolle via `asyncio.wait_for`; graceful degradation ist in
  `consensus_backends.py` schon implementiert.

**Fallback (codex-Position):** Falls Schritt 1 zeigt, dass harte synchrone Aufruf-Grenzen
existieren, die nicht ohne großen Umbau async werden: ein gehärteter sync→async-Bridge auf
einem **dedizierten Background-Thread-Event-Loop** (NIE `asyncio.run` im MCP-Loop), optional
als CLI-„Provider" verpackt. Nicht bevorzugt, aber zulässig.

## Entscheidung 2 — Deployment (Docker) — SEPARAT, ThinkHub-Core-Sache

Verschoben in eine eigene ThinkHub-Core-Entscheidung (eigenes ADR dort). Konsens-Tendenz
(2:1, codex+agy): **Host-CLI-Runner-Sidecar** — ein Host-Daemon mit CLIs+OAuth, vom
pal-Container über Unix-Socket erreicht; pal bleibt im Container (Hub-Konsistenz +
`--stateful`-Isolation), OAuth-Token bleiben auf dem Host. **Einstimmig verworfen:**
CLIs+Credentials in den Container mounten (Token-Exposure + glibc/Pfad-Brittleness).
Alternative (claude): pal nativ. → Gehört NICHT in dieses pal-Repo-ADR; nur referenziert.

## Reihenfolge / Konsequenzen

1. **ZUERST Entscheidung 1** (CLI-Migration, pal-intern) — läuft unabhängig vom Deployment.
2. **Schritt 1 (VOR jeder Code-Änderung):** verifizieren, wie tief der synchrone
   `expert_analysis`-Pfad sitzt — sind die Tool-Handler durchgängig async bis zum
   Provider-Call, oder gibt es echte sync-Grenzen? Ergebnis entscheidet
   async-end-to-end vs. Background-Loop. **Zurückberichten, bevor Code geändert wird.**
3. Dann: EIN gemeinsamer CLI-Backend-Hebel für alle Workflow-Tools; `chat` + `consensus`
   als Sonderfälle separat.
4. **DANACH Entscheidung 2** (Docker/Sidecar, ThinkHub-Core).

## Kosten/Nutzen

Ein zentraler Migrationspunkt (der `expert_analysis`-Hebel) statt ~11 Einzelmigrationen.
Kosten: API → 0 (Abo-gedeckt, nur Abo-Ratelimits). Risiko: Abo-Ratelimits unter Last —
`consensus_backends.py` erkennt + degradiert bereits.

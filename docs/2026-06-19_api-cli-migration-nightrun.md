# Nacht-Lauf 2026-06-18/19 — pal API→CLI-Migration (ADR-002)

> **Zusammenfassung eines autonomen Orchestrierungs-Laufs.**
> Zeitraum: 2026-06-18 21:50 → 2026-06-19 01:05 (~3 h 15 min).
> Orchestrator: Desktop-Claude (Minimac). Umsetzung: Dev-Agent **Claude-Pal-Dev** (tmux auf TH01).
> Status: **Code-Migration komplett + key-frei**, in [PR #1](https://github.com/2000teddy/pal-mcp-server/pull/1), noch nicht gemerged.

---

## 1. Ausgangslage & Ziel

pals „denkende" Tools riefen LLM-Modelle über **kostenpflichtige Provider-APIs** auf (~800 €/Monat).
Ziel: alle API-Token-abhängigen Tools auf die bereits bezahlten **Subscription-CLIs** (claude / codex /
agy) umstellen — und pal so betreibbar machen, dass am Hub **gar kein API-Key** mehr nötig ist.

Betroffen (kartiert): chat, thinkdeep, analyze, codereview, debug, precommit, refactor, secaudit,
testgen, docgen, consensus. Schon CLI/lokal: clink, cli_consensus, planner, tracer, apilookup,
challenge, listmodels, version.

**Kernbefund der Analyse:** Die 9 Workflow-Tools teilen sich EINEN gemeinsamen Aufruf-Pfad — den
`expert_analysis`-Schritt. Ein Eingriff dort deckt alle neun ab. chat + consensus sind zwei Sonderfälle.

## 2. Architektur-Entscheidungen (2× Konsens-gehärtet, $0)

Beide Designweichen wurden per `cli_consensus` (claude+codex+agy, blind, über die Abos) gehärtet:

1. **sync→async-Brücke (3/3):** Der `expert_analysis`-Pfad war bereits durchgängig `async`, nur das
   Blatt `provider.generate_content()` war synchron. → **async end-to-end** (ein `await`), kein
   `asyncio.run()`-Deadlock im MCP-Loop. Der „Background-Loop"-Fallback war nicht nötig.
2. **key-freier Betrieb (3/3 EINSTIMMIG Option B):** `requires_model()==False` auf die CLI-Tools
   (wie consensus/planner) statt eines Stub-Providers (Option A, abgelehnt: semantischer Zombie) oder
   eines globalen ModelContext-Fallbacks (Option C, abgelehnt: bricht „fail-fast" für echte API-Tools).

## 3. Die Phasen

| Phase | Inhalt | Commit |
|-------|--------|--------|
| **ADR** | ADR-002 angelegt (Strategie, Konsens-Ergebnis) | `docs(adr)` |
| **Verifikation** | sync-Tiefe des `expert_analysis`-Pfads kartiert (reine Analyse) | — |
| **A** | `_call_expert_analysis` (workflow_mixin) → `await backend.run()`. Deckt alle 9 Workflow-Tools. model→Backend-Mapping (claude/codex/agy + Default), BackendResult→dict-Adapter, graceful degradation. | `feat(workflow)` |
| **B** | chat (`simple/base.py`) + consensus (`_consult_model`) → CLI-Backend, via geteiltem Shim `backend_result_to_model_response` (kein Duplikat). consensus bleibt geblendet + partial-failure-safe. 12 Test-Dateien auf den neuen Mock-Seam umgestellt. | `feat(chat+consensus)` |
| **C** | Praxisnaher Live-Test (`tests/test_live_cli_structure.py`) über echte Abo-CLIs, `@pytest.mark.integration` (aus dem Gate ausgeschlossen). | `test(live)` |
| **E** | Key-freier Betrieb: `requires_model()==False` auf die 10 CLI-Tools + geteilter Helper `ModelContext.resolve(allow_keyfree=not requires_model())` + `default_no_provider_capabilities` (200k-Window, temp-skip). Echter Bug-Fix nebenbei: Modell-Kontinuität in `reconstruct_thread_context`. | `feat(keyfree)` |

(Dazwischen `style:` für repo-weite Formatierung.)

## 4. Ergebnisse

**Gate (TH01):** 902 passed, 19 skipped, **0 neue Fehler ggü. Baseline** — die 9 verbleibenden Fehler
sind ausschließlich die *vorbestehende* Gemini-Alias-Familie (pre-existing, unbeteiligt). 10 obsolete
„model-required"/Provider-API-/Bild-Tests sauber mit ADR-002-Grund `@pytest.mark.skip`.

**Live-Verifikation auf dem Minimac (echte Abos, kein API-Key):**
- `test_live_cli_structure` **4/4 grün** — cli_consensus (claude+codex), expert_analysis (claude),
  chat (claude), consensus (claude+codex).
- `test_keyfree_cli_operation` **5/5 grün** — volles `execute()` ohne Provider + Regression (MIT Key =
  Normalweg unverändert, reale Capabilities).

**6 Commits** auf Branch `feat/cli-backend-migration` → **PR #1** (offen, main unberührt):
`docs(adr)` · `style` · `feat(workflow)` · `feat(chat+consensus)` · `test(live)` · `feat(keyfree)`.

## 5. Offene Punkte (brauchen Christian)

1. **MacBook-Pro-Live-Test** — Laptop war nicht SSH-erreichbar (Key-Probing wurde korrekt vom
   Sicherheits-Classifier geblockt). Kommando:
   `.pal_venv/bin/python -m pytest tests/test_live_cli_structure.py -v -s -m integration`
2. **Merge PR #1** — bewusst Christian überlassen (sein Gate; main unberührt).
3. **Docker-Integration** — separate ThinkHub-Core-Phase (ADR-002 Entscheidung 2). Konsens-Tendenz
   2:1: **Host-CLI-Runner-Sidecar** (pal bleibt im Container, OAuth bleibt am Host); Mount einstimmig
   verworfen; pal-nativ als Alternative. Wartet auf Steuerung (Agent + Deploy-Entscheidung).

## 6. Arbeitsweise / Rollen

Strikte Trennung eingehalten: **Desktop-Claude orchestrierte** (Pläne, ADR, 2 Konsens-Härtungen,
Reviews, Permission-Freigaben, PR) — **Claude-Pal-Dev baute den gesamten pal-Code** auf TH01, mit
getrennten Commits, Pre-Commit-Secret-Scans, Baseline-Vergleichen und Test-Disziplin. Kein Zeile
pal-Code vom Orchestrator. Lief als 30-Min-Loop, autonom bis zum Abschluss.

## 7. Bekannte Folge-Punkte (dokumentiert, nicht blockierend)

- Deprecation von `consensus` zugunsten `cli_consensus` — separate Aufräumfrage.
- Docker-Integration (siehe §5.3).

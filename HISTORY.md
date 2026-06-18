# HISTORY — PAL MCP Server (ThinkHub-Fork)

> Chronologischer Fließtext-Verlauf der Fork-Arbeit, **neuestes oben**. Kontext für Agenten.
> Upstream-Changelog: `CHANGELOG.md` (auto, semantic-release). Fork-Changelog: `CHANGES.md`.

## 2026-06-18 — Phase A: expert_analysis über Subscription-CLI-Backend (Build 4)

ADR-002 Entscheidung 1, Phase A umgesetzt — der **zentrale Workflow-Hebel**. In
`tools/workflow/workflow_mixin.py:_call_expert_analysis` ersetzt jetzt ein einzelner
`await backend.run(prompt)` den synchronen `provider.generate_content(...)`-Call (Blatt der
ohnehin durchgängig async Kette, siehe Schritt-1-Bericht). Deckt **alle 9 Workflow-Tools**
(analyze, codereview, debug, thinkdeep, precommit, refactor, secaudit, testgen, docgen) auf
einen Schlag — sie erben `_call_expert_analysis`, keiner überschreibt es.

**Modell→Backend-Mapping** (neu in `clink/consensus_backends.py`, schlank + per Keyword,
erste Regel gewinnt): `claude/sonnet/opus/haiku → claude` · `gpt/openai/o1/o3/codex → codex` ·
`gemini/flash → agy` · sonst Default `claude` (+Log, „matched=False"). Default per
`PAL_EXPERT_CLI_DEFAULT_BACKEND` überschreibbar. Neue Helfer: `select_expert_backend_name()`,
`backend_for_model()`. **Einzel-Backend** (`backend.run`), bewusst NICHT `run_backends` — der
expert-Schritt ist ein Modell, kein Konsens.

**Adapter `BackendResult → dict`:** `success` → JSON-Parse wie bisher bzw. `raw_analysis`/
`format:text` bei Nicht-JSON; `rate_limited`/`error` → bestehender `analysis_error`-Pfad
(graceful); leerer Erfolg → `empty_response`. Äußeres `try/except` bleibt als Sicherheitsnetz.
Natives `CliBackend`-Timeout deckt den bisher fehlenden expert-Timeout ab (nichts doppelt).
CLI-Backends sind textbasiert: System-Prompt wird in den einen Prompt gefaltet, Bilder
werden mit Warn-Log verworfen (Temperatur/thinking_mode entfallen).

**Tests:** neu `tests/test_expert_cli_backend.py` (14: Mapping je Familie + unknown/None/Env-Override
+ Adapter success-JSON/fenced-JSON/plain-text/rate_limited/error/empty + System-Prompt-Folding);
`tests/test_workflow_utf8.py` auf den Backend-Seam (`_resolve_expert_backend`/`backend_for_model`)
umgestellt statt `provider.generate_content`. Beide Dateien grün (19/19). ruff/black/isort grün.
Gesamt-Unit-Suite: 9 Fehler — **alle** in der **vorbestehenden** Gemini-Alias-/Fallback-Familie
(`test_auto_mode_*`, `test_intelligent_fallback`, `test_per_tool_model_defaults`; `gemini-flash`
vs `gemini-2.5-flash`), NICHT von dieser Migration (vom Orchestrator bestätigt, vgl. commit 03cb50e).

**Offen:** Phase B = die zwei Sonderfälle `chat` (`tools/simple/base.py`) und `consensus`
(`tools/consensus.py`) — separat, auf OK des Orchestrators.

## 2026-06-18 — ADR-002 aufgenommen: API→CLI-Migration (Build 3)

ADR-002 (`docs/architecture/ADR-002-api-cli-migration.md`) ins Repo aufgenommen — vom
Orchestrator (Minimac) geliefert, konsens-gehärtet via `cli_consensus` (claude 8/10, agy 9/10,
codex 8/10 — 3/3, $0 API-Kosten). **Entscheidung 1:** den gemeinsamen synchronen
`expert_analysis`-Pfad der Workflow-Tools (analyze, codereview, debug, thinkdeep, precommit,
refactor, secaudit, testgen, docgen) durchgängig async machen und direkt die
`clink/consensus_backends.py`-Schicht awaiten — ein zentraler Hebel statt ~11 Einzelmigrationen,
eliminiert ~800 €/Monat API-Kosten. `chat` + `consensus` als Sonderfälle separat. **Entscheidung 2**
(Docker/Sidecar) ist verschoben — ThinkHub-Core-Sache, nicht dieses Repo.

**Schritt 1 (laufend, reine Verifikation, KEIN Code):** Tiefe des synchronen `expert_analysis`-Pfads
untersuchen — ist die Kette MCP-Handler → `generate_content()` durchgängig async oder gibt es eine
echte sync-Grenze? Ergebnis entscheidet „async end-to-end" (bevorzugt) vs. codex-Fallback
(dedizierter Background-Loop). Bericht → `/tmp/pal-dev-schritt1-bericht.md`, dann Stopp bis OK.

## 2026-06-17 — cli_consensus gebaut + selbst-reviewt (Build 2)

`cli_consensus` implementiert (ADR-001, „Option 1.5"): neues Tool + `CliBackend`-Schicht
(`clink/consensus_backends.py`), die claude/codex/agy als read-only Subprozesse über die Abos
befragt — geblendet, Stance-Prompts aus `consensus.py` (jetzt public `get_stance_enhanced_prompt`),
Ein-Schuss-parallel, Partial-Failure + Drossel-Awareness. agy (Antigravity, Gemini-CLI-Nachfolger)
nimmt den Prompt als **Argument** (nicht stdin) + liefert Plain-Text → eigener `agy_text`-Parser.
Eigener schlanker async-Runner (nicht der clink-Agent, dessen stdin-Zwang + agentische Flags wie
`--yolo` unpassend sind); clink-**Parser** wiederverwendet.

**Selbst-Review per Dogfooding** (cli_consensus auf eigenen Code, 3/3 Backends, 8–9/10 Confidence)
fand echte HIGH-Bugs: `gather` ohne `return_exceptions` + Parser-Exceptions außer `ParserError`
brachen die „never-raises"-Garantie; agy-ARG_MAX-Crash bei langen Prompts; Post-kill-Hang +
verwaiste Kinder; non-zero Exit ignoriert. **Alle gefixt** (top-level no-raise, broaden except,
ARG_MAX-Guard, `start_new_session`+killpg, bounded reap, dedup + Backend-Cap).

**21 Unit-Tests grün, ruff/black/isort grün, Backend- + Tool-Smoke grün** (3/3, echter Dissens
claude→Click vs. codex/agy→argparse). Dev-Deps (pytest/ruff/black/isort) waren nicht installiert →
in `.pal_venv` nachgezogen. Vorbestehend (NICHT cli_consensus): 45 Gemini-Alias-Test-Fehler
(`flash→flash2.5`), per `git stash` verifiziert, als separater Task geflaggt.

## 2026-06-17 — ThinkHub-Doku-Gerüst eingeführt (Build 1)

pal in das ThinkHub-Doku-Regime integriert, als Vorbereitung für das `cli_consensus`-Vorhaben.
Angelegt: `DEVELOPMENT-WORKFLOW.md` (pal-angepasst — semantic-release/Conventional-Commits/
`code_quality_checks.sh` gewahrt, DB-/Multi-VM-Ballast des Musters weggelassen), `HISTORY.md`,
`TODO.md`, `CHANGES.md` (getrennt vom Upstream-`CHANGELOG.md`), `APP_VERSION.md` (Spiegel von
config.py), `BUILD_NUMBER.md`, `CONTRIBUTING.md`, `COMPLIANCE-TABLE.md` (Template, aktiv ab Phase 2),
`docs/architecture/` für ADRs.

**Nächstes:** ADR-001 (cli_consensus — Multi-Modell-Konsens über Abo-CLIs claude/codex/agy statt
bezahlter Provider-APIs; Architektur „Option 1.5" = Tool + wiederverwendbare CliBackend-Schicht),
dann Implementierung.

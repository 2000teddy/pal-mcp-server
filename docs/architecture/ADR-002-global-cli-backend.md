# ADR-002: Globaler Abo-CLI-Backend-Modus (`PAL_BACKEND`)

**Status:** Implemented
**Datum:** 2026-07-03
**Bezug:** revidiert die in [ADR-001](ADR-001-cli-consensus.md) verworfene „Option 2 — CLI-Provider".
Auftrag: `docs/cli_provider_plan.md`.

> Diese ADR ist zugleich die **Übergabe-Doku** für den Hub-Agenten (TH01): nach `git pull`
> zuerst lesen, dann die Folge-Schritte unten abarbeiten.

## Kontext

ADR-001 hat den Abo-CLI-Weg für den Konsens etabliert (`cli_consensus`), den generellen
CLI-*Provider* („alle Tools über Abo-CLIs") aber verworfen — mit zwei Begründungen:
sync/async-Deadlock-Risiko und Blast-Radius (ein CLI-Bruch träfe alle Tools).

Die Rahmenbedingungen haben sich geändert: **Subscription soll der Normalbetrieb sein**,
nicht die Ausnahme. Offene Per-Token-APIs sind explizit unerwünscht (Kostendeckelung);
sie sollen nur noch als Notfall-Rückfall existieren. Der in ADR-001 genannte
Revisionsauslöser ist damit erfüllt — die Zielgröße ist nicht mehr ~12 %, sondern ~100 %
der Tool-Aufrufe über Abos.

## Entscheidung

Ein **globaler Backend-Schalter** `PAL_BACKEND` in der `.env` mit zwei Modi:

| Modus | Verhalten |
|-------|-----------|
| `subscription` (**Default**, auch bei ungesetzter Variable) | Alle Tools laufen über den neuen `CLIModelProvider` (Abo-CLIs `claude`/`codex`/`agy`). Offene Per-Token-Provider (Gemini/OpenAI/Azure/XAI/DIAL/OpenRouter/Custom) werden **nicht registriert** — kein stiller Fallback auf offene Token-Abrechnung. **MiniMax bleibt registriert**: gedeckelte/prepaid API, faktisch subscription-artig. Ist keine der drei CLIs im PATH → **lauter Startfehler**. |
| `api` (**nur Notfall**) | Exakt das historische Voll-API-Verhalten; kein CLI-Provider. |

Kernstücke:

1. **`CLIModelProvider`** (`providers/cli_provider.py`, `ProviderType.CLI`): ein regulärer
   Provider hinter dem Standard-Interface. **Kein Tool wurde angefasst, kein Tool dupliziert** —
   die Tools sehen weiterhin `generate_content(...) -> ModelResponse`.
2. **Synchron statt async** (Auflösung des ADR-001-Deadlock-Arguments): Der Provider ruft die
   CLI **blockierend** via `subprocess.Popen/communicate` auf (`clink/cli_invoke.py`) — kein
   `asyncio`, kein neuer Event-Loop. Das blockiert den Event-Loop genau so lange wie die
   synchronen HTTP-Calls der API-Provider, also kein neues Verhalten.
3. **Blast-Radius ist jetzt gewollt**: „CLI kaputt → alle Tools kaputt" ist im
   Subscription-Modus akzeptiert, weil (a) laut & früh erkennbar (Startfehler, klare
   Fehlermeldungen) und (b) `PAL_BACKEND=api` als expliziter Rückfallschalter existiert.
4. **Alias-Spiegelung** (`conf/cli_models.json`, überschreibbar via `CLI_MODELS_CONFIG_PATH`):
   Der CLI-Katalog spiegelt sämtliche Aliasse der Gemini-/OpenAI-Kataloge
   (`flash`, `pro`, `gpt5`, `o3`, …), sodass **kein Modellwunsch im Subscription-Modus
   unauflösbar** ist. Ein Test erzwingt das dauerhaft
   (`tests/test_cli_provider.py::TestAliasResolution::test_all_api_catalogue_aliases_resolve`).
5. **`auto`-Modus**: `ProviderType.CLI` steht an erster Stelle der `PROVIDER_PRIORITY_ORDER`;
   `get_preferred_model` liefert `cli-claude-opus` (extended reasoning) bzw.
   `cli-claude-sonnet` (fast/balanced).
6. **Fehlersemantik**: Timeout/Parse-Fehler/leerer Output → Exception (wie API-Provider);
   Rate-Limits → `CliRateLimitError`, **nicht** retryt; transiente Fehler → 1 Retry.
   Kill bei Timeout trifft die ganze Prozessgruppe. Timestamp-Prefix-Cleaning und
   Rate-Limit-Heuristik werden aus `clink/consensus_backends.py` **importiert** (eine Quelle).
7. **`cli_consensus` bleibt unverändert** (eigener Partial-Failure-Vertrag); das klassische
   `consensus`-Tool folgt `PAL_BACKEND` und konsultiert im Subscription-Modus CLI-Backends.

## Modellkatalog (Default)

| Katalogname | CLI | Abo | bedient u. a. die Aliasse |
|---|---|---|---|
| `cli-claude-sonnet` | `claude --print --output-format json --model sonnet` | Claude Max | `sonnet`, `claude`, `flash*`, `mini`, `nano` |
| `cli-claude-opus` | `claude … --model opus` | Claude Max | `opus`, `claude-opus` |
| `cli-codex-gpt` | `codex exec --sandbox read-only --json` (CLI-Default-Modell) | ChatGPT | `gpt5*`, `o3*`, `o4-mini`, `codex*`, `chat-latest` |
| `cli-agy-gemini-pro` | `agy --model "Gemini 3.1 Pro (Low)" -p` | Google One | `pro`, `gemini*` |

## Tests

- `tests/test_cli_provider.py` — 47 Unit-Tests (Kommandobau, Parsing→`ModelResponse`,
  Alias-Vollabdeckung, Fehlerpfade, Bild-Abweisung, Retry-Semantik). Subprozess gemockt.
- `tests/test_pal_backend_switch.py` — 12 Schalter-Tests (Default=subscription, api-Notfall,
  MiniMax-Ausnahme, lauter Startfehler ohne CLIs, kein stiller API-Fallback).
- `tests/test_subscription_parity.py` — Paritätstests: alle 11 modellrufenden Tools
  (chat + 9 Workflow-Tools + consensus) laufen end-to-end im Subscription-Modus; alle drei
  `generate_content`-Callsites abgedeckt.
- Historische Suite läuft als **api-Modus-Regression** (conftest pinnt `PAL_BACKEND=api`).

## Konsequenzen

**Positiv:** ~100 % der Tool-Aufrufe kostengedeckelt über Abos; ein Schalter statt Tool-Matrix;
keine Tool-Duplikate; API-Pfad bleibt als geprüfter Notfallmodus erhalten.

**Negativ / Risiken:**
- CLI-Interface-Brüche treffen im Subscription-Modus alle Tools (bewusst akzeptiert, s. o.).
- CLIs ignorieren Feintuning (`temperature`, `thinking_mode`, `max_output_tokens`) — wird
  angenommen und ignoriert; Bild-Inputs werden klar abgewiesen (`supports_images=false`).
- Abo-Automatisierung bleibt ToS-Grauzone (wie ADR-001, bewusst akzeptiert).
- Ein blockierender CLI-Aufruf kann Minuten dauern (wie lange API-Calls) — Timeout 300 s,
  Prozessgruppen-Kill.

## Hub-Deploy (Folge-Schritte für den TH01-Agenten)

1. `git pull` (Author-once auf dem Mac → Hub zieht).
2. CLIs auf dem Hub installiert + per OAuth angemeldet: `claude`, `codex`, `agy`.
3. `.env` auf dem Hub: `PAL_BACKEND=subscription` explizit setzen (Default gilt auch ungesetzt);
   MiniMax-Key bleibt. Offene API-Keys können (Kostenregel ADR-001) geleert werden, müssen aber
   nicht — im Subscription-Modus werden sie ohnehin nicht registriert.
4. Dienst-/Bridge-Neustart (supergateway) → mcporter exponiert pal wieder im Mesh.
5. Live-Smoke (Integrationscheckliste): je ein Aufruf `chat` (claude), `chat` mit `model=gpt5`
   (codex), `chat` mit `model=pro` (agy), ein `thinkdeep`-Abschluss (Expert-Analyse), ein
   `consensus`-Lauf mit 2 Modellen, ein `cli_consensus`-Lauf (Regression).
6. Notfallprobe: `PAL_BACKEND=api` setzen, Neustart, ein `chat`-Aufruf → zurück auf
   `subscription` stellen.

## Referenzen

- Auftrag/Design: `docs/cli_provider_plan.md`
- Verwandte Module: `providers/cli_provider.py`, `providers/registries/cli.py`,
  `clink/cli_invoke.py`, `conf/cli_models.json`, `server.py` (`_configure_subscription_backend`),
  `providers/registry.py` (`PROVIDER_PRIORITY_ORDER`).

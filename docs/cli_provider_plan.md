# Entwicklungsprompt: Globaler CLI-/Subscription-Provider mit `.env`-Schalter

> **Status:** Entwurf zur Ausführung durch einen Agenten (Entwicklung auf dem Mac,
> anschließende Übergabe an TH01 — analog zum bestehenden `cli_consensus`).
> **Bezug:** erweitert / revidiert `docs/architecture/ADR-001-cli-consensus.md`.

Dies ist ein **eigenständiger, ausführbarer Auftrag**. Alles Nötige steht hier drin,
inkl. der bereits recherchierten Code-Anker. Trotzdem gilt: **vor jeder Änderung die
referenzierten Stellen selbst gegenlesen** — Zeilennummern können sich verschoben haben.

---

## 1. Ziel (das „Was")

Der PAL-MCP-Server soll **alle modell-aufrufenden Tools wahlweise über die lokalen
Abo-CLIs** (Claude Max / ChatGPT / Google One — `claude` / `codex` / `agy`) statt über
bezahlte Provider-APIs laufen lassen können. Umgeschaltet wird **global über einen
einzigen `.env`-Schalter**. Es gibt **keine** Tool-Duplikate und **keine** Pro-Tool-Matrix.

**Akzeptanzmaßstab (harte Messlatte):** Jedes Tool muss im Subscription-Modus
**funktional identisch** verhalten wie im API-Modus — gleiche Ein-/Ausgabe-Form,
gleiche Workflow-Schritte, gleiche Fehlersemantik. „Es soll genauso funktionieren, als
wenn es unter API-Token-Key läuft."

## 2. Nicht-Ziele (bewusst ausgeschlossen)

- **Keine** Duplizierung von Tools als `cli_chat`, `cli_codereview`, … (verworfen — 11
  Tools doppelt zu pflegen ist ein Wartungsalbtraum).
- **Keine** Pro-Tool-Umschaltmatrix. Entscheidung ist bewusst **entweder/oder** global
  (Subscription ist grundsätzlich günstiger; das ist der Sinn der Übung).
- **Kein** Anfassen der Tool-Logik. Die Tools bleiben unverändert; nur die
  Provider-Ebene ändert sich.
- `cli_consensus` bleibt als **eigenes** Tool bestehen (nicht abbauen). Es ist der
  Präzedenzfall, aus dem wir das Subprocess-Muster übernehmen.

## 3. Ist-Zustand (recherchiert — als Ausgangsbasis)

- **Nur `cli_consensus`** läuft heute automatisch über Abo-CLIs. Alle anderen
  modell-aufrufenden Tools gehen über `ModelProviderRegistry` → Provider-APIs.
- Betroffen (hängen an API-Keys, müssen im neuen Modus über CLI laufen, ~11 Stück):
  `chat`, `thinkdeep`, `consensus`, `codereview`, `precommit`, `debug`, `secaudit`,
  `analyze`, `refactor`, `testgen`, `docgen`.
- Kein Modellaufruf (irrelevant, nicht anfassen): `planner`, `tracer`, `challenge`,
  `apilookup`, `listmodels`, `version`. `clink` ruft schon CLIs; nicht umbauen.
- **Es gibt heute keinen globalen API-vs-Subscription-Schalter.** ADR-001 hat den
  „CLI-Provider für alle Tools"-Ansatz explizit **verworfen** — aus zwei Gründen:
  1. **Blast Radius:** CLI kaputt → alle Tools kaputt. → Bei einem globalen Schalter
     mit API-Rückfallmodus ist das **gewollt und akzeptabel**.
  2. **sync/async-Deadlock-Risiko.** → **Aufgelöst** in diesem Design (siehe §5).

### Relevante Code-Anker (vorab verifiziert)

| Was | Ort |
|-----|-----|
| Provider-Interface (`generate_content` ist **synchron**, liefert `ModelResponse`) | `providers/base.py:146` |
| Provider deklarieren `MODEL_CAPABILITIES` + `get_provider_type()` | `providers/base.py:39`, `:51` |
| `ModelResponse`-Felder: `content, usage, model_name, friendly_name, provider, metadata` | `providers/shared/model_response.py:12` |
| `ModelCapabilities`-Felder (provider, model_name, friendly_name, aliases, context_window, supports_*, temperature_constraint …) | `providers/shared/model_capabilities.py:14` |
| `ProviderType`-Enum (GOOGLE/OPENAI/…/MINIMAX) | `providers/shared/provider_type.py:8` |
| Registry: `PROVIDER_PRIORITY_ORDER`, `register_provider`, `get_provider`, `get_provider_for_model` | `providers/registry.py:38`, `:61`, `:74`, `:155` |
| **Provider-Registrierung beim Start** (Hook-Punkt für den Schalter) | `server.py:380` `configure_providers()`, Registrierungen `:511–549` |
| Funktionierendes Abo-CLI-Subprocess-Muster (async) + `default_backends()` (claude/codex/agy) | `clink/consensus_backends.py` |
| Synchrone CLI-Parser (`get_parser(name).parse(stdout, stderr)`) | `clink/parsers/` |
| MCP-Boundary Modell-Auflösung (Consensus ist ausgenommen) | `server.py:~800` |

## 4. Design (das „Wie")

### 4.1 Neuer Provider `CLIModelProvider`

- Neues Modul `providers/cli_provider.py` mit Klasse `CLIModelProvider(ModelProvider)`.
- Neuer Enum-Wert `ProviderType.CLI` in `providers/shared/provider_type.py` (Wert `"cli"`).
- Konstruktor kompatibel zu `register_provider`-Aufruf (`__init__(self, api_key, **kwargs)`);
  ein echter API-Key wird **nicht** benötigt (leerer String / Dummy).
- **`generate_content(...)` synchron implementieren** (siehe §5): baut das CLI-Kommando,
  ruft die CLI blockierend auf, parst stdout mit dem passenden `clink`-Parser, verpackt
  das Ergebnis in `ModelResponse`.
- `MODEL_CAPABILITIES` als Katalog CLI-gestützter Modelle **mit Aliassen, die die
  bestehenden PAL-Aliasse spiegeln**, damit `DEFAULT_MODEL=auto` und namentliche
  Modellwünsche der Tools ohne Änderung weiter funktionieren. Mindestens:

  | Kanonischer Name | Backend-CLI | CLI-Modellflag | Ziel-Aliasse (Beispiele) |
  |---|---|---|---|
  | `cli-claude-sonnet` | `claude` (`--print --output-format json`, stdin) | `--model sonnet` | `sonnet`, `claude`, `flash`* |
  | `cli-claude-opus` | `claude` | `--model opus` | `opus`, `pro`* |
  | `cli-codex-gpt` | `codex` (`exec --sandbox read-only --json`, stdin) | `-m` | `gpt5`, `codex`, `o3`* |
  | `cli-agy-gemini-pro` | `agy` (`-p`, arg-mode) | `--model "Gemini 3.1 Pro (Low)"` | `pro`, `gemini`* |

  \* Die konkrete Alias-Zuordnung ist beim Umsetzen **an den real existierenden
  Aliassen** der API-Provider auszurichten (in `providers/gemini.py`, `openai_provider`,
  `providers/anthropic*`/`minimax` etc. nachsehen), sodass jeder Alias, den ein Tool
  im `auto`-Betrieb wählen könnte, im Subscription-Modus einem CLI-Backend auflöst.
  Ziel: **keine unauflösbaren Modelle** im Subscription-Modus.

- `get_preferred_model(category, allowed_models)` sinnvoll implementieren, damit
  `auto`-Auflösung (`registry.get_preferred_fallback_model`, `providers/registry.py:386`)
  im Subscription-Modus ein vernünftiges CLI-Default liefert (Vorschlag:
  `cli-claude-sonnet` als Allrounder, `cli-claude-opus` für „extended reasoning"-Kategorie).

### 4.2 Das Subprocess-Backend wiederverwenden

- Das Kommando-/Parser-Wissen aus `clink/consensus_backends.py` (`CliBackend.build_command`,
  Modellflags, Parser-Namen `claude_json` / `codex_jsonl` / `agy_text`, Timestamp-Cleaning)
  **wiederverwenden**, nicht neu erfinden. Bevorzugt eine gemeinsame Hilfsfunktion
  extrahieren (z. B. `clink/cli_invoke.py` mit einer **synchronen** `run_cli_sync(backend, prompt) -> (content, metadata)`),
  die sowohl der neue Provider als auch — optional — `cli_consensus` nutzen könnten.
  **Wichtig:** `cli_consensus` dabei nicht funktional verändern; wenn Refactoring zu
  riskant, im Provider eine eigene synchrone Variante bauen und das async-Backend in Ruhe lassen.

### 4.3 Der globale Schalter

- **Env-Variable:** `PAL_BACKEND` mit Werten `subscription` (**Default**) und `api`.
  **Default ist `subscription`** — das ist der bewusst gewählte Normalbetrieb
  (Kostendeckelung, kein offenes Per-Token-Risiko). `api` ist **ausschließlich der
  Notfall-Rückfallschalter**, falls die Abo-CLIs einmal nicht mehr funktionieren.
  Ist die Variable ungesetzt, gilt `subscription`.
- **Hook:** in `configure_providers()` (`server.py:380`) auswerten:
  - `PAL_BACKEND=subscription` (Default):
    - `CLIModelProvider` registrieren und **an den Anfang** von `PROVIDER_PRIORITY_ORDER`
      setzen (bzw. Priority so anpassen, dass CLI zuerst greift).
    - Die offen abrechnenden Per-Token-API-Provider (GOOGLE/OPENAI/AZURE/XAI/DIAL/
      OPENROUTER/CUSTOM) **nicht** registrieren — kein stiller, offen abrechnender
      API-Fallback (Kostenregel aus ADR-001).
    - **MiniMax bleibt registriert** (`ProviderType.MINIMAX`): MiniMax ist eine
      **gedeckelte/prepaid** API und damit faktisch subscription-artig — kein offenes
      Per-Token-Kostenrisiko, deshalb im Subscription-Modus bewusst zugelassen. Priority
      **nach** dem CLI-Provider (CLI zuerst, MiniMax als günstige Ergänzung).
    - Wenn **keine** der CLIs (`claude`/`codex`/`agy`) via `shutil.which` auffindbar ist:
      klare, laute Fehlermeldung beim Start (nicht still auf offene APIs zurückfallen).
  - `PAL_BACKEND=api` (**nur Notfall**): stellt das **heutige Voll-API-Verhalten** wieder
    her — alle API-Provider registriert, `CLIModelProvider` nicht. Dient ausschließlich
    dem Rückfall, wenn der Subscription-Weg ausfällt.
- Der Schalter muss **testbar** sein, ohne echten Prozessstart (Provider-Registrierung
  von der CLI-Verfügbarkeit entkoppeln bzw. mockbar halten).

### 4.4 `.env` / `.env.example` dokumentieren

Block in `.env.example` (und in der echten `.env` auf dem Zielsystem) ergänzen, **mit
Erläuterung der Modi**:

```dotenv
# ─────────────────────────────────────────────────────────────
# PAL_BACKEND — globaler Backend-Schalter (Abo-CLI  vs.  offene API)
#
#   subscription  → NORMALBETRIEB (Default). Alle Tools laufen über die
#                   lokalen Abo-CLIs (Claude Max = `claude`,
#                   ChatGPT = `codex`, Google One = `agy`). Keine offenen
#                   Token-Kosten, KEIN stiller API-Fallback. CLIs müssen
#                   installiert & eingeloggt sein.
#                   Ausnahme: MiniMax bleibt aktiv — gedeckelte/prepaid
#                   API, faktisch subscription-artig (kein Token-Risiko).
#   api           → NOTFALL-Rückfall. Stellt das volle API-Verhalten wieder
#                   her (GEMINI/ANTHROPIC/… API-Keys nötig, offene Token-
#                   kosten). Nur nutzen, wenn der Abo-Weg ausfällt.
#
# Hinweis Konsens: `cli_consensus` läuft IMMER über Abo-CLIs (unabhängig
# von PAL_BACKEND). Das klassische `consensus`-Tool folgt PAL_BACKEND.
# ─────────────────────────────────────────────────────────────
PAL_BACKEND=subscription
```

## 5. Der sync/async-Knackpunkt (ADR-001-Auflösung — verbindlich)

ADR-001 hat den Provider-Ansatz u. a. wegen **Deadlock-Gefahr** verworfen: Der Server
läuft in einem asyncio-Event-Loop; `generate_content` wird **synchron** aus dem
Tool-Code aufgerufen. Würde man darin `asyncio.run(...)` auf das bestehende
async-`CliBackend` aufrufen, kracht es („cannot be called from a running event loop").

**Auflösung:** Der neue Provider ruft die CLI **blockierend mit `subprocess.run(...)`**
auf — *kein* `asyncio`, *kein* `asyncio.run`, *kein* neuer Loop. Konkret:

- `subprocess.run([...], input=prompt.encode(), stdout=PIPE, stderr=PIPE, timeout=…)`,
  Prozessgruppe/`start_new_session=True` zum sauberen Killen bei Timeout beibehalten
  (siehe `_terminate` in `consensus_backends.py`).
- stdout mit `get_parser(parser_name).parse(stdout, stderr)` (synchron) auswerten.
- Das blockiert den Event-Loop für die Dauer des CLI-Aufrufs — **genauso** wie die
  bestehenden API-Provider bei ihren synchronen Netz-Calls blockieren. Also kein
  neues Verhaltensrisiko gegenüber dem API-Modus.
- **Schritt 0 der Umsetzung:** verifizieren, wie/wo Tools `generate_content` aufrufen
  (Aufruf am MCP-Boundary, `server.py:~800`, und in den Tool-`execute`-Pfaden). Bestätigen,
  dass ein blockierender Subprocess dort vertretbar ist (ist er, da API-Provider ebenso
  blockieren). Falls überraschend doch in einem Kontext nötig, der nicht blockieren darf:
  `asyncio.to_thread` am Aufrufer — aber **nicht** `asyncio.run` im Provider.

## 6. Randfälle / Kompatibilität (alle bedenken)

- **`consensus` (klassisch):** löst seine mehreren Modelle über die Registry auf →
  greift im Subscription-Modus automatisch auf `CLIModelProvider`. Sicherstellen, dass
  die im consensus genannten Modelle (z. B. `for`/`against`-Stances mit `gpt5`/`pro`)
  auf CLI-Backends auflösen. `cli_consensus` bleibt unberührt daneben bestehen.
- **Vision/Images:** CLIs unterstützen keine Bild-Inputs → `supports_images=False` in den
  Capabilities; wenn ein Tool Bilder schickt, sauber (verständlich) abweisen, nicht crashen.
- **`temperature`, `thinking_mode`, `max_output_tokens`, top_p etc.:** Die Abo-CLIs
  akzeptieren solche Feineinstellungen i. d. R. nicht → Parameter **annehmen und
  ignorieren** (kein Fehler), damit die Tool-Aufrufe unverändert durchlaufen.
- **`count_tokens`:** Heuristik aus der Basisklasse (Zeichen/4) genügt.
- **Restriction-Policy / `list_models`:** Der neue Provider muss `list_models` sinnvoll
  liefern (für `listmodels`-Tool und `get_available_models`), damit CLI-Modelle sichtbar sind.
- **Rate-Limit/Timeout/Empty-Output:** Semantik aus `consensus_backends.py` übernehmen
  (Rate-Limit-Hints, leerer Content = Fehler), aber im Provider-Kontext als
  **Exception** hochreichen (Tools erwarten bei Fehlern eine Exception, nicht ein
  degradiertes Ergebnis — anders als der partial-failure-Vertrag von `cli_consensus`).
- **Timestamp-Prefix-Cleaning** (`_TIMESTAMP_PREFIX` in `consensus_backends.py`)
  übernehmen — ein globales CLAUDE.md kann `claude --print` eine `**HH:MM**`-Zeile
  voranstellen, die raus muss.

## 7. Tests (Pflicht — „sauber durchgetestet")

Alles unter `tests/` (Unit, gemockt) + Simulator, mit `./code_quality_checks.sh` 100 % grün.

1. **Unit — `CLIModelProvider`** (`tests/test_cli_provider.py`), `subprocess.run` gemockt:
   - Kommando-Bau je Backend (claude/codex/agy), Modellflag-Position (agy: Modell vor `-p`).
   - stdout-Parsing → `ModelResponse` (content, provider=`ProviderType.CLI`, metadata).
   - Alias-Auflösung: jeder gespiegelte Alias (`sonnet`,`opus`,`gpt5`,`pro`,…) → korrektes Backend.
   - Fehlerpfade: CLI nicht in PATH, Timeout, non-zero exit, leerer Output, Rate-Limit →
     jeweils saubere Exception.
   - `validate_model_name`, `get_capabilities`, `list_models`, Restriction-Integration.
2. **Unit — Schalter** (`tests/test_pal_backend_switch.py`):
   - `PAL_BACKEND=subscription` **und ungesetzt** (Default) → `configure_providers()`
     registriert `ProviderType.CLI`, Priority so, dass `get_provider_for_model("sonnet")`
     den CLI-Provider liefert; MiniMax bleibt registriert; die offenen API-Provider nicht.
   - `PAL_BACKEND=api` (Notfall) → CLI-Provider **nicht** registriert, volles API-Verhalten.
   - Keine CLI auffindbar + subscription → lauter Startfehler (gemockt via `shutil.which`).
3. **Parität pro Tool** (der eigentliche Akzeptanztest): Für **jedes** der 11 Tools
   (`chat, thinkdeep, consensus, codereview, precommit, debug, secaudit, analyze,
   refactor, testgen, docgen`) einen Test, der es im Subscription-Modus mit **gemocktem
   CLI-Backend** ausführt und prüft, dass Antwortform/Workflow-Schritte identisch zum
   API-Modus sind. Bestehende Tool-Tests als Vorlage; wo möglich denselben Test
   parametrisiert über beide Backends laufen lassen.
4. **Simulator** (`communication_simulator_test.py`): sicherstellen, dass `--quick` auch
   unter `PAL_BACKEND=subscription` grün ist (mit fake/echter CLI). Ggf. dedizierten
   Sim-Test `subscription_backend_validation` ergänzen.
5. **Live/Integration (nur auf Maschine mit eingeloggten CLIs, z. B. TH01):** jedes Tool
   **einmal** real gegen `claude`/`codex`/`agy` durchlaufen und Sichtprüfung auf Parität.

Vorgabe aus `CLAUDE.md`: `source .pal_venv/bin/activate` → `./code_quality_checks.sh`
(ruff/black/isort + Unit-Tests) muss **100 %** bestehen; danach
`python communication_simulator_test.py --quick`.

## 8. Doku & ADR

- **`docs/architecture/ADR-002-global-cli-backend.md`** neu: dokumentiert, dass die in
  ADR-001 verworfene „Option 2" jetzt **bewusst umgesetzt** wird, **weil** (a) ein
  einziger globaler Schalter mit explizitem API-Rückfallmodus den Blast-Radius zu einer
  gewollten Eigenschaft macht und (b) die Deadlock-Gefahr durch **blockierendes
  `subprocess.run` statt `asyncio`** entfällt. ADR-001 oben mit Verweis „superseded in
  part by ADR-002" markieren.
- `.env.example` (siehe §4.4), `docs/configuration.md`, `docs/adding_providers.md` und
  `CLAUDE.md`/README um den `PAL_BACKEND`-Schalter ergänzen.

## 9. Übergabe an TH01 (wie beim `cli_consensus`)

1. Entwicklung + alle Tests **hier auf dem Mac**. Der Default `PAL_BACKEND=subscription`
   gilt auch lokal — die CLIs `claude`/`codex`/`agy` sind hier vorhanden (`cli_consensus`
   läuft bereits lokal). Für Regressionsläufe gegen die APIs temporär `PAL_BACKEND=api` setzen.
2. Sauberer Branch, fokussierte Commits (Provider / Schalter / Tests / Doku getrennt),
   Commit-Messages im Projektstil.
3. Übergabe an TH01 nach etabliertem Muster. Auf TH01:
   - `claude`, `codex`, `agy` müssen **installiert und eingeloggt** sein (Abo-Auth).
   - Dort `PAL_BACKEND=subscription` in der `.env` setzen.
   - Live-Integrationstests (§7.5) laufen lassen.

## 10. Guardrails

- API-Provider-Code **nicht** löschen — nur bedingt (nicht-)registrieren. Rückschaltbar bleiben.
- Tool-Logik **nicht** anfassen.
- Secrets (API-Keys, Tokens) niemals im Klartext loggen/ausgeben.
- Bei Unsicherheit über Alias-Mapping oder `auto`-Default: erst die realen API-Provider-
  Aliasse gegenlesen, dann spiegeln — **kein** Modell darf im Subscription-Modus
  unauflösbar sein.
- Vor Abschluss: `./code_quality_checks.sh` grün **und** `--quick`-Simulator grün.

## 11. Definition of Done

- [ ] `ProviderType.CLI` + `CLIModelProvider` (synchron, `subprocess.run`) implementiert.
- [ ] `PAL_BACKEND`-Schalter in `configure_providers()`, **Default `subscription`**;
      subscription registriert CLI (+ MiniMax), keine offenen API-Provider; `api` = Notfall,
      volles API-Verhalten; fehlende CLI → lauter Startfehler.
- [ ] Alias-Katalog so, dass `auto` + alle tool-gewählten Modelle im Subscription-Modus auflösen.
- [ ] Alle 11 Tools verhalten sich im Subscription-Modus **funktional identisch** zum API-Modus.
- [ ] `cli_consensus` unverändert funktionsfähig daneben.
- [ ] Unit- + Schalter- + Paritäts-Tests grün; `./code_quality_checks.sh` 100 %; `--quick` grün.
- [ ] `.env.example`, ADR-002, Doku aktualisiert.
- [ ] Bereit zur Übergabe an TH01.

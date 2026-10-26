# TODO — PAL MCP Server (ThinkHub-Fork)

> **Status-Kurzzeile (Stand 2026-10-26, KW44):** Build 2 fertig; CO-01 core-gegated.
> **Scope:** Dieses File ist das **Bauplan-Backlog** der PALDEV-Lane, **nicht** die Freigaben-Liste.
> Die vollständige Christian-Gate-Liste (mit Fristen und Belegen) steht in
> `~/thinkhub-administrator/FREIGABEN-OFFEN-CHRISTIAN.md`; hier stehen nur die bauplan-relevanten Punkte.
> **Im Klartext:** `cli_consensus` + `PAL_BACKEND`-Subscription-Backend (ADR-001/ADR-002, #1–#9) sind
> gebaut, getestet und gemergt. Die MD-Pflege steht bis auf **ein Repo-Admin-Follow-up**: das CI-Gate
> aus #14 liegt auf `main` und blockiert seit dem 21.07. (`WARN_UNTIL`), ist aber noch **nicht** als
> *required status check* eingetragen — `main` trägt am 26.10. gar keine Branch-Protection
> (`gh api …/branches/main/protection` → 404). Der verbleibende Hauptpunkt ist **keine PAL-Arbeit**:
> CO-01 (pal-Rebuild) hängt am Core-/Hub-Fenster. In dieser Lane offen sind damit fünf Punkte:
> das Branch-Protection-Follow-up oben, plus die vier Einträge unter „🟡 Offen" (zwei
> Kleinigkeiten und die beiden Dependency-Punkte aus der mcp-Drift, Stand 26.10. 15:2x UTC).
>
> **Rolle:** Backlog **und** Fortschritt — die einzige „was kommt / was ist erledigt"-Quelle.
> Erledigtes wird abgehakt (nicht gelöscht, solange es Kontext trägt), Neues kommt rein.
> Priorität: 🔴 kritisch · 🟠 wichtig · 🟡 normal · 🟢 nice · 💡 Idee.
> Der Reconcile-Wächter (Ebene 2) meldet, wenn dieser Stand > 5 PRs hinter dem Merge-Stand liegt.

## 🟠 In Arbeit

- [x] **MD-Pflege / Durchsetzungssystem** (Christians Beschluss 2026-07-07) — Ebene-1-Kern erledigt:
  - [x] Altlasten: CHANGES.md + HISTORY.md bis #11 nachgezogen, COMPLIANCE-TABLE rückwirkend befüllt
  - [x] Phasen-Schalter gestrichen (COMPLIANCE immer Pflicht)
  - [x] Rollen der Doku-Dateien in `CONTRIBUTING.md` festgeschrieben
  - [x] Ebene 1: warnendes CI-Gate gelandet (#14, `.github/workflows/md-compliance.yml`); Warn→blockierend
    flippt automatisch am `WARN_UNTIL=2026-07-21` (kein zweiter Commit). **Repo-Admin-Follow-up offen:**
    Check nach dem Warn-Fenster in Branch-Protection als *required status check* eintragen.

## ✅ cli_consensus + Subscription-Backend (Build 2 → #1–#9)

Multi-Modell-Konsens über Abo-CLIs (claude/codex/agy) gebaut, 21 Unit-Tests grün, per Dogfooding
selbst-reviewt + gehärtet. Danach der globale `PAL_BACKEND`-Schalter (ADR-002).
Details: `docs/architecture/ADR-001-cli-consensus.md`, `ADR-002-global-cli-backend.md`, `docs/tools/cli_consensus.md`.

- [x] `git pull` auf TH01 → Bridge-Neustart → Smoke (Deploy-Report 2026-06-25)
- [x] CLIs auf dem Hub (Linux) per OAuth anmelden (claude/codex/agy) — live verifiziert (2.1.202 / 0.142.5 / 1.0.16)
- [x] `agy` als vollwertiger clink-Client (AgyAgent, prompt-as-arg) — #4
- [x] `CLAUDE.md` um ThinkHub-Lese-Reihenfolge ergänzt — #8
- [x] `docs/tools/cli_consensus.md` (Nutzer-Doku) — #9
- [x] COMPLIANCE-TABLE aktiviert + CI-Gate angestoßen — diese MD-Pflege (Schalter gestrichen; CI = Folge-PR)

## 🟡 Offen

- [ ] `.env`-Backups auf dem Mac löschen (`.env.bak-openai-…`, `.env.old`) — vom Classifier blockiert, Christians Wort
- [ ] Optional: `AGY.md` (Antigravity-CLI-Hinweise) statt/neben `GEMINI.md`
- [x] 🔴 **Dependency-Drift: `mcp` nach oben begrenzen.** `requirements.txt:1` pinnt `mcp>=1.0.0`
  ohne Obergrenze; CI installiert inzwischen mcp **2.3.0**, wo die lowlevel-Dekoratoren entfallen
  sind → `AttributeError` an `server.py:731` beim Modul-Import, 9 Test-Dateien scheitern bei der
  Collection. Seit dem 15.07. unbemerkt, weil kein CI-Lauf stattfand. **Sofortmaßnahme:** `mcp<2`
  als eigener `fix`-PR mit CI-Nachweis. **Danach getrennt zu entscheiden:** Migration auf die
  mcp-2.x-API (ADR-Frage — `server.py` nutzt die Dekoratoren an mehreren Stellen). **Gleiche
  Drift-Fläche, noch ungeprüft:** `requirements.txt:2-4` und **alle** Zeilen in
  `requirements-dev.txt` haben ebenfalls keine Obergrenze. Belege:
  `changes/2026-10-26_todo-kw44-status-kopfzeile.md` §CI-Stand, PR #19.
  **Sofortmaßnahme erledigt (26.10., PR #20 `fix/mcp-pin-upper-bound`):** `requirements.txt:1`
  **und** `pyproject.toml:7` stehen auf `mcp>=1.0.0,<2`. Frische venv aus
  `requirements.txt`+`requirements-dev.txt` löst **mcp 1.30.0** auf, `list_tools` vorhanden,
  **971 passed, 0 failed**, keine Collection-Errors; CI 7/7 grün. Beleg:
  `changes/2026-10-26_mcp-pin-upper-bound.md`. **Nicht mit erledigt** sind die mcp-2.x-Migration
  (ADR-Frage) und die restliche Drift-Fläche; beide stehen **zusätzlich als eigene offene Punkte**
  unten (der Text hier bleibt wörtlich stehen, die Punkte sind kopiert, nicht entfernt), damit das
  Häkchen sie nicht mit zudeckt.

- [ ] 🟡 **Dependency-Drift, Restfläche — noch ungeprüft.** Ohne Obergrenze sind **alle übrigen**
  Laufzeit-Deklarationen: `requirements.txt:2-6` (`google-genai`, `openai`, `pydantic`,
  `python-dotenv`, `importlib-resources`) und spiegelbildlich `pyproject.toml:8-12` — plus **alle
  acht** Zeilen in `requirements-dev.txt`. (Korrektur 26.10.: der ursprüngliche 🔴-Punkt nannte nur
  `requirements.txt:2-4` und die `pyproject.toml`-Seite gar nicht; nachgezählt am Dateistand.)
  Mit PR #20 wurde nur `mcp` begrenzt — die einzige Zeile, die real gebrochen ist; der Rest blieb
  bewusst außerhalb des Fix-Scopes, weil jede Obergrenze ihren eigenen Verträglichkeits-Nachweis
  braucht. **Zu entscheiden:** ob und wie gepinnt wird (je Zeile eine frische venv + Testlauf).
  Gleiche Mechanik wie bei `mcp`: offene Versionsbereiche plus ein CI, das nur auf `pull_request`
  läuft, bleiben unbemerkt bis zum nächsten PR.

- [ ] 🟡 **Migration auf die mcp-2.x-API (ADR-Frage).** `server.py` nutzt die in 2.x entfallenen
  lowlevel-Dekoratoren an vier Stellen: `server.py:731` (`@server.list_tools()`), `:793`
  (`@server.call_tool()`), `:1392` (`@server.list_prompts()`), `:1442` (`@server.get_prompt()`).
  **Ersatz in 2.3.0, am installierten Paket nachgesehen** (frische venv mit `mcp==2.3.0`,
  `inspect.signature`): die Handler werden dem Konstruktor übergeben — `Server(name, …,
  on_list_tools=…, on_call_tool=…, on_list_prompts=…, on_get_prompt=…)` — und für eigene Methoden
  gibt es `add_request_handler(method, params_type, handler)` / `add_notification_handler`. Die
  Handler-Signatur ändert sich mit (`ServerRequestContext` + typisierte `*Result`-Objekte statt
  freier Rückgaben), `Server.run()` nimmt weiterhin `InitializationOptions`. `middleware` ist in
  2.x **nicht** der Dekorator-Ersatz, sondern eine eigene Schicht (`ServerMiddleware`,
  `mcp/server/runner.py`) — frühere Notiz hier war unpräzise. Also Umbau, keine Umbenennung:
  gehört in ein ADR, nicht in einen `fix`-PR. Der Pin `mcp<2` hält das Fenster offen, löst es
  nicht auf.

## ⏸️ Blockiert (extern)

- [ ] CO-01 pal-Rebuild auf TH01 — ThinkLocal-Zwei-Peer-Proof ist **erbracht** (TL-07 grün, 15.07.,
  `~/hermes/reports/2026-07-15_0918_TL07-zwei-peer-proof-ERBRACHT.md`); Gate-Revalidierung am HEAD `3fdb27d`
  grün (`~/hermes/reports/2026-07-15_0934_CO-01-pal-gate-revalidation.md`). **Blocker jetzt nicht mehr TL-07,
  sondern nur noch:** (a) **Core-/Hub-Mandat + Nacht-Fenster** — Rebuild-Trigger (`docker compose … thinkhub-pal`
  unter `/opt/thinkhub`) = TABU für Admin-/PAL-Lane, Core stößt ihn an. Blocker (b) **Runner-Vertrag ADR-003**
  ist **geschlossen** — die gemergte **Core-`ADR-003` §8 (Core PR #52)** verankert den Vertrag durable
  (gepinnt via `tests/unit/test_adr003_contract_doc.py`). PAL-seitig als Referenz gespiegelt:
  `docs/architecture/ADR-003-host-cli-runner.md`. Nur Belege (nicht normativ): Core-Handoff
  `~/hermes/reports/2026-07-15_1115_ADR-003-runner-contract-handoff.md`, Bridge-Karte
  `~/hermes/reports/2026-07-15_1049_CO-01-bridge-runner-verifikation.md`, Handoff-Prep
  `~/hermes/reports/2026-07-07-1832-pal-handoff-prep.md`.

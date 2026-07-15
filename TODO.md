# TODO — PAL MCP Server (ThinkHub-Fork)

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

## ⏸️ Blockiert (extern)

- [ ] CO-01 pal-Rebuild auf TH01 — ThinkLocal-Zwei-Peer-Proof ist **erbracht** (TL-07 grün, 15.07.,
  `~/hermes/reports/2026-07-15_0918_TL07-zwei-peer-proof-ERBRACHT.md`); Gate-Revalidierung am HEAD `3fdb27d`
  grün (`~/hermes/reports/2026-07-15_0934_CO-01-pal-gate-revalidation.md`). **Blocker jetzt nicht mehr TL-07,
  sondern nur noch:** (a) **Core-/Hub-Mandat + Nacht-Fenster** — Rebuild-Trigger (`docker compose … thinkhub-pal`
  unter `/opt/thinkhub`) = TABU für Admin-/PAL-Lane, Core stößt ihn an. Blocker (b) **Runner-Vertrag ADR-003**
  ist **geschlossen**: Core-Handoff `~/hermes/reports/2026-07-15_1115_ADR-003-runner-contract-handoff.md` +
  PAL-Repo-Referenzspiegel `docs/architecture/ADR-003-host-cli-runner.md` (mit CO-01-Rebuild-Konformitäts-Checkliste).
  Bridge-Pfad live grün: `~/hermes/reports/2026-07-15_1049_CO-01-bridge-runner-verifikation.md`
  (Handoff-Prep: `~/hermes/reports/2026-07-07-1832-pal-handoff-prep.md`).

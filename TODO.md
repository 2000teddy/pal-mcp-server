# TODO — PAL MCP Server (ThinkHub-Fork)

> **Rolle:** Backlog **und** Fortschritt — die einzige „was kommt / was ist erledigt"-Quelle.
> Erledigtes wird abgehakt (nicht gelöscht, solange es Kontext trägt), Neues kommt rein.
> Priorität: 🔴 kritisch · 🟠 wichtig · 🟡 normal · 🟢 nice · 💡 Idee.
> Der Reconcile-Wächter (Ebene 2) meldet, wenn dieser Stand > 5 PRs hinter dem Merge-Stand liegt.

## 🟠 In Arbeit

- [ ] **MD-Pflege / Durchsetzungssystem** (Christians Beschluss 2026-07-07):
  - [x] Altlasten: CHANGES.md + HISTORY.md bis #11 nachgezogen, COMPLIANCE-TABLE rückwirkend befüllt
  - [x] Phasen-Schalter gestrichen (COMPLIANCE immer Pflicht)
  - [x] Rollen der Doku-Dateien in `CONTRIBUTING.md` festgeschrieben
  - [ ] Ebene 1: warnendes CI-Gate (`changes/`-Eintrag + COMPLIANCE-Zeile je PR), 2 Wochen warnend → blockierend *(Folge-PR)*

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

- [ ] CO-01 pal-Rebuild auf TH01 — wartet auf ThinkLocal Zwei-Peer-Proof (Re-Pair); Handoff-Prep liegt vor
  (`~/hermes/reports/2026-07-07-1832-pal-handoff-prep.md`). Rebuild-Trigger = Hub-/Core-Mandat (TABU für Admin-Lane).

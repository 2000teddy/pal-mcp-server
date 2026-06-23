# TODO — PAL MCP Server (ThinkHub-Fork)

> Einzige Quelle für „was kommt". Priorität: 🔴 kritisch · 🟠 wichtig · 🟡 normal · 🟢 nice · 💡 Idee
> Erledigtes raus, Neues rein.

## ✅ cli_consensus — gebaut + selbst-reviewt (Build 2, 2026-06-17)

Multi-Modell-Konsens über Abo-CLIs (claude/codex/agy) implementiert, 21 Unit-Tests grün,
per Dogfooding selbst-reviewt + gehärtet (HIGH-Findings gefixt), ruff/black/isort grün.
Details: `docs/architecture/ADR-001-cli-consensus.md`, `docs/tools/cli_consensus.md`.

**Offen — Hub-Deploy (TH-Agent / Christian):**
- [ ] `git pull` auf TH01 → `.env` der API-Provider leeren (Kostenregel) → Bridge-Neustart → Smoke
- [ ] CLIs auf dem Hub (Linux) per OAuth anmelden (claude/codex/agy) — headless-Auth verifizieren
- [ ] `.env`-Backups auf dem Mac löschen (`.env.bak-openai-…`, `.env.old`) — vom Classifier blockiert, dein Wort
- [x] `agy` als vollwertiger clink-Client (AgyAgent mit prompt-as-arg) fürs `clink`-Tool — erledigt
      (`clink/agents/agy.py`, registriert in `clink/agents/__init__.py` + `clink/constants.py`,
      `conf/cli_clients/agy.json`; live über echtes agy verifiziert)

## 🟡 Doku-Feinschliff
- [ ] `CLAUDE.md` um die ThinkHub-Lese-Reihenfolge (§7) ergänzen — Verweis auf `DEVELOPMENT-WORKFLOW.md`
- [ ] `docs/tools/cli_consensus.md` (Nutzer-Doku) nach dem Bau

## 💡 Später / Phase 2
- [ ] COMPLIANCE-TABLE.md aktivieren, CI-Gate
- [ ] ggf. `AGY.md` (Antigravity-CLI-Hinweise) statt `GEMINI.md`

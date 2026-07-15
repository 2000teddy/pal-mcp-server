# 2026-07-15 — ADR-003 PAL-Repo-Referenzspiegel + CO-01-Rebuild-Konformität

Repo-naher Vorbau für den CO-01-Rebuild von `thinkhub-pal`. Der Rebuild selbst (`docker compose …`
unter `/opt/thinkhub`) bleibt Core-/Nacht-Fenster-Mandat (TABU); diese Änderung liefert die PAL-seitige
autoritative Referenz, gegen die die neu gebaute Image-/`clink`-Version geprüft wird.

## Was
- **Neu `docs/architecture/ADR-003-host-cli-runner.md`:** Referenz-Spiegel (kein Fork) auf den Core-Runner-Vertrag
  (Quelle: Core-`ADR-003` + Handoff `~/hermes/reports/2026-07-15_1115_ADR-003-runner-contract-handoff.md`).
  Enthält Draht-Vertrag (§2), Socket-Konvention (§3), Ordering-Invariante (§5) und eine
  **CO-01-Rebuild-Konformitäts-Checkliste** (C1–C5) mit Ist-Stand am HEAD `f5173d5`.
- **`docs/architecture/README.md`:** ADR-Index nachgezogen (001/002 auf `Implemented`, 003 als `Reference`).
- **`TODO.md`:** CO-01-Blocker (b) „Runner-Vertrag ADR-003" als **geschlossen** markiert; verbleibt nur (a)
  Core-/Nacht-Fenster-Trigger.

## Warum jetzt
`grep ADR-003` im PAL-Repo war = 0 Treffer; der Vertrag `server.py`/`clink` → Shim → AF_UNIX-Runner war
PAL-seitig nirgends referenzierbar (Handoff §7.2). Ohne Spiegel baut der Rebuild gegen einen nur im
Core-Baum sichtbaren Vertrag — Drift-Risiko bei Socket-Env, Framing, Whitelist, Timeout, Exit-Codes.

## Konformitäts-Befund (repo-seitig belegt, HEAD `f5173d5`)
- C1 CLI-Aufruf (basename+argv+stdin): konform (`clink/cli_invoke.py` `Popen(stdin=PIPE)`).
- C3 Timeout: PAL-Default = 300 s (`consensus_backends.DEFAULT_TIMEOUT_SECONDS`) == Runner-`DEFAULT_TIMEOUT`.
  **Drift-Warnung C3a:** per-CLI-`timeout`-Override >300 s in `conf/cli_models.json` würde der Runner bei
  300 s kappen (exit 124); `clink/constants.py` trägt separat 1800 — nicht der von `cli_invoke` genutzte Wert.
- C4 Backend: `.env PAL_BACKEND=subscription`; Empfehlung: beim Rebuild explizit setzen/bestätigen.
- C5 Healthz: `Dockerfile HEALTHCHECK`; Container live `curl /healthz` → `ok`.

## Validierung
Reine MD-Änderung (docs/architecture + TODO), **kein** Python/Dockerfile/CI → kein Test-/Build-Delta.
`/opt/thinkhub` nur read-only referenziert (kein Write, kein Rebuild). `git diff --check` sauber.

## Review-Nachtrag (codex CHANGES-NEEDED, 2026-07-15)
Quellen-Hierarchie geschärft: **einzige normative Quelle = gemergte Core-`ADR-003` §8 (Contract) via Core PR #52**,
gepinnt durch `tests/unit/test_adr003_contract_doc.py`. Handoff- und Bridge-Reports sind nur noch
historischer/Live-Beleg, nicht autoritativ. Stale Zukunfts-Formulierung in §6 („durable Verankerung ist ein
Core-Repo-PR / steht aus") entfernt — die Verankerung ist bereits gelandet.

## Status
Kein Selbst-Merge, kein PR ohne echten Review (claude/codex/agy, nie MiniMax/pal:chat).
Auf Feature-Branch `docs/adr-003-host-cli-runner-20260715`, wartet auf Review-Freigabe.

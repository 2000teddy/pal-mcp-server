# 2026-07-07 — ELv2-Sprachregel: „open-source" → „source-available" (Follow-up zu PR #10)

Post-Merge-Review von PR #10 fand verbliebene „open-source"-Formulierungen, die
der approved ELv2-Sprachregel widersprechen (ausdrücklich **nicht** „Open Source").

- **SECURITY.md Z. 12:** „PAL MCP is an **open-source** … server" → „**source-available**".
- **SECURITY.md Z. 47:** „This is an **open-source** project" → „**source-available** project".
- **DEVELOPMENT-WORKFLOW.md Z. 15:** „pal ist ein reifes **Open-Source-Repo**" →
  „reifes **source-available** Repo (ELv2)" — identischer Defekt, vom repo-weiten
  Sweep mitgefunden; hier gleich mitbehoben statt in einer weiteren Runde.

**Lektion (aus PR #10):** Der Lizenz-Sweep muss die **Sprachregel** als Zielgröße
nehmen — also repo-weit auch „open-source"/„open source" prüfen, nicht nur den
String „Apache". Sweep jetzt sauber (nur die gewollte OSI-Abgrenzung in den
LICENSE/README/changes-Texten bleibt).

Validierung: reine Prosa-/Doku-Änderung, kein Python, kein Dockerfile → kein
Test-/Build-Delta.

---

**Kein Selbst-Merge.** Merge erst nach grüner, unabhängiger Review via
claude/codex/agy (nie MiniMax/pal:chat).

# 2026-07-07 — ELv2-Lizenzumstellung (Gate 4 erteilt)

Schließt die letzte ELv2-Lücke, konsistent zu den anderen vier Repos.

- **LICENSE:** Apache 2.0 → Elastic License 2.0 (ELv2), source-available.
  Kanonischer ELv2-Text, byte-identisch zu agentdeck/thinkhub-core.
- **README:** Apache-Formulierung → ELv2-Sprachregel („source-available, frei
  für eigene Nutzung", ausdrücklich **nicht** „Open Source").
- **Copyright-Zeile:** Statt einer bespoke Copyright-Zeile im LICENSE-Body (die
  von den vier Referenz-Repos abweichen würde) wird die Attribution im **NOTICE**
  geführt. Das erfüllt zugleich die Apache-2.0-Pflicht (s. u.). Der exakte
  juristische Copyright-Inhaber-String bleibt wie bei den Geschwister-Repos ein
  Pre-Merge-Offenpunkt (aktuell „Christian Ullmann").

## Fachlicher Sonderfall ggü. den anderen vier Repos ⚠️

pal ist — anders als agentdeck/hermes/… (Eigencode) — ein **Derivat von
Fremdcode unter Apache 2.0**: ursprünglich „Gemini MCP Server" → „Zen MCP" →
„PAL MCP", `Copyright 2025 Beehive Innovations` (im bisherigen LICENSE-Appendix).
Apache-2.0 erlaubt die Weiterlizenzierung des kombinierten/abgeleiteten Werks
unter anderen Bedingungen (hier ELv2), verlangt aber nach §4 die Erhaltung der
Ursprungs-Attribution. Deshalb hier **zusätzlich** zu den Standard-Schritten:

- **NOTICE** angelegt: kreditiert Beehive Innovations (Apache-2.0), nennt die
  Namens-/Feature-Änderungen (§4(b)) und verweist auf die erhaltene Lizenzkopie.
- **LICENSE-APACHE-2.0** angelegt: der bisherige Apache-2.0-Text bleibt
  verbatim erhalten (§4(a) — Empfänger erhalten weiterhin eine Kopie der Lizenz,
  unter der die Ursprungs-Anteile stehen).

Kein „echter fachlicher Grund", pal **nicht** heute zu flippen — der Flip ist
Apache-2.0-konform, solange die Attribution (NOTICE + LICENSE-APACHE-2.0)
erhalten bleibt. Genau das ist umgesetzt.

## GPL/AGPL-Dependency-Scan

- **Runtime-Deps** (`requirements.txt`): `mcp` (MIT), `google-genai` (Apache-2.0),
  `openai` (Apache-2.0), `pydantic` (MIT), `python-dotenv` (BSD-3) — alle permissiv.
- **Kein GPL, kein AGPL** im Runtime-Baum.
- Einziger Copyleft-Treffer: `python-gitlab` (**LGPLv3**), rein transitiv über das
  **dev-/Release-Tool** `python-semantic-release` (`requirements-dev.txt`) — nicht
  ins Produkt gelinkt/ausgeliefert. ELv2-verträglich.

## NOTICE

**Ja** — nötig, weil pal Apache-2.0-Fremdcode (Beehive Innovations) derivativ
nutzt; Apache-2.0 §4 verlangt Attributionserhalt. Bei reinem Eigencode (wie den
anderen vier Repos) wäre kein NOTICE nötig.

---

**Kein Selbst-Merge.** Merge erst nach grüner, unabhängiger Review via
claude/codex/agy (nie MiniMax/pal:chat).

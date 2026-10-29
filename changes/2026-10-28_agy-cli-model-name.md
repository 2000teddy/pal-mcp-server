# fix(agy): CLI-Modellname auf `Gemini 4 Argon (Low)` angleichen

**Datum:** 2026-10-28
**Autor:** agy (Antigravity CLI / `Gemini 4 Argon`) im Auftrag des TH01-Watchdogs
**Trailer:** `Co-Authored-By: Gemini 4 Argon <noreply@google.com>`

## Problem

Der PAL-CLI-Backend `cli-agy-gemini-pro` war **tot**. Ursache: das in der CLI
hartcodierte Modell-Flag `Gemini 3.1 Pro (Low)` existiert in der agy-CLI
(Antigravity CLI 1.4.9) **nicht mehr** — der Name wurde vom Anbieter umbenannt.

Live-Beleg (vor dem Fix):

```
$ mcporter call pal chat model="cli-agy-gemini-pro" prompt="..." \
    working_directory_absolute_path=/home/chris/pal-mcp-server
error: model Gemini 3.1 Pro (Low) is not recognized as a known model or custom model in settings
```

Die agy-CLI kennt aktuell nur noch: `Gemini 4 Argon (Low/Medium/High)`,
`Gemini 3.8 Flash (…)`, `Claude Opus 5.5 (…)`, `Claude Sonnet 5.5 (…)`,
`GPT-OSS 120B (Medium)`.

**Zwei Hardcodings** auf den toten Namen:
- `conf/cli_models.json` → `cli_model`
- `clink/consensus_backends.py` → `model=`

plus eine Test-Assertion in `tests/test_cli_provider.py`.

## Änderung

Exakt **3 Ein-Zeilen-Änderungen**, keine Logikänderung:

| Datei | Vorher | Nachher |
|---|---|---|
| `conf/cli_models.json` | `Gemini 3.1 Pro (Low)` | `Gemini 4 Argon (Low)` |
| `clink/consensus_backends.py` | `Gemini 3.1 Pro (Low)` | `Gemini 4 Argon (Low)` |
| `tests/test_cli_provider.py` | `Gemini 3.1 Pro (Low)` | `Gemini 4 Argon (Low)` |

## Belege

**Unit-Gate (Zieldatei):**
```
$ pytest tests/test_cli_provider.py -q
47 passed in 0.42s
```

**Gesamtsuite — Baseline-Vergleich (identisch, keine Regression):**

| Lauf | Ergebnis |
|---|---|
| `origin/main` (unverändert, ohne Fix) | `5 failed, 966 passed, 4 skipped, 16 deselected` |
| Branch mit Fix | `5 failed, 966 passed, 4 skipped, 16 deselected` |

Die 5 Failures sind **preexistent** und **nicht** durch diesen Fix verursacht:
Sie treten nur bei `.env`-Anwesenheit auf und sind im Repo bereits in PR #19
dokumentiert (`changes/2026-10-26_todo-kw44-status-kopfzeile.md`, Commit
`docs: Praeexistenz des CI-Fehlers am unveraenderten main belegen`).
Gegenprobe: dieselben 5 Tests auf unverändertem `origin/main` mit identischer
Dateikombination → **identische 5 Failures**. Im Einzelruf sind sie grün
(Test-Pollution/Reihenfolge-Abhängigkeit der Suite, kein Code-Defekt).

**Live-Probe nach dem Fix:**
```
$ mcporter call pal chat model="cli-agy-gemini-pro" \
    prompt="reply with exactly: CLEAN_BASE_OK" \
    working_directory_absolute_path=/home/chris/pal-mcp-server
content: "CLEAN_BASE_OK"
metadata.model_used: cli-agy-gemini-pro
```

Vorher `error`, nachher `content` — der Backend ist wieder funktionsfähig.

## Nebenbefund (im changes/-Eintrag belegt, nicht Teil des Fixes)

Der ursprüngliche Fix-Commit lag auf dem PR-#20-Branch (`fix/mcp-pin-upper-bound`,
HEAD `4bf303d`) und trug dessen 12 Commits mit. Ein PR von diesem Branch hätte
PR #20 dupliziert. Deshalb: **eigener Branch direkt auf `origin/main`**
(`5d41a7c`), derselbe 3-Zeilen-Diff, byte-identisch verifiziert.

## Auswirkung

`cli-agy-gemini-pro` funktioniert wieder. Das ist einer von drei PAL-CLI-Backends —
relevant, weil `claude` (OAuth abgelaufen 28.10. 10:34 UTC) und `codex`
(nicht angemeldet) derzeit **beide** ausfallen. `agy` ist aktuell der einzige
funktionierende Consensus-Backend.

## Nicht enthalten

Kein Merge (Merge auf `main` löst `semantic-release` → öffentliche Publikation
`ghcr.io` + Version 9.9.1 aus → **Christian-Gate**). Kein Deploy, kein
Secret, keine Policy-Änderung.

---

## Nachtrag Do 2026-10-29 — Review-Runde (`pal codereview`), LOW-Befund (`conf/cli_models.json:181`) & Compliance-Nachzug (#22)

### 1. Review-Runde über `pal codereview` (Verfügbarkeit & Selbstreview-Vermerk)

Nach Wiederherstellung des `cli-agy-gemini-pro`-Backends wurde PR #22 am 2026-10-29 via
`mcporter call pal codereview` (`model=cli-agy-gemini-pro`, `relevant_files`:
`clink/consensus_backends.py`, `conf/cli_models.json`, `tests/test_cli_provider.py`)
geprüft:

- **Backend-Status (live geprüft via `pal chat`):** `cli-agy-gemini-pro` funktioniert
  (`PAL_BACKEND_OK`), während `cli-claude-sonnet` (OAuth abgelaufen) und `cli-codex-gpt`
  (`401 Unauthorized`) weiterhin ausfallen.
- **Explizite Einschränkung (Selbstreview):** Da `agy` sowohl den Fix implementiert hat als
  auch der einzige derzeit funktionierende Review-Backend ist, handelt es sich um ein
  **Selbstreview**. Dies ist in `COMPLIANCE-TABLE.md` (Zeile 22) ausdrücklich offengelegt.
- **Review-Urteil:** **APPROVE** (keine funktionalen oder sicherheitsrelevanten Mängel) mit
  **einem LOW-Befund**:
  - `conf/cli_models.json:181`: Nach dem Update von `cli_model` in Zeile 198 auf
    `"Gemini 4 Argon (Low)"` verwies das `description`-Feld in Zeile 181 weiterhin auf
    `"Gemini 3.1 Pro over the agy CLI..."`.

### 2. Unabhängige Gegenprüfung & Behebung des LOW-Befunds

- Auf der Basis `origin/fix/mcp-pin-upper-bound` (`4bf303d`) waren `description` (Zeile 181)
  und `cli_model` (Zeile 198) konsistent auf `"Gemini 3.1 Pro"` gesetzt; die Inkonsistenz
  wurde durch PR #22 neu eingeführt.
- Passend zum `friendly_name` in Zeile 166 (`"CLI (Gemini Pro via Google One)"`) und zur
  versionsneutralen Formulierung der übrigen Einträge in `conf/cli_models.json`
  (`"Claude Sonnet over the claude CLI..."`, `"Claude Opus over the claude CLI..."`,
  `"OpenAI models over the codex CLI..."`) wurde Zeile 181 generisch gefasst, damit sie
  beim nächsten Anbieter-Renaming nicht erneut veraltet:
  ```json
  "description": "Gemini Pro over the `agy` CLI (Google One subscription, no API cost). Serves the gemini/pro alias family in subscription mode.",
  ```
- `cli_model` (`"Gemini 4 Argon (Low)"`, Zeile 198) bleibt unverändert.

### 3. Schließung der zwei Buchhaltungs-Lücken in `COMPLIANCE-TABLE.md`

- **Lücke A (fehlende Zeile für PR #22):** PR #21 (auf ungepinntem `main`) wurde am
  2026-10-28 17:36:02 UTC zugunsten des gestapelten PR #22 (Basis `fix/mcp-pin-upper-bound`)
  geschlossen, `COMPLIANCE-TABLE.md` enthielt aber bislang nur Zeile `#21`.
- **Lücke B (`CR`-Spalte):** Zeile `#21` stand auf `CR = ~~` („Review-Runde offen").
- **Auflösung nach Hausregel:** Zeile `#21` bleibt als datierter Befund des geschlossenen
  PR #21 unverändert stehen; für den aktiven PR **#22** wurde eine eigene Zeile `| 22 | #22 |`
  mit `CR = ok`, explizitem Selbstreview-Vermerk, dokumentierter Behebung des LOW-Befunds und
  der sauberen CI-Checkout-Testevidenz (`971 passed, 4 skipped, 16 deselected, 0 failed` ohne
  `.env`-Artefakt; `pytest tests/test_cli_provider.py -q` → `47 passed`) ergänzt.

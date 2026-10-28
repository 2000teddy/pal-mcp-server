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

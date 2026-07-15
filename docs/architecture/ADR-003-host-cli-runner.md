# ADR-003 (PAL-Repo-Spiegel) — Keyfree Host-CLI-Runner: Draht-Vertrag & CO-01-Rebuild-Konformität

> **Status:** Referenz-Spiegel · **Eigentum:** Core · **Einzige normative Quelle:** die **gemergte** Core-`ADR-003`
> `docs/architecture/ADR-003-pal-keyfree-host-cli-runner.md` **§8 (Contract)** — gelandet als **Core PR #52**,
> per `tests/unit/test_adr003_contract_doc.py` an den Runner-Code gepinnt. Bei jeder Abweichung gilt Core §8, nicht dieser Spiegel.
> **Nur historischer/Live-Beleg (nicht normativ):** Core→PAL-Handoff
> `~/hermes/reports/2026-07-15_1115_ADR-003-runner-contract-handoff.md` und PAL-Bridge-Karte
> `~/hermes/reports/2026-07-15_1049_CO-01-bridge-runner-verifikation.md`.
>
> **Warum dieser Spiegel:** Der Runner-Code lebt im Core-Baum (`/opt/thinkhub/core/pal-runner/`, TABU für
> Admin/PAL). Im PAL-Repo war `grep ADR-003` = 0 Treffer — der Vertrag `server.py`/`clink` → Container-Shim →
> AF_UNIX-Runner war PAL-seitig nirgends referenzierbar. Dieser Spiegel schließt die Lücke **als Referenz**
> (kein Fork): er hält fest, welche Invarianten die **aus diesem Repo gebaute** `thinkhub-pal`-Image-/`clink`-Seite
> beim CO-01-Rebuild einhalten muss. Änderungen am Vertrag selbst gehören ins Core-Repo, nicht hierher.

## 1 · Was aus diesem Repo in den Rebuild geht

Der CO-01-Rebuild baut `thinkhub-pal` aus **diesem Repo** (`Dockerfile` → `CMD ["python", "server.py"]`).
Die PAL-Seite spricht den Runner **nicht direkt**, sondern ruft `claude`/`codex`/`agy` als Subprozesse
(`clink/cli_invoke.py`, `subprocess.Popen`, argv-Liste, `stdin=PIPE`); im Container sind diese Namen der
**Shim** (`_forwarder`), der über AF_UNIX an den Host-Runner weiterreicht. PAL-seitige Vertragskonformität =
korrekte Aufruf-Konstruktion + kompatible Limits, nicht das Framing selbst (das lebt im Shim/Runner, Core-Baum).

## 2 · Draht-Vertrag (normativ: Core `ADR-003` §8 / Core PR #52 — hier nur als Referenz gespiegelt)

- **Transport:** `AF_UNIX` / `SOCK_STREAM`, eine Anfrage pro Verbindung.
- **Framing:** 4-Byte big-endian Länge (`struct >I`) + UTF-8-JSON-Body.
- **Request (Shim→Runner):** `{ "cli": "claude|codex|agy", "args": [...], "stdin_b64": "..." }` —
  `cli` = basename(argv[0]), `args` = argv[1:], `stdin` nur ohne TTY.
- **Response:** `{ "exit_code": int, "stdout_b64": ..., "stderr_b64": ..., "error": "<slug?>" }` — bit-genau zurückgespielt.
- **Exit-/Fehler-Codes (invariant):** `2` bad_request · `127` not_allowed · `124` timeout · `126` exec_failed ·
  `1` runner_error · `125` Shim: Runner unerreichbar/I/O.

## 3 · Socket-Konvention

- Container-Default: `PAL_CLI_RUNNER_SOCKET` → sonst `/run/pal-cli/pal-cli-runner.sock` (gleich in Runner & Shim).
- Host-Ist: `/run/user/1000/pal-cli/pal-cli-runner.sock` (systemd `--user`, `RuntimeDirectory=pal-cli`).
- Mount (compose, Core-Baum): das **Verzeichnis**, nicht die Datei —
  `${PAL_CLI_RUNNER_DIR_HOST:-/run/user/1000/pal-cli}:/run/pal-cli`.

## 4 · CO-01-Rebuild-Konformitäts-Checkliste (PAL-Seite)

Gegen diese Punkte ist die **neu gebaute** Image-/`clink`-Version vor dem Deploy zu prüfen (Belege repo-lokal):

| # | Invariante (Quelle) | Repo-seitiger Check | Ist-Stand HEAD `f5173d5` |
|---|---|---|---|
| C1 | CLI-Aufruf = basename + argv + stdin (§2) | `clink/cli_invoke.py` `Popen(..., stdin=PIPE)`, argv-Liste, `prompt_mode` stdin/arg | ✅ konform |
| C2 | Whitelist `claude/codex/agy`, `shell=False` (§4) | keine Shell-Interpolation in `cli_invoke`; CLIs aus `conf/cli_models.json` | ✅ konform |
| C3 | Timeout ≤ Runner-`DEFAULT_TIMEOUT` (300 s, §4) | `clink/cli_invoke.py` Default = `DEFAULT_TIMEOUT_SECONDS` (aus `consensus_backends` = **300**) | ✅ aligned |
| C3a | **Drift-Warnung:** per-CLI-`timeout`-Override >300 s in `conf/cli_models.json` würde der Runner dennoch bei 300 s kappen (exit `124`). `clink/constants.py` trägt separat `1800` — **nicht** der von `cli_invoke` genutzte Wert. | vor Rebuild: `grep -n timeout conf/cli_models.json` | prüfen |
| C4 | Backend-Resolution = `subscription` (§5) | `.env` Z.255 `PAL_BACKEND=subscription`; Mesh-`pal` (mcporter) nur `PAL_MCP_FORCE_ENV_OVERRIDE=true` → Netto Default | ✅, aber **explizit setzen/bestätigen** beim Rebuild |
| C5 | Healthz-Endpoint bleibt (§Bridge) | `Dockerfile` `HEALTHCHECK … healthcheck.py`; Container `curl /healthz` → `ok` | ✅ live grün |

## 5 · Ordering-Invariante (kritisch, Core-seitig beim Deploy)

Runner-**Service muss laufen, BEVOR** `docker compose up` — sonst legt Docker das Socket-Verzeichnis als
**root** an und der Runner (User `chris`, uid 1000) kann nicht binden. uid-Alignment `appuser(1000) == chris(1000)`.
Das ist ein **Core-/Nacht-Fenster-Schritt**; hier nur als Referenz, damit der Rebuild nicht dagegen läuft.

## 6 · Grenzen

Reiner Referenz-Spiegel. Kein Runner-Code, kein Framing-Fork. Die **durable** Vertrags-Verankerung
ist **bereits gelandet**: Core-`ADR-003` §8 (Contract) via **Core PR #52**, an den Runner-Code gepinnt durch
`tests/unit/test_adr003_contract_doc.py`. Sie ist damit **nicht mehr ausstehend**; der frühere Handoff war laut
seinem eigenen §7 nur ein temporärer Vorläufer dieser Verankerung. Dieser Spiegel deckt allein die PAL-Repo-Seite
und **referenziert** Core §8 als Quelle — er ergänzt oder ändert den Vertrag nicht.

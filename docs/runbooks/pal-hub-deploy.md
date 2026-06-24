# Runbook — PAL MCP Server Deploy

> **Scope & Heimstatt (bitte zuerst lesen).** Dieses Runbook dokumentiert den Deploy des
> **`pal-mcp-server`-Containers aus DIESEM Repo** (`docker-compose.yml` / `Dockerfile` /
> `docker/scripts/`). Die **ThinkHub-Hub-Integration** (Container `thinkhub-pal`, der
> stdio→Port-Bridge-Layer, der gemeinsame Stack unter `/opt/thinkhub/core/docker-compose.yml`)
> ist **NICHT** in diesem Repo definiert — sie gehört zu **thinkhub-core** und wird hier nur
> referenziert, nicht dupliziert. Wo die Hub-Topologie von diesem Repo abweicht, ist das unten
> ehrlich markiert (insb. Healthcheck: pal ist ein **stdio-MCP-Server ohne HTTP-Port**, das
> `:8000/healthz` gehört thinkhub-**core**, nicht pal).
>
> Stand: 2026-06-24 · Grundlage: `docker-compose.yml`, `Dockerfile`, `docker/scripts/healthcheck.py`,
> `.env.example`, ADR-002 (key-free CLI). **Kein Live-Deploy in diesem Dokument.**

---

## 1. Voraussetzungen

- **Docker Engine** (getestet ≥ 24) und **Docker Compose v2** (`docker compose version`).
- **Image baubar**: das Repo enthält `Dockerfile` (Multi-Stage, Target `runtime`) und
  `docker-compose.yml` (Service `pal-mcp`, Container `pal-mcp-server`, Image `pal-mcp-server:latest`).
- **Kein eigener Port nötig**: pal ist ein **stdio-MCP-Server** (`CMD ["python", "server.py"]`,
  **kein `EXPOSE`**). Eine Port-Exposition entsteht erst durch den Hub-Bridge-Layer (supergateway,
  stdio→Port) — der ist **thinkhub-core-Sache**, nicht Teil dieses Compose.
- **Schreibbares `./logs`** (wird als Volume gemountet) und das benannte Volume `pal-mcp-config`.
- **Optional — Auto-Start**: wer pal als Dienst hochfahren will, kann den Container per
  `restart: unless-stopped` (bereits im Compose) ODER per **systemd user service** betreiben
  (Unit mit `ExecStart=docker compose up` / `EnvironmentFile=`). Systemd ist **nicht** Teil dieses
  Repos und muss separat eingerichtet werden.
- **Hub-Kontext (nur für den integrierten Deploy, thinkhub-core):** der gemeinsame Stack
  (`thinkhub-core` / `postgres` / `otel`) muss laufen; Quelle ist
  `/opt/thinkhub/core/docker-compose.yml`. Für den **Standalone-Deploy aus diesem Repo ist das
  nicht erforderlich.**

## 2. Konfiguration / `.env`-Provider-Reihenfolge

Empfohlene Schichtung, **höchste Priorität zuerst** (gewinnt bei Konflikt). **Keine echten
Secrets ins Repo** — `.env`-Dateien mit Keys sind `.gitignore`-pflichtig.

| Prio | Quelle | Hinweis |
|------|--------|---------|
| 1 (höchste) | **systemd `EnvironmentFile=`** | Nur wenn pal unter systemd läuft; die Unit liest die Datei, Docker erbt sie über die Shell. Erfordert explizite Unit-Konfiguration (nicht im Repo). |
| 2 | **`.env.local`** | Lokale, **nicht committete** Overrides. Hinweis: Compose liest standardmäßig nur `.env`; `.env.local` muss explizit via `--env-file .env.local` (oder Merge-Skript) gezogen werden. |
| 3 | **`.env`** (aus `.env.example` kopiert) | Repo-natives Compose-Interpolations-File (`${VAR}`-Defaults). `cp .env.example .env`, dann befüllen. |
| 4 (niedrigste) | **Inline `environment:` in `docker-compose.yml`** | Nur als **Eskalations-Helfer**/Default-Fallback (`${VAR:-default}`). Keine Keys hart eintragen. |

- **`PAL_MCP_FORCE_ENV_OVERRIDE`** (real, repo-eigen): steuert, ob `.env`-Werte die System-Env
  **überschreiben** (`true`) oder die System-Env Vorrang hat (`false`, Default in Tests). Für einen
  deterministischen Deploy bewusst setzen.
- **Key-free, empfohlen am Hub:** pal kann **ohne Provider-Keys** starten, wenn
  `PAL_MCP_ALLOW_KEYFREE_STARTUP=true` gesetzt ist (sonst Fail-fast „At least one API configuration
  is required"). Die **Generierung** über Abo-CLIs (claude/codex/agy) stammt aus **ADR-002**; das
  **Startup-Flag** selbst ist im Code als **ADR-003 / host-runner bridge** gekennzeichnet
  (`server.py`) — das ADR-Dokument liegt noch **nicht** im Repo (`docs/architecture/` hat aktuell
  nur ADR-001/002). Generierung siehe §3.

## 3. OAuth / headless — hart ehrlich

pal kennt **zwei Auth-Modelle**; sie unterscheiden sich grundlegend:

**A) Key-free CLI-Modus (ADR-002, der Hub-Zielzustand).** Auth läuft NICHT über Provider-API-Keys,
sondern über die **Abo-CLIs** selbst:
- `claude` (Anthropic-Abo), `codex` (ChatGPT-Abo), `agy` (Antigravity/Google).
- Anmeldung: jeweils der CLI-eigene Login (z. B. `claude` interaktiv, `codex login`, `agy login`).
- **Headless-Realität:** der **Erst-Login ist interaktiv** (Browser-/Device-Flow) → braucht
  **Christian-am-Gerät** (oder einen Browser auf dem Host). **Danach** persistiert das Token im
  CLI-Profil (`~/.claude`, `~/.codex`, `~/.config/agy` o. ä.) und der weitere Betrieb ist headless.
- Im Container: die CLI-Profile müssen als Volume/Bind eingebunden werden — **das ist eine
  thinkhub-core-Deploy-Frage** (Host-CLI-Runner-Sidecar, vgl. ADR-002 Entscheidung 2), nicht dieses
  Compose. Hier nur als Touchpoint vermerkt.

**B) Provider-API-Key-Modus (Legacy).** Das sind **statische Keys, KEIN OAuth**:
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`, `OPENROUTER_API_KEY`,
  `DIAL_API_KEY` → einfache Secrets in der Env (§2).
- **Azure OpenAI**: `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` (Key, ebenfalls **kein** OAuth).
- **Es gibt für diese Provider kein „headless OAuth"** — sie werden als Key gesetzt. Wer OAuth statt
  statischer Keys will (z. B. Azure AD / Entra für Azure OpenAI), braucht das auf Provider-Seite
  und ist hier **nicht abgedeckt** → Christian-am-Gerät / Provider-Konsole.

**Fazit headless:** vollständig headless ist nur der *Folge*-Betrieb nach einem einmaligen
interaktiven CLI-Login (Modus A) bzw. das Setzen statischer Keys (Modus B). Der **interaktive
Erst-Login (A)** ist **nicht** headless.

## 4. Smoke nach Deploy (kein Secret-Test)

> **Achtung:** Für den **pal-Container dieses Repos** gibt es **kein HTTP `/healthz`** — der
> Healthcheck ist ein **Prozess-/Import-Check** (`docker/scripts/healthcheck.py`: `pgrep -f
> server.py`, kritische Imports, Log-Verzeichnis schreibbar). Das `curl :8000/healthz` aus dem
> ThinkHub-Kontext trifft **thinkhub-core**, nicht pal.

```bash
# Läuft der Container, und ist er "healthy"?
docker compose ps
docker inspect --format '{{.State.Health.Status}}' pal-mcp-server

# Healthcheck explizit ausführen (Exit 0 = ok), ohne Secrets:
docker compose exec pal-mcp python /usr/local/bin/healthcheck.py; echo "exit=$?"

# Letzte Logzeilen sichten (Repo-Container heißt pal-mcp-server):
docker compose logs --tail 50 pal-mcp | head
#   Hub-Variante (thinkhub-core): docker logs --tail 50 thinkhub-pal | head
```

Erwartung: `State.Health.Status = healthy`, Healthcheck-Exit `0`, in den Logs „Logging to …" +
„Available providers: …" bzw. (key-free) die `PAL_MCP_ALLOW_KEYFREE_STARTUP`-Warnung. **Kein**
echter Tool-Call mit Secrets im Smoke.

## 5. Rollback

```bash
# Container + Netzwerk stoppen/entfernen (Volumes bleiben erhalten):
docker compose down

# Vorher: benanntes Config-Volume sichern (kein Secret-Dump, nur Volume-Inhalt):
docker run --rm -v pal-mcp-config:/data -v "$(pwd)/backups:/backup" \
  alpine tar czf /backup/pal-mcp-config-$(date +%Y%m%d).tgz -C /data .
#   -> Backup-Pfad: ./backups/pal-mcp-config-<datum>.tgz  (./backups vorher anlegen)

# Logs liegen als Bind-Mount unter ./logs (kein Volume-Backup nötig).

# Auf vorheriges Image zurück: zuvor getaggtes Image deployen, z. B.
#   docker tag pal-mcp-server:latest pal-mcp-server:rollback   (vor dem Update setzen)
#   docker compose up -d   (nutzt das in compose referenzierte Image)
```

`docker compose down -v` würde auch `pal-mcp-config` **löschen** — nur nach gesichertem Backup und
bewusst einsetzen.

---

### Offene Punkte / nicht hier dokumentiert (bewusst, kein Spekulieren)

- **Hub-Bridge (stdio→Port, supergateway), `thinkhub-pal`-Compose, `:8000`-Topologie, CLI-Profil-
  Mounts**: gehören zu **thinkhub-core** (`/opt/thinkhub/...`) und sind nicht in diesem Repo
  verifizierbar → dort dokumentieren, nicht hier raten.
- Ob ein **vollständiges Hub-Deploy-Runbook** in pal-mcp-server oder in thinkhub-core/ein Runbooks-Repo
  gehört, ist eine offene **Heimstatt-Frage** (siehe PR-Body).

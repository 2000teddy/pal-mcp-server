# 2026-10-26 — CI-Gate-Lücken als benannte Backlog-Punkte (CI-Gate-1 / CI-Gate-2)

**Art:** reine Dokumentation. Keine Berechtigungs-Änderung, keine Änderung an
`.github/workflows/`, kein Merge, kein Release.

**Auslöser:** Watchdog-Sweep vom 26.10., im Bericht auf „~15:50 UTC" datiert; eingegangen und
bearbeitet um **15:40 UTC** — die Datumszeile des Berichts liegt also zehn Minuten in der
Zukunft. Hier als Zitat wiedergegeben, nicht übernommen. Der Sweep hat zu Recht beanstandet, dass das
Repo-Admin-Follow-up zum MD-Compliance-Gate nur als **Unterzeile unter einem abgehakten Punkt**
(`TODO.md`, „🟠 In Arbeit", Unterpunkt des `[x]` zur MD-Pflege) steht. In einer Checkliste ist ein
offener Posten unter einem `[x]` unsichtbar — genau deshalb ist er drei Monate liegen geblieben.

## Was aufgenommen wurde

Zwei **getrennte** Punkte unter „🟡 Offen", jeder mit Ist-Stand, konkreter Aktion, Zuständigkeit und
Gate-Begründung:

### CI-Gate-1 — `main` hat keine Branch-Protection
- **Ist-Stand, live geprüft:** `gh api repos/2000teddy/pal-mcp-server/branches/main/protection` →
  **HTTP 404 „Branch not protected"**.
- **Wirkung:** Das md-compliance-Gate ist seit dem 21.07. im blockierenden Modus
  (`WARN_UNTIL=2026-07-21` → `exit 1` statt `::warning::`) — aber ohne Branch-Protection ist es
  **kein** *required status check*. Ein roter Check verhindert keinen Merge. Das gilt für **alle
  sieben** Checks: sie sind Hinweis, nicht Schranke.
- **Zu tun:** Branch-Protection-Rule auf `main`, darin `md-compliance`, `test (3.10/3.11/3.12)` und
  `lint` als *required*; zu entscheiden, ob `Build Docker Image` und `Validate PR` mitkommen und ob
  „require a pull request before merging" + „dismiss stale approvals" gesetzt werden.
- **Warum Christian-Gate:** Das Lane-Token hat `admin=true`, könnte die Rule also technisch setzen.
  Es ist aber eine **Policy-Entscheidung auf einem öffentlichen Repo** (`visibility: public`): sie
  legt fest, wer unter welchen Bedingungen auf `main` schreiben darf, wirkt auf alle künftigen
  Beiträge einschließlich externer Forks, und kann mit „include administrators" den Owner selbst
  aussperren. Technische Machbarkeit ist hier kein Mandat.

### CI-Gate-2 — auf `main` läuft nie ein Testlauf
- **Ist-Stand:** `.github/workflows/test.yml` triggert ausschließlich auf
  `pull_request: branches: [main]`. Kein `push`-, kein `schedule`-Trigger. Geprüft an allen sechs
  Workflows: nur `semantic-release.yml` läuft auf `push: main`, `docker-release.yml` auf
  `release: published`, der Rest auf `pull_request`.
- **Wirkung:** Zwischen dem 15.07. und dem 26.10. wurde kein PR geöffnet → **drei Monate kein
  einziger Testlauf**. „Grün" war in dieser Zeit erinnert, nicht gemessen. Darin konnte die
  `mcp`-Drift unbemerkt reifen; sie ist erst mit dem ersten PR nach drei Monaten sichtbar geworden.
- **Teil-Ausnahme, die es nicht auffängt:** `semantic-release.yml:36-40` hat einen Schritt
  „Verify tests pass" (`pytest … -m "not integration"`). Der ist am 26.10. nach dem Merge von #19
  mit denselben 9 Collection-Errors gescheitert (Run `40287130220`). Folge: **kein Release** — aber
  auch **kein sichtbares rotes Signal**, weil ein fehlgeschlagener Release-Lauf in keiner
  PR-Checkliste erscheint. Der Schutz hat also gegriffen, ohne zu warnen.
- **Zu tun:** `push: branches: [main]` und/oder ein `schedule:`-Trigger in `test.yml`.
- **Warum Christian-Gate:** Änderung an `.github/workflows/` ist Repo-Admin. Kostenargument spricht
  dafür (Actions-Minuten sind auf öffentlichen Repos frei, also kostenneutral), aber es bleibt eine
  Workflow-Entscheidung, und dieser Auftrag schließt Workflow-Änderungen ausdrücklich aus.

## Abgrenzung zum Auftragstext

Der Sweep hat beide Punkte als **einen** („der CI-Trigger-Punkt") behandelt und auf
`TODO.md:28-29` als „bereits erfasst" verwiesen. Das trifft nur auf CI-Gate-1 zu. CI-Gate-2 — dass
`test.yml` nur auf `pull_request` läuft — stand **nirgends** im Backlog, sondern nur als Lehre im
Fließtext von `HISTORY.md`. Es sind zwei verschiedene Lücken mit zwei verschiedenen Fixes: die eine
macht rote Checks verbindlich, die andere lässt überhaupt erst welche entstehen. Eine
Branch-Protection auf `main` hätte die `mcp`-Drift **nicht** gefunden, weil ohne PR gar kein Check
läuft. Deshalb zwei Punkte.

## Was ausdrücklich NICHT getan wurde
- Keine Branch-Protection gesetzt (obwohl `admin=true`).
- Keine Zeile in `.github/workflows/` angefasst.
- Kein Merge, kein Tag, kein Release. PR #20 bleibt ein Owner-Gate.
- Die Unterzeile an `TODO.md:28-29` wurde **nicht gelöscht** (Hausregel), sondern um einen Zeiger
  auf den neuen Punkt ergänzt.

## `BUILD_NUMBER.md`
Bleibt bei **4**. Reine Doku innerhalb desselben PRs — dieselbe Begründung wie beim TODO-Nachtrag:
der Bump gilt dem Arbeitsschritt, nicht jedem Doku-Commit darin (Hauspraxis der Doku-PRs #15–#19).

## Review
`pal clink` · `cli_name=claude` · `role=codereviewer` → `claude-sonnet-5-5`. Siehe PR-Kommentar.

## Status
Kein Selbst-Merge. Die beiden Punkte sind **Christian-Gates** und bleiben offen, bis er entscheidet;
die Lane führt sie nicht eigenmächtig aus, obwohl das Token es technisch erlaubt.

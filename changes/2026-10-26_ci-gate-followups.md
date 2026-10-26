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
- **Ist-Stand, live geprüft — und zwar alle drei Mechanismen:**
  - `gh api repos/2000teddy/pal-mcp-server/branches/main/protection` → **HTTP 404 „Branch not
    protected"** (klassische Branch-Protection)
  - `gh api repos/2000teddy/pal-mcp-server/rules/branches/main` → **`[]`** (keine Regel, die auf
    `main` greift)
  - `gh api repos/2000teddy/pal-mcp-server/rulesets` → **`[]`** (überhaupt kein Ruleset angelegt)

  Die erste Abfrage allein hätte **nichts** bewiesen, und in der ersten Fassung dieses Eintrags
  stand nur sie. **Rulesets** sind der neuere, parallele Mechanismus: sie schützen einen Branch
  unabhängig von der klassischen Protection und erscheinen im `protection`-Endpunkt **nicht** —
  ein 404 dort ist also kein Nachweis von Schutzlosigkeit. Befund aus der Review, nachgeprüft,
  und das Ergebnis stützt die Aussage stärker als vorher: alle drei leer.
- **Wirkung:** Das md-compliance-Gate ist seit dem 21.07. im blockierenden Modus
  (`WARN_UNTIL=2026-07-21` → `exit 1` statt `::warning::`) — aber ohne Branch-Protection ist es
  **kein** *required status check*. Ein roter Check verhindert keinen Merge. Das gilt für **alle
  sieben** Checks: sie sind Hinweis, nicht Schranke.
- **Zu tun:** Branch-Protection-Rule auf `main`, darin `md-compliance`, `test (3.10/3.11/3.12)` und
  `lint` als *required*; zu entscheiden, ob `Build Docker Image` und `Validate PR` mitkommen und ob
  „require a pull request before merging" + „dismiss stale approvals" gesetzt werden.
- **Warum Christian-Gate:** Das Lane-Token hat `admin=true`, könnte die Rule also technisch setzen.
  Es ist aber eine **Policy-Entscheidung auf einem öffentlichen Repo** (`visibility: public`): sie
  legt fest, wer unter welchen Bedingungen auf `main` schreiben darf, und wirkt auf alle künftigen
  Beiträge einschließlich externer Forks. Mit „include administrators" bindet sie **den Owner
  selbst** an den PR-Weg und an grüne Checks; er kann die Regel in den Settings jederzeit ändern
  oder löschen, aber nicht im Vorbeigehen umgehen. (Die erste Fassung schrieb „kann den Owner
  aussperren" — das war zu stark, Review-Befund, korrigiert.) Technische Machbarkeit ist hier kein
  Mandat.

### CI-Gate-2 — auf `main` läuft nie ein Testlauf
- **Ist-Stand:** `.github/workflows/test.yml` triggert ausschließlich auf
  `pull_request: branches: [main]`. Kein `push`-, kein `schedule`-Trigger. Geprüft an allen sechs
  Workflows: nur `semantic-release.yml` läuft auf `push: main`; `docker-release.yml` auf
  `release: published` **und** `workflow_dispatch` (letzteres fehlte in der ersten Fassung,
  Review-Befund); `test.yml`, `md-compliance.yml`, `semantic-pr.yml` und `docker-pr.yml` jeweils
  nur auf `pull_request`. **Kein einziger `schedule:`-Trigger im ganzen Repo.**
- **Wirkung:** Zwischen dem 15.07. und dem 26.10. wurde kein PR geöffnet → **drei Monate kein
  einziger Testlauf**. „Grün" war in dieser Zeit erinnert, nicht gemessen. Darin konnte die
  `mcp`-Drift unbemerkt reifen; sie ist erst mit dem ersten PR nach drei Monaten sichtbar geworden.
- **Teil-Ausnahme, die es nicht auffängt:** `semantic-release.yml:36-40` hat einen Schritt
  „Verify tests pass" (`pytest … -m "not integration"`). Der ist am 26.10. nach dem Merge von #19
  mit denselben 9 Collection-Errors gescheitert (Run `40287130220`). Folge: **kein Release** — aber
  auch **kein sichtbares rotes Signal**, weil ein fehlgeschlagener Release-Lauf in keiner
  PR-Checkliste erscheint. Der Schutz hat also gegriffen, ohne zu warnen.
- **Zu tun — die beiden Trigger sind nicht gleichwertig:** `push: branches: [main]` feuert erst
  **nach** einem Merge und hätte diese Drift **nicht** früher gefunden, weil in den drei Monaten
  gar nicht gepusht wurde; er schließt nur die Lücke „gemergt, aber nie getestet". **Nur ein
  `schedule:`-Trigger** findet Drift ohne Commit. Die erste Fassung führte beide als gleichwertig
  („und/oder") — irreführend, Review-Befund, korrigiert.
- **Fallstrick, der zum Fix gehört:** GitHub deaktiviert geplante Workflows in öffentlichen Repos
  **automatisch nach 60 Tagen ohne Repo-Aktivität**
  ([GitHub Docs](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows),
  nachgelesen 26.10.). In einem Repo, das 13 Wochen stillstand, wäre der nächtliche Lauf also
  selbst verstummt, und zwar lautlos. Ein `schedule:` allein genügt deshalb nicht — es braucht
  einen Keepalive oder die bewusste Inkaufnahme der Abschaltung plus manuelle Reaktivierung im
  Actions-Tab. Was GitHub als „Aktivität" zählt, definiert die Doku **nicht**; das ist vor dem
  Bau zu klären. Der Hinweis kam aus der Review und ist am Doku-Stand gegengeprüft.
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
`pal clink` · `cli_name=claude` · `role=codereviewer` → `claude-sonnet-5-5`, 2026-10-26.

**Runde 5** (auf `0163be8`): **CHANGES-NEEDED**, vier Befunde — alle zutreffend, alle behoben:
1. Das 404 an `branches/main/protection` beweist weniger als behauptet, weil **Rulesets** dort
   nicht erscheinen. Nachgeprüft: `rules/branches/main` → `[]`, `rulesets` → `[]`. Ergebnis
   stützt die Aussage, der Befund war trotzdem richtig — der Beleg war lückenhaft.
2. `push` und `schedule` waren als gleichwertig geführt. Falsch: `push` hätte diese Drift nicht
   gefunden. Getrennt dargestellt.
3. 60-Tage-Auto-Disable geplanter Workflows fehlte — am GitHub-Doku-Stand gegengeprüft und
   aufgenommen, inklusive der Einschränkung, dass „Aktivität" nicht definiert ist.
4. „kann den Owner aussperren" war überzogen; `docker-release.yml`-Trigger unvollständig. Beides
   korrigiert.

**Bestätigt von der Review:** die Trennung in CI-Gate-1 und CI-Gate-2 ist technisch korrekt und
der Widerspruch zum Sweep-Auftrag berechtigt („Branch-Protection macht einen vorhandenen Check
verbindlich, erzeugt aber keinen").

**Nicht vom Reviewer bestätigt** (die `gh`-Aufrufe waren ihm nicht freigegeben): das 404, die
Ruleset-Abfragen, `visibility: public`, `admin=true` und Run `40287130220`. Diese fünf Fakten sind
von dieser Lane geprüft, einseitig. Der Run ist nachgewiesen als `Semantic Release` / `failure` /
`event=push` / `head=5d41a7c` / `2026-10-26T07:39:29Z`.

## Status
Kein Selbst-Merge. Die beiden Punkte sind **Christian-Gates** und bleiben offen, bis er entscheidet;
die Lane führt sie nicht eigenmächtig aus, obwohl das Token es technisch erlaubt.

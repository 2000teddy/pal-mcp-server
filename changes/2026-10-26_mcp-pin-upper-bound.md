# 2026-10-26 — `mcp` nach oben begrenzen (`mcp>=1.0.0,<2`)

Folge-PR zum Review-of-Record von PR #19 (`claude-sonnet-5-5`, APPROVE,
`issuecomment-6409932957`). Dort war der Befund: `requirements.txt:1` pinnte `mcp>=1.0.0` **ohne
Obergrenze**, CI installierte inzwischen mcp **2.3.0**, und dort ist die lowlevel-Dekorator-API
entfallen → `AttributeError: 'Server' object has no attribute 'list_tools'` an `server.py:731`
beim Modul-Import → **9 Collection-Errors** auf allen drei Matrix-Versionen.

Dieser PR sind **zwei Code-Zeilen plus Nachweis** — eine je Versionsdeklaration. Er fasst bewusst
nichts anderes an. (Im ersten Anlauf war es eine Zeile; `pyproject.toml` kam über die Review herein.)

## Was
**Beide** Versionsdeklarationen des Repos, gleich gezogen:
- `requirements.txt:1`: `mcp>=1.0.0` → **`mcp>=1.0.0,<2`**
- `pyproject.toml:7`: `"mcp>=1.0.0"` → **`"mcp>=1.0.0,<2"`**

`pyproject.toml` war im ersten Anlauf übersehen und kam über die Review herein (High-Befund). Das
war kein Schönheitsfehler: `pyproject.toml` ist die Metadaten-Quelle für Wheel und sdist, also
hätten `pip install .` und jeder Install des veröffentlichten Pakets weiter auf mcp 2.x aufgelöst
und am Import gebrochen — während `semantic-release.yml:48-49` nach einem `fix(deps)`-Titel genau
dieses Artefakt veröffentlicht. Der Release hätte einen Fix behauptet, den sein Artefakt nicht
enthält. `git ls-files | xargs grep -lE 'mcp[>=<~]'` bestätigt, dass es **keine weiteren**
Deklarationen gibt (kein Lockfile, kein `setup.py`, kein `setup.cfg`); `test.yml:25` und
`Dockerfile:24` lesen `requirements.txt`.

## Warum eine Obergrenze und nicht ein exakter Pin
`mcp 1.x` enthält die Dekoratoren, die `server.py` nutzt; innerhalb der 1er-Reihe sind
Patch-/Minor-Updates gewollt (Sicherheitsfixes). Ein exakter Pin (`==1.27.2`) würde die Drift
anhalten, aber auch jedes Sicherheitsupdate blockieren. `<2` ist die kleinste Änderung, die den
tatsächlichen Bruch ausschließt.

## Was dieser PR ausdrücklich NICHT tut
- **Keine Migration auf die mcp-2.x-API.** `server.py` nutzt die lowlevel-Dekoratoren an vier
  Stellen (`:731`, `:793`, `:1392`, `:1442`); in 2.3.0 gehen dieselben Handler als
  Konstruktor-Callbacks (`on_list_tools=` / `on_call_tool=` / `on_list_prompts=` /
  `on_get_prompt=`) in den `Server`, eigene Methoden über `add_request_handler`. Am Paket
  nachgesehen (siehe §Review, zweite Runde) — die erste Fassung dieses Absatzes nannte
  zusätzlich `middleware`, das ist in 2.x aber eine eigene Schicht und **nicht** der
  Dekorator-Ersatz. Das ist ein Umbau, keine Umbenennung → bleibt eine **ADR-Frage** und ein
  offener TODO-Punkt.
- **Keine Obergrenzen für die übrigen Abhängigkeiten.** `requirements.txt:2-6`
  (`google-genai`, `openai`, `pydantic`, `python-dotenv`, `importlib-resources`), die
  vier Spiegelzeilen `pyproject.toml:8-11` (ohne `importlib-resources`) und **alle acht Zeilen** in `requirements-dev.txt`
  (`pytest`, `pytest-asyncio`, `pytest-mock`, `black`, `ruff`, `isort`,
  `python-semantic-release`, `build`) sind ebenfalls nur nach unten begrenzt. (Korrektur in der
  zweiten Review-Runde: hier stand erst `2-4` ohne die `pyproject.toml`-Seite.) Bewusst nicht
  mitgenommen — jede Obergrenze braucht ihren eigenen Verträglichkeits-Nachweis; es bleibt ein
  eigener offener Punkt. Dieser PR fasst `requirements-dev.txt` **nicht** an.

## Validierung
Siehe PR-Body für die vollständigen Läufe. Kurzform: frische venv aus
`requirements.txt` + `requirements-dev.txt`, dann der exakte CI-Befehl
(`pytest tests/ -v --ignore=simulator_tests/ -m "not integration"`), einmal CI-treu ohne `.env`
und einmal im Repo-Verzeichnis mit `.env`. Erfolgsmetrik ist **„keine Collection-Errors"** —
die 5 Failures, die nur mit `.env` auftreten, sind das in PR #19 belegte Umgebungsartefakt und
nicht Gegenstand dieses PRs.

## Bekannte Sequenz-Abhängigkeit zu PR #19
Der Backlog-Punkt, den dieser PR erledigt, steht in `TODO.md:47` **des #19-Branches** — auf `main`
existiert er noch nicht. Dieser PR ist von `main` gebranched (so beauftragt) und kann die Checkbox
deshalb nicht abhaken, ohne denselben Textblock ein zweites Mal anzulegen. Darum bleibt `TODO.md`
hier **unangetastet**; das Abhaken gehört in den PR, der als **zweiter** merged. Wird das
vergessen, führt `TODO.md` einen erledigten Punkt als offen — deshalb steht es hier, im PR-Body
und im Watchdog-Bericht.

## Nachweis für die `pyproject.toml`-Seite
Nicht nur statisch (Diff + grep), sondern aufgelöst — `pip install --dry-run .` in der frischen venv:

```
Collecting click>=7.0 (from uvicorn>=0.31.1->mcp<2,>=1.0.0->pal-mcp-server==9.9.0)
Would install … mcp-1.30.0 … pal-mcp-server-9.9.0 …
```

Der Resolver liest die Grenze aus `pyproject.toml` (`mcp<2,>=1.0.0`) und landet auf **1.30.0**.
Damit ist belegt, dass Wheel/sdist-Installationen nicht mehr auf 2.x laufen.

## Offen geblieben (bewusst, mit Begründung)
- **Untergrenze `>=1.0.0` ist unrealistisch.** `server.py:31-43` importiert `ToolAnnotations`,
  `PromptsCapability` und `ToolsCapability` und übergibt `instructions=` an `InitializationOptions`
  (`server.py:1605-1607`) — Symbole, die mcp 1.0.0 noch nicht hatte. Die Untergrenze ist damit eine
  Zusage, die der Code nicht hält. Die **echte** Mindestversion zu bestimmen heißt bisecten
  (frische venv pro Kandidat) und ist ein eigener Schritt; dieser PR behebt den real auftretenden
  Bruch nach oben, nicht die theoretische Lücke nach unten. Als Folgepunkt notiert, nicht geraten.
- **`APP_VERSION.md` ist aus dem Takt:** `pyproject.toml:3` steht auf **9.9.0**, `APP_VERSION.md`
  auf **9.8.2**. Die Datei soll laut ihrem eigenen Kommentar die Version spiegeln. Nebenbefund
  dieses PRs, hier **nicht** mitgeändert (eigener Punkt).
- **`APP_VERSION.md`/`pyproject.toml`-Spiegelung** bleibt als Nebenbefund stehen und wird
  **nicht** mitgeändert: die Version entscheidet `semantic-release` aus dem Commit-Titel
  (`pyproject.toml:124`, `patch_tags = ["fix", "perf"]`), nicht diese Lane. Ein manueller Eingriff
  in die Spiegel-Datei würde dem zuvorkommen.

## Nachtrag 26.10. — `TODO.md`-Checkbox im Branch abgehakt

(Commits `779047f` 15:07 UTC, `2d52791` 15:13 UTC und die Korrekturrunde darauf.)

**Befund (Watchdog-Sweep, im Bericht wörtlich auf „15:0x UTC" datiert, in der Lane eingegangen
15:05 UTC):** `git diff origin/main..origin/fix/mcp-pin-upper-bound
-- TODO.md` war **leer**. Der Rebase auf `5d41a7c` hat das Repo-Dokument nicht angefasst —
`TODO.md:47` stand im Branch weiterhin als offene 🔴-Sofortmaßnahme, identisch zu `main`. Damit war
genau der Zustand eingetreten, den der PR-Kommentar vom 26.10. 07:40 UTC selbst beschrieben hatte:
ein `main` mit gesetztem Pin, das den Pin im Backlog weiter als offen führt. Der Befund trifft zu
und ist nachgeprüft, nicht übernommen.

**Warum es passiert ist:** Die Checkbox kam mit PR #19 auf `main`; die Merge-Reihenfolge
(#19 zuerst) war bewusst so gewählt, damit sie überhaupt existiert. Der Auftrag zum Rebase sagte
dann ausdrücklich „`TODO.md:47` bleibt offen" — korrekt für den Zeitpunkt, an dem die Zeile noch
#19 gehörte und #20 noch nicht grün war. Nach dem Merge von #19 kippt diese Begründung, und das ist
beim Rebase nicht nachgezogen worden. Lehre: ein Reconcile-Punkt, der an einer Merge-Reihenfolge
hängt, muss nach dem ersten Merge **erneut** geprüft werden, nicht nur beim Setzen.

**Nachgezogen in diesem PR:**
- `TODO.md:47` → `- [x]`, mit Abschluss-Absatz (beide Deklarationen, aufgelöste Version, Testzahlen,
  Beleg-Datei). Der ursprüngliche Punkt-Text bleibt **wörtlich** stehen; es ist ein Zusatz, keine
  Umschreibung.
- Die beiden Dinge, die der Pin **nicht** erledigt, stehen jetzt **zusätzlich als eigene offene
  Einträge** unter „🟡 Offen": die ungeprüfte Restfläche und die mcp-2.x-Migration (ADR-Frage).
  Genauer als „herausgelöst": die Originalsätze bleiben wörtlich unter dem `[x]` stehen, die
  Punkte sind **kopiert**, nicht verschoben. Grund für die Dopplung: ein `[x]` über einem
  Absatz, der „gleiche Drift-Fläche, noch ungeprüft" enthält, liest sich als erledigt. Die
  Trennung ist der eigentliche Punkt des Nachtrags — ohne sie hätte das Häkchen zwei offene
  Themen mit zugedeckt.
- `COMPLIANCE-TABLE.md`: Zeile 19 trug noch den Platzhalter `(dieser PR)` aus der Zeit, als #19
  offen war. Da #19 am 26.10. 07:39 UTC als `5d41a7c` gelandet ist, steht dort jetzt `#19` —
  Konvention wie in allen Zeilen davor. Zeile 20 analog auf `#20`.
- **`BUILD_NUMBER.md` bleibt bei 4.** Der erste Anlauf des Nachtrags hatte auf 5 gebumpt; die
  zweite Review-Runde hat das als Doppelzählung markiert, und das trifft zu: die Begründung für
  3 → 4 war „dieser `fix`-PR = ein Arbeitsschritt". Ein Doku-Nachtrag **innerhalb** desselben
  PRs korrigiert diesen Schritt, er ist kein neuer — und die Hauspraxis der Doku-Commits
  (#15–#19) bumpt nicht. Zurückgenommen auf **4**.

**Kein Merge.** PR #20 ist laut `~/thinkhub-administrator/FREIGABEN-OFFEN-CHRISTIAN.md` ein eigenes
Christian-Gate: der Merge löst `semantic-release` aus und publiziert öffentlich (`v9.9.1` +
`ghcr.io`-Image, Repo-`visibility: PUBLIC`). Dieser Nachtrag macht den PR merge-**ready**, nicht
merge-**bar**.

## `BUILD_NUMBER.md`: gebumpt (3 → 4)

Der erste Anlauf hatte **nicht** gebumpt, mit Verweis auf die Hauspraxis der Doku-PRs #15–#18.
Die Review hat das als Regel-Unklarheit markiert, und die Auflösung ist eindeutig:
`CONTRIBUTING.md:44` sagt „+1 pro Arbeitsschritt" **ohne** Ausnahme für `fix`-PRs, und dies ist ein
`fix`-PR mit drei Commits und einer Runtime-Wirkung — also ein Arbeitsschritt, kein Bookkeeping.
Die Nicht-Bump-Praxis gilt für Doku-PRs; hier greift sie nicht. Gebumpt auf **4**.

## Review
`pal clink` · `cli_name=claude` · `role=codereviewer` → **`claude-sonnet-5-5`**, 2026-10-26.
Erstes Votum **CHANGES-NEEDED** mit einem High-Befund (`pyproject.toml` nicht mitgezogen) — der
Befund wurde nachgeprüft, traf zu und ist in diesem PR behoben.

**Zweite Runde (Review-of-Record für den TODO-Nachtrag), 15:08 UTC auf `779047f`:** erneut
**CHANGES-NEEDED**, sechs Befunde, alle Doku, kein Code. Nachgeprüft und behoben:
1. **Restfläche war unvollständig (Medium, traf zu).** Der neue Backlog-Punkt nannte nur
   `requirements.txt:2-4`. Ohne Obergrenze sind auch `:5` (`python-dotenv`) und `:6`
   (`importlib-resources`) sowie die Spiegelzeilen `pyproject.toml:8-11`. Am Dateistand
   nachgezählt, auf `2-6` + `pyproject.toml` korrigiert. Der Zählfehler stammt aus dem
   Original-Punkt von #19 und wäre mit der Kopie weitergetragen worden.
2. **`middleware` als 2.x-Dekorator-Ersatz war falsch (traf zu).** Der Reviewer konnte es nicht
   prüfen (kein Paket-Download freigegeben) und hat es als unbelegt markiert. Hier nachgesehen:
   frische venv mit `mcp==2.3.0`, `inspect.signature(Server.__init__)`. Ergebnis: die Handler
   gehen als `on_list_tools=` / `on_call_tool=` / `on_list_prompts=` / `on_get_prompt=` in den
   Konstruktor, eigene Methoden über `add_request_handler(method, params_type, handler)`;
   `Server.middleware` existiert **nicht**, `ServerMiddleware` ist eine eigene Schicht
   (`mcp/server/runner.py`). Backlog-Punkt und `HISTORY.md` entsprechend korrigiert. Die vier
   betroffenen Dekorator-Stellen sind `server.py:731`, `:793`, `:1392`, `:1442`.
3. **`BUILD_NUMBER` 4 → 5 war Doppelzählung (traf zu).** Zurückgenommen, siehe oben.
4. **Kopfzeilen-Zählung (traf zu).** `TODO.md:12-13` sprach von „drei Punkten … plus die zwei
   Kleinigkeiten"; mit den zwei neuen Einträgen sind es fünf. Angepasst.
5. **Formulierungen (traf zu).** „herausgelöst" → „zusätzlich als eigene Punkte geführt" (es
   ist eine Kopie); der Verweis auf eine lane-interne Auftragsformulierung ist aus dem
   Backlog-Text raus — das Repo ist öffentlich, und „bewusst außerhalb des Fix-Scopes, weil
   jede Obergrenze einen eigenen Nachweis braucht" ist die sachliche Begründung.
6. **Platzhalter-Uhrzeiten (traf zu).** Durch die tatsächlichen Commit-Zeiten aus `git log`
   ersetzt. Die Zeitangabe „15:0x UTC" des Sweep-Berichts bleibt als **Zitat** stehen — so steht
   sie im Bericht; der Eingang in der Lane war 15:05 UTC.

**Dritte Runde (Gegenprüfung auf `2d52791`), 15:13 UTC:** nochmals **CHANGES-NEEDED**, drei
Befunde, alle zutreffend und behoben:
1. **`pyproject.toml:8-12` war falsch (Medium).** Die Abhängigkeiten stehen auf **8–11**, Zeile 12
   ist die schließende `]`, und `importlib-resources` ist dort **nicht** deklariert (es ist ein
   `python_version<"3.9"`-Eintrag nur in `requirements.txt:6`). Also vier Spiegelzeilen, nicht
   fünf, und „spiegelbildlich" war zu stark. An allen sechs Stellen korrigiert. Die Zahl kam aus
   der zweiten Review-Runde und ist von mir ungeprüft übernommen worden — derselbe Fehler, den
   diese Runde beim Original-Punkt von #19 aufgedeckt hat, eine Ebene höher.
2. **Zukunfts-Uhrzeiten (Medium).** `15:2x`/`15:1x` waren zum Schreibzeitpunkt noch nicht
   eingetreten. Ersetzt durch die Commit-Zeiten aus `git log`; die Kopfzeile in `TODO.md` trägt
   jetzt nur noch das Datum.
3. **Befund-Zählung (Low-Medium).** COMPLIANCE-Zeile 20 sprach von „sechs Befunden, fünf trafen
   zu". Richtig ist: **sechs Befunde, alle sechs trafen zu und sind behoben**; der zusätzliche
   Layout-Hinweis (Punkt nach „✅" verschieben) war kein Befund, sondern eine Empfehlung, die der
   Reviewer selbst als nicht blockierend bezeichnet hat. Vereinheitlicht.

**Vierte Runde (Gegenprüfung auf `e571088`), 15:16 UTC: APPROVE.** Alle drei Punkte am Repo-Stand
bestätigt (Zeilenangaben, Uhrzeiten, Zählung), keine neuen Fehler. Damit ist die Review-of-Record
für den Nachtrag geschlossen. Der Reviewer hat selbst darauf hingewiesen, dass jeder weitere
Commit formal eine weitere Runde auslöst — dieser Absatz hält das APPROVE fest und ändert sonst
nichts; eine fünfte Runde darauf wäre reine Rekursion und findet nicht statt. Ausdrücklich
**nicht** vom Reviewer bestätigt (zweimal so gesagt, weil ohne Paket-Download nicht prüfbar): die
mcp-2.3.0-API-Details. Die sind von dieser Lane geprüft, mit genannter Methode — nicht von zwei
Seiten.

**Nicht übernommen:** den abgehakten Punkt aus „🟡 Offen" nach „✅" zu verschieben. Der
Reviewer nennt es selbst eine Layout-Entscheidung, nicht blockierend; `CONTRIBUTING.md:42`
definiert `TODO.md` als „Backlog **und** Fortschritt (offen/erledigt)", und `TODO.md:22` führt
dasselbe Muster. Ein Verschieben würde den Diff um einen Block-Move vergrößern, der im Review
schlechter zu lesen ist als das `[x]` an seiner Stelle.

## Status
Kein Selbst-Merge (`CONTRIBUTING.md` §Branch-Strategie). Review über `claude`
(`pal clink`, `role=codereviewer`); `codex` ist nicht einholbar (Token 08.07. abgelaufen, 401),
`pal:chat` ist für Reviews gesperrt.

# 2026-07-15 — TODO-Reconcile: CO-01-Blocker auf Realität umgeschrieben

Reiner Doku-/Bookkeeping-Nachtrag (Ebene-2-Reconcile). Der Blocker-Text zu CO-01 nannte
noch den ThinkLocal-Zwei-Peer-Proof als Bremse — der ist seit 15.07. erbracht. Working truth
im Repo muss den echten verbleibenden Blocker abbilden.

## Was
- **TODO.md, Abschnitt „⏸️ Blockiert (extern)", CO-01:** Blocker-Text ersetzt.
  - Alt: „wartet auf ThinkLocal Zwei-Peer-Proof (Re-Pair)".
  - Neu: TL-07 **erbracht** (Beleg verlinkt) + Gate-Revalidierung grün (HEAD `3fdb27d`); der
    verbleibende Blocker ist jetzt zweigeteilt: (a) **Core-/Hub-Mandat + Nacht-Fenster** für den
    Rebuild-Trigger (`docker compose … thinkhub-pal` unter `/opt/thinkhub` = TABU für Admin/PAL),
    (b) **geteilter Runner-Vertrag ADR-003** (Host-CLI-Runner unter `/opt/thinkhub/core/pal-runner/`
    noch undokumentiert).
  - Zeiger auf die Verifikation ergänzt: `~/hermes/reports/2026-07-15_1049_CO-01-bridge-runner-verifikation.md`.

## Warum jetzt
Der frühere externe Blocker (TL-07) ist weg; ohne Reword liest die einzige „was-blockiert"-Quelle
im Repo einen erledigten Grund. Der echte Rest-Blocker (Core-Fenster + ADR-003-Vertrag) stand nur
in den Hermes-Reports, nicht in der Repo-Working-Truth.

## Validierung
Reine MD-Änderung, **kein Python/Dockerfile/CI** → kein Test-/Build-Delta.
`/opt/thinkhub` nur beobachtend referenziert, nicht angefasst. Lokal: `git diff --check` sauber.

## Status
Kein Selbst-Merge, kein PR ohne echten Review (claude/codex/agy, nie MiniMax/pal:chat).
Auf Feature-Branch `docs/todo-co01-blocker-reword-20260715`, wartet auf Review-Freigabe.

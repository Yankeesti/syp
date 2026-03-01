# Quiz Module Findings

Kurz und knappe Liste von Bugs/Verbesserungen beim Testen des Quiz‑Moduls.

## Eintragen
- Format: `- [YYYY-MM-DD] Typ: Bereich – Kurzbeschreibung (Status)`
- Typ: Bug | Verbesserung | Frage
- Bereich: Router | Services | Repositories | Schemas | Models | Tests | Migrations | Sonstiges
- Optional: Referenz (Issue/PR), kurze Repro/Notizen
- Neueste Einträge oben anhängen.

## Beispiel
- [2026-01-17] Bug: Services – Score wird bei leeren Antworten nicht auf 0 gesetzt (Status: offen). Referenz: n/a

## Aktuelle Einträge
- [2026-01-17] Frage: Schemas – Cloze-Task gibt `blank_id` je Lücke zurück; ist das nötig, da `position` bereits eindeutig ist? (Status: offen).
- [2026-01-17] Verbesserung: Schemas – In `GET /quiz/quizzes` enthaltene Tasks führen unnötiges Feld `quiz_id` (bereits im übergeordneten Quiz vorhanden) (Status: offen).

# Learning Module – Findings

Kurze, prägnante Dokumentation von Bugs und Verbesserungen, die beim Testen des Learning‑Moduls auffallen. Einträge bitte knapp und handlungsorientiert halten.

Format für Einträge:
- Datum
- Typ: Bug | Verbesserung
- Bereich/Feature
- Beobachtung
- Vorschlag/Nächste Schritte
- Referenzen (optional: Route, Datei, Test)

Beispiel:
- 2026-01-17 | Bug | `/learning/sessions` | 500 bei leerem Payload | Validierung für Pflichtfelder ergänzen | Route: `POST /learning/sessions`

## Log

(Hier folgen die Einträge chronologisch, neueste oben)

- 2026-01-17 | Bug | PUT `/learning/attempts/{attempt_id}/answers/{task_id}` (cloze) | Entfernte Lücken bleiben bestehen: fehlende `blank_id`s im Payload löschen bestehende Einträge nicht; zudem können zuvor gespeicherte, nicht zur Task gehörende Blanks erhalten bleiben | Update als Snapshot behandeln: nur `blank_id`s erlauben, die in der Task definiert sind; übergebene Lücken upserten, alle anderen Lücken der Task für diesen Attempt löschen; 422 bei ungültiger `blank_id`; Tests: (1) 3→2 Blanks → 1 gelöscht, (2) ungültige `blank_id` → 422, (3) leere Liste → alle gelöscht | Route: PUT `/learning/attempts/{attempt_id}/answers/{task_id}`
- 2026-01-17 | Bug | POST `/learning/attempts/{attempt_id}/answers/{task_id}` (cloze) | Fehlende Validierung: übergebene `blank_id` existiert nicht in den Lücken der Task | `blank_id` gegen die in der Task definierten Lücken prüfen; bei Ungültigkeit 422/400 zurückgeben; Tests ergänzen (ungültige ID, fehlende ID) | Route: POST `/learning/attempts/{attempt_id}/answers/{task_id}`
- 2026-01-17 | Bug | PUT `/learning/attempts/{attempt_id}/answers/{task_id}` (multiple_choice) | Fehlende Validierung: `selected_option_ids` werden nicht gegen die Optionen der Task geprüft | Für jede ID prüfen, dass sie zu den auswählbaren Optionen der Task gehört; bei Verstoß 422/400 zurückgeben; Tests ergänzen (u. a. ungültige ID, Duplikate) | Route: PUT `/learning/attempts/{attempt_id}/answers/{task_id}`

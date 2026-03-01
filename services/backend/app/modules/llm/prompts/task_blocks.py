"""Task-Type spezifische Prompt-Blöcke für die Quiz-Generierung."""

from app.shared.enums import TaskType

# --- SCHEMAS ---

MC_SCHEMA = """{{
  "type": "multiple_choice",
  "prompt": "string - Die Fragestellung",
  "topic_detail": "string - Unterthema der Frage",
  "options": [
    {{"text": "string", "is_correct": boolean, "explanation": "string"}}
  ]
}}"""

FT_SCHEMA = """{{
  "type": "free_text",
  "prompt": "string - Die Fragestellung",
  "topic_detail": "string - Unterthema der Frage",
  "reference_answer": "string - Die Musterlösung"
}}"""

CLOZE_SCHEMA = """{{
  "type": "cloze",
  "prompt": "string - Einleitungstext",
  "topic_detail": "string - Unterthema der Frage",
  "template_text": "string - Text mit {{{{blank_N}}}} Platzhaltern",
  "blanks": [
    {{"position": number, "expected_value": "string"}}
  ]
}}"""

# --- EXAMPLES ---

MC_EXAMPLES = [
    """Beispiel 1 (3 Optionen, 1 richtig):
{{
  "type": "multiple_choice",
  "prompt": "In welchem Jahr fiel die Berliner Mauer?",
  "topic_detail": "Geschichte - Kalter Krieg",
  "options": [
    {{"text": "1989", "is_correct": true, "explanation": "Die Berliner Mauer fiel am 9. November 1989 und markierte das Ende des Kalten Krieges"}},
    {{"text": "1961", "is_correct": false, "explanation": "1961 wurde die Mauer errichtet, nicht abgerissen"}},
    {{"text": "2001", "is_correct": false, "explanation": "Das ist das Jahr von 9/11, nicht relevant für die Berliner Mauer"}}
  ]
}}""",
    """Beispiel 2 (4 Optionen, 2 richtig):
{{
  "type": "multiple_choice",
  "prompt": "Welche der folgenden sind Gase bei Raumtemperatur?",
  "topic_detail": "Chemie - Aggregatzustände",
  "options": [
    {{"text": "Sauerstoff", "is_correct": true, "explanation": "Sauerstoff ist ein Gas bei Raumtemperatur"}},
    {{"text": "Eisen", "is_correct": false, "explanation": "Eisen ist ein Metall und fest bei Raumtemperatur"}},
    {{"text": "Kohlendioxid", "is_correct": true, "explanation": "CO₂ ist ein Gas bei Raumtemperatur"}},
    {{"text": "Quecksilber", "is_correct": false, "explanation": "Quecksilber ist eine Flüssigkeit bei Raumtemperatur"}}
  ]
}}""",
    """Beispiel 3 (5 Optionen, 1 richtig):
{{
  "type": "multiple_choice",
  "prompt": "Welcher ist der größte Planet unseres Sonnensystems?",
  "topic_detail": "Astronomie - Sonnensystem",
  "options": [
    {{"text": "Saturn", "is_correct": false, "explanation": "Saturn ist groß, aber Jupiter ist größer"}},
    {{"text": "Merkur", "is_correct": false, "explanation": "Merkur ist der kleinste Planet"}},
    {{"text": "Jupiter", "is_correct": true, "explanation": "Jupiter ist mit einem Durchmesser von etwa 143.000 km der größte Planet"}},
    {{"text": "Neptun", "is_correct": false, "explanation": "Neptun ist groß, aber nicht der größte"}},
    {{"text": "Venus", "is_correct": false, "explanation": "Venus ist ähnlich groß wie die Erde, aber nicht der größte"}}
  ]
}}""",
]

FT_EXAMPLES = [
    """Beispiel 1 (kurze Antwort):
{{
  "type": "free_text",
  "prompt": "Was ist Photosynthese und warum ist sie für Pflanzen wichtig?",
  "topic_detail": "Biologie - Pflanzenstoffwechsel",
  "reference_answer": "Photosynthese ist ein biologischer Prozess, bei dem Pflanzen Licht, Wasser und Kohlendioxid in Zucker (Glukose) und Sauerstoff umwandeln. Sie ist für Pflanzen essentiell, da sie ihre Energiequelle darstellt und gleichzeitig Sauerstoff für die Atmosphäre produziert."
}}""",
    """Beispiel 2 (ausführliche Erklärung):
{{
  "type": "free_text",
  "prompt": "Erkläre die Unterschiede zwischen absoluten und relativen Altersbestimmungsmethoden in der Geologie.",
  "topic_detail": "Geologie - Datierungsmethoden",
  "reference_answer": "Relative Altersbestimmung ordnet Gesteine und Fossilien in eine Abfolge an, ohne exakte Alter zu bestimmen (z.B. durch Schichtenfolge). Absolute Altersbestimmung liefert konkrete Altersangaben durch radiometrische Methoden wie C-14 oder K-Ar Datierung. Relative Methoden sind älter und günstiger, während absolute Methoden präziser sind."
}}""",
]

CLOZE_EXAMPLES = [
    """Beispiel 1 (2 Lücken):
{{
  "type": "cloze",
  "prompt": "Vervollständige den Satz über das Sonnensystem:",
  "topic_detail": "Astronomie",
  "template_text": "Die Erde umkreist die {{{{blank_1}}}} in einer elliptischen Bahn und benötigt etwa {{{{blank_2}}}} Tage dafür.",
  "blanks": [
    {{"position": 1, "expected_value": "Sonne"}},
    {{"position": 2, "expected_value": "365"}}
  ]
}}""",
    """Beispiel 2 (3 Lücken):
{{
  "type": "cloze",
  "prompt": "Vervollständige den Satz über die Französische Revolution:",
  "topic_detail": "Geschichte - 18. Jahrhundert",
  "template_text": "Die Französische Revolution fand im Jahr {{{{blank_1}}}} statt, führte zum Sturz von {{{{blank_2}}}} und hatte das Motto {{{{blank_3}}}}.",
  "blanks": [
    {{"position": 1, "expected_value": "1789"}},
    {{"position": 2, "expected_value": "König Ludwig XVI."}},
    {{"position": 3, "expected_value": "Liberté, Égalité, Fraternité"}}
  ]
}}""",
]

# --- RULES ---

MC_RULES = """Regeln für Multiple Choice:
- Anzahl der Optionen kann variieren (3-5 empfohlen)
- Mindestens 1 korrekte Antwort
- Positionen der richtigen Antworten zufällig mischen"""

FT_RULES = """Regeln für Free Text:
- Fragen sollten inhaltlich logisch und klar formuliert sein
- Die Referenzantwort sollte verständlich und vollständig sein"""

CLOZE_RULES = """Regeln für Cloze:
- Lücken an sinnvollen Stellen setzen (wichtige Fachbegriffe)
- {{{{blank_N}}}} Format exakt einhalten
- blanks-Liste muss mit Platzhaltern im template_text korrespondieren"""

# --- DICTIONARIES FOR MAPPINGS ---

TASK_TYPE_SCHEMAS_DETAILED: dict[TaskType, str] = {
    TaskType.MULTIPLE_CHOICE: MC_SCHEMA,
    TaskType.FREE_TEXT: FT_SCHEMA,
    TaskType.CLOZE: CLOZE_SCHEMA,
}

TASK_TYPE_EXAMPLES: dict[TaskType, list[str]] = {
    TaskType.MULTIPLE_CHOICE: MC_EXAMPLES,
    TaskType.FREE_TEXT: FT_EXAMPLES,
    TaskType.CLOZE: CLOZE_EXAMPLES,
}

TASK_TYPE_RULES: dict[TaskType, str] = {
    TaskType.MULTIPLE_CHOICE: MC_RULES,
    TaskType.FREE_TEXT: FT_RULES,
    TaskType.CLOZE: CLOZE_RULES,
}

# --- FUNCTION TO BUILD TASK BLOCKS ---


def get_task_block(task_type: TaskType, num_types: int) -> str:
    """Baut einen Task-Block mit angepasster Beispielanzahl.

    Args:
        task_type: Der Task-Typ.
        num_types: Gesamtzahl der angeforderten Typen (für Beispielanzahl).

    Returns:
        Zusammengesetzter Block aus Schema, Beispielen und Regeln.
    """
    schema = TASK_TYPE_SCHEMAS_DETAILED[task_type]
    examples = TASK_TYPE_EXAMPLES[task_type]
    rules = TASK_TYPE_RULES[task_type]

    # Beispielanzahl basierend auf Gesamtzahl Typen
    if num_types == 1:
        selected_examples = examples[:3]
    elif num_types == 2:
        selected_examples = examples[:2]
    else:
        selected_examples = examples[:1]

    parts = [
        f"### {task_type.value.upper()}",
        "Schema:",
        schema,
        # *selected_examples,
        rules,
    ]
    return "\n\n".join(parts)


# --- STATIC BLOCKS (for backwards compatibility) ---

MULTIPLE_CHOICE_BLOCK = """
### MULTIPLE CHOICE ###

Schema:
{{
  "type": "multiple_choice",
  "prompt": "string - Die Fragestellung",
  "topic_detail": "string - Unterthema der Frage",
  "options": [
    {{"text": "string", "is_correct": boolean, "explanation": "string"}}
  ]
}}

Beispiel 1 (3 Optionen, 1 richtig):
{{
  "type": "multiple_choice",
  "prompt": "In welchem Jahr fiel die Berliner Mauer?",
  "topic_detail": "Geschichte - Kalter Krieg",
  "options": [
    {{"text": "1989", "is_correct": true, "explanation": "Die Berliner Mauer fiel am 9. November 1989 und markierte das Ende des Kalten Krieges"}},
    {{"text": "1961", "is_correct": false, "explanation": "1961 wurde die Mauer errichtet, nicht abgerissen"}},
    {{"text": "2001", "is_correct": false, "explanation": "Das ist das Jahr von 9/11, nicht relevant für die Berliner Mauer"}}
  ]
}}

Beispiel 2 (4 Optionen, 2 richtig):
{{
  "type": "multiple_choice",
  "prompt": "Welche der folgenden sind Gase bei Raumtemperatur?",
  "topic_detail": "Chemie - Aggregatzustände",
  "options": [
    {{"text": "Sauerstoff", "is_correct": true, "explanation": "Sauerstoff ist ein Gas bei Raumtemperatur"}},
    {{"text": "Eisen", "is_correct": false, "explanation": "Eisen ist ein Metall und fest bei Raumtemperatur"}},
    {{"text": "Kohlendioxid", "is_correct": true, "explanation": "CO₂ ist ein Gas bei Raumtemperatur"}},
    {{"text": "Quecksilber", "is_correct": false, "explanation": "Quecksilber ist eine Flüssigkeit bei Raumtemperatur"}}
  ]
}}

Beispiel 3 (5 Optionen, 1 richtig):
{{
  "type": "multiple_choice",
  "prompt": "Welcher ist der größte Planet unseres Sonnensystems?",
  "topic_detail": "Astronomie - Sonnensystem",
  "options": [
    {{"text": "Saturn", "is_correct": false, "explanation": "Saturn ist groß, aber Jupiter ist größer"}},
    {{"text": "Merkur", "is_correct": false, "explanation": "Merkur ist der kleinste Planet"}},
    {{"text": "Jupiter", "is_correct": true, "explanation": "Jupiter ist mit einem Durchmesser von etwa 143.000 km der größte Planet"}},
    {{"text": "Neptun", "is_correct": false, "explanation": "Neptun ist groß, aber nicht der größte"}},
    {{"text": "Venus", "is_correct": false, "explanation": "Venus ist ähnlich groß wie die Erde, aber nicht der größte"}}
  ]
}}

Regeln für Multiple Choice:
- Anzahl der Optionen kann variieren (3-5 empfohlen)
- Mindestens 1 korrekte Antwort
- Positionen der richtigen Antworten zufällig mischen
"""

FREE_TEXT_BLOCK = """
### FREE TEXT ###

Schema:
{{
  "type": "free_text",
  "prompt": "string - Die Fragestellung",
  "topic_detail": "string - Unterthema der Frage",
  "reference_answer": "string - Die Musterlösung"
}}

Beispiel 1 (kurze Antwort):
{{
  "type": "free_text",
  "prompt": "Was ist Photosynthese und warum ist sie für Pflanzen wichtig?",
  "topic_detail": "Biologie - Pflanzenstoffwechsel",
  "reference_answer": "Photosynthese ist ein biologischer Prozess, bei dem Pflanzen Licht, Wasser und Kohlendioxid in Zucker (Glukose) und Sauerstoff umwandeln. Sie ist für Pflanzen essentiell, da sie ihre Energiequelle darstellt und gleichzeitig Sauerstoff für die Atmosphäre produziert."
}}

Beispiel 2 (ausführliche Erklärung):
{{
  "type": "free_text",
  "prompt": "Erkläre die Unterschiede zwischen absoluten und relativen Altersbestimmungsmethoden in der Geologie.",
  "topic_detail": "Geologie - Datierungsmethoden",
  "reference_answer": "Relative Altersbestimmung ordnet Gesteine und Fossilien in eine Abfolge an, ohne exakte Alter zu bestimmen (z.B. durch Schichtenfolge). Absolute Altersbestimmung liefert konkrete Altersangaben durch radiometrische Methoden wie C-14 oder K-Ar Datierung. Relative Methoden sind älter und günstiger, während absolute Methoden präziser sind."
}}

Regeln für Free Text:
- Fragen sollten inhaltlich logisch und klar formuliert sein
- Die Referenzantwort sollte verständlich und vollständig sein
"""

CLOZE_BLOCK = """
### CLOZE (Lückentext) ###

Schema:
{{
  "type": "cloze",
  "prompt": "string - Einleitungstext",
  "topic_detail": "string - Unterthema der Frage",
  "template_text": "string - Text mit {{{{blank_N}}}} Platzhaltern",
  "blanks": [
    {{"position": number, "expected_value": "string"}}
  ]
}}

Beispiel 1 (2 Lücken):
{{
  "type": "cloze",
  "prompt": "Vervollständige den Satz über das Sonnensystem:",
  "topic_detail": "Astronomie",
  "template_text": "Die Erde umkreist die {{{{blank_1}}}} in einer elliptischen Bahn und benötigt etwa {{{{blank_2}}}} Tage dafür.",
  "blanks": [
    {{"position": 1, "expected_value": "Sonne"}},
    {{"position": 2, "expected_value": "365"}}
  ]
}}

Beispiel 2 (3 Lücken):
{{
  "type": "cloze",
  "prompt": "Vervollständige den Satz über die Französische Revolution:",
  "topic_detail": "Geschichte - 18. Jahrhundert",
  "template_text": "Die Französische Revolution fand im Jahr {{{{blank_1}}}} statt, führte zum Sturz von {{{{blank_2}}}} und hatte das Motto {{{{blank_3}}}}.",
  "blanks": [
    {{"position": 1, "expected_value": "1789"}},
    {{"position": 2, "expected_value": "König Ludwig XVI."}},
    {{"position": 3, "expected_value": "Liberté, Égalité, Fraternité"}}
  ]
}}

Regeln für Cloze:
- Lücken an sinnvollen Stellen setzen (wichtige Fachbegriffe)
- {{{{blank_N}}}} Format exakt einhalten
- blanks-Liste muss mit Platzhaltern im template_text korrespondieren
"""

TASK_TYPE_BLOCKS: dict[TaskType, str] = {
    TaskType.MULTIPLE_CHOICE: MULTIPLE_CHOICE_BLOCK,
    TaskType.FREE_TEXT: FREE_TEXT_BLOCK,
    TaskType.CLOZE: CLOZE_BLOCK,
}

# --- COMPACT SCHEMA DEFINITIONS (for correction prompts) ---

MULTIPLE_CHOICE_SCHEMA = """{
  "type": "multiple_choice",
  "prompt": "string",
  "topic_detail": "string",
  "options": [{"text": "string", "is_correct": boolean, "explanation": "string"}]
}"""

FREE_TEXT_SCHEMA = """{
  "type": "free_text",
  "prompt": "string",
  "topic_detail": "string",
  "reference_answer": "string"
}"""

CLOZE_SCHEMA = """{
  "type": "cloze",
  "prompt": "string",
  "topic_detail": "string",
  "template_text": "string mit {{blank_N}} Platzhaltern",
  "blanks": [{"position": number, "expected_value": "string"}]
}"""

TASK_TYPE_SCHEMAS: dict[TaskType, str] = {
    TaskType.MULTIPLE_CHOICE: MULTIPLE_CHOICE_SCHEMA,
    TaskType.FREE_TEXT: FREE_TEXT_SCHEMA,
    TaskType.CLOZE: CLOZE_SCHEMA,
}

"""Konstanten und Templates für die LLM-basierte Quiz-Generierung."""

from app.shared.enums import TaskType

# --- KONFIGURATION ---
DEFAULT_NUM_QUESTIONS = 10
DEFAULT_TOPIC = "Allgemeines Thema"

# --- ROLLEN-TEMPLATES ---
ROLE_SINGLE = """Du bist ein erfahrener deutschsprachiger Pädagoge, spezialisiert auf {task_type_desc}.
Du formulierst präzise, eindeutige und fachlich korrekte Aufgaben auf Deutsch."""

ROLE_MULTI = """Du bist ein erfahrener deutschsprachiger Pädagoge für vielfältige Lernaufgaben.
Du formulierst präzise, eindeutige und fachlich korrekte Aufgaben auf Deutsch."""

TASK_TYPE_DESCRIPTIONS: dict[TaskType, str] = {
    TaskType.MULTIPLE_CHOICE: "Prüfungsfragen mit Antwortoptionen",
    TaskType.FREE_TEXT: "offene Verständnisfragen",
    TaskType.CLOZE: "Lückentexte zur Begriffsabfrage",
}

# --- ZIEL-TEMPLATES (nach Kontext-Quelle) ---
OBJECTIVE_FILE_ONLY = """AUFTRAG: Erstelle EXAKT {num_questions} Aufgaben.
WICHTIG: Basiere ALLE Fragen ausschließlich auf dem Dokumentinhalt.
Füge KEIN eigenes Wissen hinzu - nur was im Dokument steht!"""

OBJECTIVE_DESC_ONLY = """AUFTRAG: Erstelle EXAKT {num_questions} Aufgaben.
Folge den Spezifikationen des Nutzers in der folgenden Nachricht.
Nutze dein Fachwissen für relevante und korrekte Fragen."""

OBJECTIVE_BOTH = """AUFTRAG: Erstelle EXAKT {num_questions} Aufgaben.
QUELLE: Das bereitgestellte Dokument (PRIORITÄT!)
Folge den Spezifikationen des Nutzers für den thematischen Fokus.
Ergänze nur wenn nötig mit Fachwissen."""

# --- PROZESS-TEMPLATES ---
PROCESS_WITH_FILE = """VORGEHEN:
1. Lies das Dokument vollständig
2. Identifiziere die {num_questions} wichtigsten prüfbaren Fakten
3. {assignment_step}
4. Validiere das JSON-Format"""

PROCESS_DESC_ONLY = """VORGEHEN:
1. Rufe dein Wissen zum Thema ab
2. Wähle {num_questions} grundlegende, wichtige Konzepte
3. {assignment_step}
4. Validiere das JSON-Format"""

# --- ASSIGNMENT-STEP FRAGMENTE ---
ASSIGNMENT_SINGLE_TYPE = "Formuliere zu jedem Konzept eine {task_type}-Aufgabe"

ASSIGNMENT_MULTI_INTRO = "Entscheide für jedes Konzept den passenden Aufgabentyp:"

ASSIGNMENT_MULTI_LINE = "   - {description} → {name}"

ASSIGNMENT_DISTRIBUTION = "Verteile gleichmäßig auf: {task_types}"

TASK_TYPE_ASSIGNMENT_HINTS: dict[TaskType, tuple[str, str]] = {
    TaskType.MULTIPLE_CHOICE: (
        "Fakten und Definitionen mit klaren Optionen",
        "Multiple Choice",
    ),
    TaskType.FREE_TEXT: ("Erklärungen und Zusammenhänge", "Free Text"),
    TaskType.CLOZE: ("Fachbegriffe und Terminologie", "Cloze"),
}

# --- OUTPUT-FORMAT ---
OUTPUT_FORMAT = """AUSGABEFORMAT: Valides JSON, KEIN zusätzlicher Text.

{{
  "title": "string - Titel des Quiz",
  "topic": "string - Hauptthema",
  "tasks": [ ... ]
}}"""

# --- FINALE CONSTRAINTS ---
FINAL_CONSTRAINTS = """REGELN:
- EXAKT {num_questions} Aufgaben sind in dem Quiz enthalten
- ALLE Texte auf DEUTSCH
- NUR valides JSON ausgeben"""

# --- USER PROMPT TEMPLATES ---
USER_PROMPT_TOPIC_TEMPLATE = "Thema/Beschreibung: {topic}\n"
USER_PROMPT_DOCUMENT_TEMPLATE = "DOKUMENT_START\n{content}\nDOKUMENT_ENDE"

# --- CORRECTION PROMPT TEMPLATES ---

CORRECTION_PROMPT_INTRO = """Deine vorherige JSON-Antwort war ungültig.

FEHLER:
{validation_errors}

Korrigiere deine Antwort. Erwartetes Format:"""

CORRECTION_PROMPT_QUIZ_SCHEMA = """
QUIZ-STRUKTUR:
{
  "title": "string",
  "topic": "string",
  "tasks": [...]
}
"""

CORRECTION_PROMPT_OUTRO = """
Antworte NUR mit dem korrigierten JSON."""

# --- TASK COUNT EXTRACTION PROMPT ---

TASK_NUMBER_EXTRACTION_PROMPT = """
Du extrahierst die gewünschte Anzahl an Fragen aus einem Nutzer-Prompt.
Antworte ausschließlich mit einem JSON-Objekt im Format: {"num_questions": <zahl>}.
Wenn keine Anzahl spezifiziert ist, setze den Wert auf -1.
Gib keine zusätzlichen Wörter, kein weiteres JSON, keine Erklärungen.

Beispiele:
userprompt: "Erstelle mir ein Quiz zum Thema Burgen mit 5 Fragen"
Ausgabe: {"num_questions": 5}
userprompt: "Erstelle mir ein Quiz über Angela Merkel"
Ausgabe: {"num_questions": -1}
"""

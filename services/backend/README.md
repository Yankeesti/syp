# Backend Overview

## Inhaltsverzeichnis
1. [Installation & Setup](#installation--setup)
2. [Server Starten](#server-starten)
3. [Code-Formatierung](#code-formatierung)
4. [Datenbank-Migrationen mit Alembic](#datenbank-migrationen-mit-alembic)
5. [Architektur](#architektur)
   - [Modularer Monolith](#modularer-monolith)
   - [Module & Bounded Contexts](#module--bounded-contexts)
   - [Layer-Architektur](#layer-architektur)

---

## Installation & Setup

### Voraussetzungen
- **Python 3.13 oder höher**
- **Poetry** (Python Dependency Management)
- **PostgreSQL 17** (läuft als Docker-Container oder lokal)

### 1. Abhängigkeiten installieren

```bash
poetry install
```

### 2. PostgreSQL-Datenbank starten

Das Projekt benötigt eine PostgreSQL-Datenbank. Der empfohlene Weg ist die Verwendung des Docker-Containers aus dem Projekt:

```bash
# Navigiere zum PostgreSQL-Verzeichnis
cd ../../infrastructure/postgres

# Starte PostgreSQL-Container
docker compose up -d

# Container-Logs ansehen
docker compose logs -f postgres

# Container stoppen
docker compose down
```

**Standard-Zugangsdaten** (aus `infrastructure/postgres/docker-compose.yaml`):
- **Host:** `localhost:5432`
- **User:** `admin`
- **Passwort:** `secure_password`
- **Datenbank:** `backend`

### 3. Umgebungsvariablen konfigurieren

Erstelle eine `.env`-Datei basierend auf der Vorlage:

```bash
cp .env.example .env
```

**Wichtige Umgebungsvariablen** (in `.env`):

| Variable | Beschreibung | Standardwert |
|----------|--------------|--------------|
| `DATABASE_URL` | PostgreSQL-Verbindungs-URL im Format: `postgresql+asyncpg://user:password@host:port/database` | `postgresql+asyncpg://admin:secure_password@localhost:5432/backend` |
| `DEBUG` | Debug-Modus aktivieren | `false` |
| `ECHO_SQL` | SQL-Queries in der Konsole ausgeben (nützlich für Debugging) | `false` |

**Beispiel `.env`:**
```env
# Application Settings
DEBUG=false

# Database Configuration
DATABASE_URL=postgresql+asyncpg://admin:secure_password@localhost:5432/backend
ECHO_SQL=false
```

**Hinweis:** Die `DATABASE_URL` muss das `postgresql+asyncpg://`-Schema verwenden, da das Backend asynchrone SQLAlchemy-Treiber nutzt.

### 4. Datenbank initialisieren

Nach der Konfiguration muss die Datenbank-Schema erstellt werden (siehe [Datenbank-Migrationen](#datenbank-migrationen-mit-alembic)).

### 5. Pre-commit Hooks installieren (Empfohlen)

Pre-commit Hooks sorgen dafür, dass der Code automatisch bei jedem Commit formatiert wird:

```bash
poetry run pre-commit install
```

**Wichtig:** Jeder Entwickler muss diesen Befehl nach dem Klonen des Repositories **einmalig** ausführen, damit die Hooks lokal aktiviert werden!

---

## Server Starten

### Entwicklungsserver mit Auto-Reload starten

```bash
poetry run uvicorn app.main:app --reload
```

Der Server läuft standardmäßig auf **`http://localhost:8000`**

- **API-Dokumentation (Swagger UI):** `http://localhost:8000/docs`
- **Alternative API-Dokumentation (ReDoc):** `http://localhost:8000/redoc`

### Optionale Parameter

```bash
# Custom Host und Port
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Ohne Auto-Reload (für Produktion)
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Code-Formatierung

Das Projekt verwendet **Black** und **add-trailing-comma** für konsistente Code-Formatierung.

### Code formatieren

```bash
poetry run poe format
```

### Automatische Formatierung bei Git Commit

Wenn Pre-commit Hooks installiert sind (siehe [Installation](#5-pre-commit-hooks-installieren-empfohlen)), wird der Code automatisch bei jedem `git commit` formatiert.

---

## Datenbank-Migrationen mit Alembic

Das Projekt verwendet **Alembic** für Datenbank-Schema-Migrationen. Alembic erkennt Änderungen an SQLAlchemy-Modellen automatisch und erstellt entsprechende Migrations-Skripte.

### Schritt-für-Schritt-Anleitung

#### 1. Neue Migration erstellen (nach Model-Änderungen)

Wenn du ein neues SQLAlchemy-Model hinzufügst oder ein bestehendes änderst:

**a) Model in `app/modules/<modul>/models.py` definieren**

Beispiel:
```python
from app.core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
import uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email_hash: Mapped[str] = mapped_column(unique=True, index=True)
```

**b) Model in `app/models/__init__.py` importieren**

Damit Alembic das Model erkennt, muss es in `app/models/__init__.py` importiert werden:

```python
from app.modules.auth.models import User

__all__ = ["User"]
```

**c) Migration automatisch generieren**

```bash
poetry run alembic revision --autogenerate -m "Beschreibung der Änderung"
```

Beispiel:
```bash
poetry run alembic revision --autogenerate -m "Add user table"
```

**d) Generierte Migration überprüfen**

Die Migration wird in `app/alembic/versions/` erstellt (z.B. `d2bf9d1c6cf0_add_user_table.py`).

**Wichtig:** Überprüfe die generierte Datei, um sicherzustellen, dass Alembic die Änderungen korrekt erkannt hat!

#### 2. Migration anwenden

```bash
poetry run alembic upgrade head
```

Dieser Befehl wendet alle ausstehenden Migrationen auf die Datenbank an.

#### 3. Migration rückgängig machen

```bash
# Eine Migration zurückrollen
poetry run alembic downgrade -1

# Zu einer bestimmten Revision zurückrollen
poetry run alembic downgrade <revision_id>

# Alle Migrationen rückgängig machen
poetry run alembic downgrade base
```

#### 4. Migrations-Status prüfen

```bash
# Aktuelle Migration anzeigen
poetry run alembic current

# Migrations-Historie anzeigen
poetry run alembic history

# Ausstehende Migrationen anzeigen
poetry run alembic history --verbose
```

### Häufige Alembic-Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `alembic revision --autogenerate -m "message"` | Neue Migration basierend auf Model-Änderungen erstellen |
| `alembic upgrade head` | Alle ausstehenden Migrationen anwenden |
| `alembic downgrade -1` | Letzte Migration rückgängig machen |
| `alembic current` | Aktuelle Migrations-Version anzeigen |
| `alembic history` | Migrations-Historie anzeigen |

### Workflow-Zusammenfassung

1. **Model erstellen/ändern** in `app/modules/<modul>/models.py`
2. **Model importieren** in `app/models/__init__.py`
3. **Migration generieren:** `poetry run alembic revision --autogenerate -m "description"`
4. **Migration überprüfen** in `app/alembic/versions/`
5. **Migration anwenden:** `poetry run alembic upgrade head`

---

## Architektur

### Modularer Monolith

Das Backend folgt einem **Modularen Monolithen**-Ansatz, der die Vorteile von Microservices (klare Modul-Grenzen, unabhängige Entwicklung) mit der Einfachheit eines Monolithen (gemeinsame Datenbank, einfaches Deployment) kombiniert.

**Kernprinzipien:**
- **Domain-Driven Design (DDD):** Das System ist in fachliche Module (Bounded Contexts) unterteilt, die jeweils eine klar abgegrenzte Geschäftsdomäne repräsentieren.
- **Strikte Modulgrenzen:** Jedes Modul ist eigenständig und darf nur über definierte Schnittstellen mit anderen Modulen kommunizieren.
- **Gemeinsame Datenbank:** Alle Module nutzen dieselbe PostgreSQL-Datenbank, aber mit unterschiedlichen Tabellen-Präfixen oder Schemas (zukünftig möglich).
- **Einfaches Deployment:** Ein einzelner Service, der als FastAPI-Anwendung läuft.

### Module & Bounded Contexts

Das Backend ist in vier fachliche Module unterteilt:

| Modul | Bounded Context | Verantwortlichkeiten |
|-------|----------------|----------------------|
| **auth** | Identity & Access Management | Magic-Link-Authentifizierung, Benutzerverwaltung (CRUD), Account-Löschung |
| **quiz** | Content Management | Quiz-Verwaltung, Task-Verwaltung (Multiple Choice, Free Text, Cloze), Ownership-Regeln, Zustandsverwaltung (private/protected/public), LLM-basierte Task-Generierung |
| **learning** | Learning Progress & Evaluation | Übungssessions (Attempts), Antwort-Persistierung, automatische Bewertung, Lernstatistiken |
| **llm** | LLM Infrastructure | LLM-Provider-Abstraktion, Task-Generierung, Free-Text-Bewertung |

**Kommunikationsregeln zwischen Modulen:**
- ✅ `learning` → `quiz` (Read-Only): Learning liest Quiz/Task-Daten
- ✅ `quiz` → `llm`: Quiz nutzt LLM für Task-Generierung
- ✅ `learning` → `llm`: Learning nutzt LLM für Free-Text-Bewertung
- ✅ Alle Module → `auth`: Authentifizierung über `CurrentUserId`-Dependency
- ❌ `quiz` darf NICHT von `learning` abhängen
- ❌ `learning` darf NICHT in `quiz` schreiben (nur lesen!)
- ❌ `auth` darf NICHT von anderen Modulen abhängen

### Layer-Architektur

Jedes Modul folgt einer **3-Layer-Architektur**:

```
app/modules/<modul>/
├── router.py           # API-Layer: HTTP-Endpunkte, Request/Response-DTOs
├── services/           # Business-Logic-Layer: Use-Cases, Orchestrierung
├── repositories/       # Data-Access-Layer: Datenbank-Operationen (CRUD)
├── models/             # ORM-Layer: SQLAlchemy-Modelle
└── schemas/            # DTO-Layer: Pydantic-Request/Response-Schemas
```

**Verantwortlichkeiten der Layer:**

1. **Router (API-Layer):**
   - HTTP-Endpunkte definieren
   - Request/Response-Validierung (Pydantic)
   - Dependency Injection
   - Delegiert an Service-Layer

2. **Service (Business-Logic-Layer):**
   - Geschäftslogik-Orchestrierung
   - Koordiniert mehrere Repositories
   - Ruft andere Module auf (z.B. LLM-Service)
   - Error-Handling
   - **Keine direkten HTTP-Abhängigkeiten**

3. **Repository (Data-Access-Layer):**
   - Reine Datenbank-Operationen (CRUD)
   - SQLAlchemy-Queries
   - **Keine Geschäftslogik**

4. **Models (ORM):**
   - SQLAlchemy-Tabellenstrukturen
   - Relationships

5. **Schemas (DTOs):**
   - Pydantic-Request/Response-DTOs
   - Validierung

---

## Technologie-Stack

- **FastAPI** – Web-Framework
- **SQLAlchemy 2.0** – ORM (async)
- **AsyncPG** – PostgreSQL-Treiber (async)
- **Alembic** – Datenbank-Migrationen
- **Pydantic** – Validierung & Settings
- **PostgreSQL 17** – Datenbank
- **Uvicorn** – ASGI-Server
- **Poetry** – Dependency-Management
- **Python 3.13+** – Erforderliche Version

---

## Implementierungsstatus

**Abgeschlossen:**
- ✅ Projektstruktur mit 4 Modulen (auth, quiz, learning, llm)
- ✅ Core-Module (config, exceptions, database)
- ✅ Database-Session-Management mit `DatabaseSessionManager`
- ✅ Shared-Module (dependencies mit `DBSessionDep`, utils)
- ✅ FastAPI-App mit Router-Registrierung
- ✅ Health-Check-Endpunkte für alle Module
- ✅ Alembic-Konfiguration für async SQLAlchemy
- ✅ Base-Model-Setup mit `Base`-Klasse
- ✅ User-Model und UserRepository (auth-Modul)
- ✅ Erste Alembic-Migration für User-Tabelle

**In Arbeit / TODO:**
- ⏳ Quiz- und Task-Modelle/Services (quiz-Modul)
- ⏳ Attempt- und Answer-Modelle/Services (learning-Modul)
- ⏳ LLM-Provider-Implementierungen (llm-Modul)
- ⏳ Security-Modul (JWT, Hashing) in `app/core/security.py`
- ⏳ Authentication-Dependencies (`CurrentUser`, `CurrentUserId`)
- ⏳ Tests
- ⏳ CI/CD-Pipeline

---

## Weitere Dokumentation

Für detaillierte Entwicklungs-Guidelines, Code-Konventionen und Alembic-Beispiele siehe:
- **CLAUDE.md** – Entwicklungs-Commands, Architektur-Details, Coding-Guidelines

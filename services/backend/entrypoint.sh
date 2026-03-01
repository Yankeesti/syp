#!/bin/bash

# Wartezeit für die Datenbank (einfache Prüfung)
echo "Warte auf PostgreSQL..."
sleep 5

# Alembic Migrationen ausführen
echo "Führe Datenbank-Migrationen aus..."
alembic upgrade head

# Start des FastAPI-Servers
echo "Starte FastAPI Backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
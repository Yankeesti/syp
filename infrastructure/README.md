# Infrastructure

## Lokale Postgres- und pgAdmin-Instanz
Die Compose-Datei unter `infrastructure/postgres/docker-compose.yaml` startet eine Postgres-Datenbank samt pgAdmin-UI. Docker Desktop/Engine muss laufen.

### Dienste starten/stoppen
```bash
# aus dem Repo-Stamm oder direkt aus infrastructure/postgres
docker compose -f infrastructure/postgres/docker-compose.yaml up -d

# Status prüfen / Logs ansehen
docker compose -f infrastructure/postgres/docker-compose.yaml ps
docker compose -f infrastructure/postgres/docker-compose.yaml logs -f postgres

# Dienste beenden und Volumes entfernen
docker compose -f infrastructure/postgres/docker-compose.yaml down -v
```

### Standard-Credentials
| Dienst    | Zugangsdaten |
|-----------|--------------|
| Postgres  | DB: `myapp` · User: `admin` · Passwort: `secure_password`
| pgAdmin UI | E-Mail: `admin@example.com` · Passwort: `pgadmin_password`

**Speicherort der Datenbank**
- Im Container liegen die Daten unter `/var/lib/postgresql/data`.
- Lokal ist das als Docker-Volume `postgres_postgres_data` gespeichert. Mit `docker volume inspect postgres_postgres_data` findest du den Host-Pfad (typisch `/var/lib/docker/volumes/postgres_postgres_data/_data`).
- `docker compose ... down -v` oder `docker volume rm postgres_postgres_data` löschen das Volume inklusive aller Daten – ideal, wenn du den Cluster mit neuen Credentials neu aufsetzen willst.

> Hinweis: Postgres merkt sich das Passwort im Volume `postgres_data`. Wenn du die Variablen in der Compose-Datei änderst, aber das Volume nicht löschst, behält die Datenbank das alte Passwort. In dem Fall mit `docker volume rm <volume-name>` zurücksetzen und neu starten.

### Verbindung über pgAdmin herstellen
1. Öffne `http://localhost:5050` und logge dich mit den pgAdmin-Zugangsdaten ein.
2. Rechtsklick auf **Servers → Register → Server...**
3. Reiter **General**: Name frei wählen (z. B. `Local Postgres`).
4. Reiter **Connection**:
   - `Host name/address`: `postgres` (innerhalb Docker-Netzes) oder `localhost`, wenn du pgAdmin außerhalb des Containers nutzt.
   - `Port`: `5432`
   - `Maintenance database`: `myapp` (oder `postgres`, falls bevorzugt)
   - `Username`: `admin`
   - `Password`: `secure_password` (optional „Save password“ aktivieren)
5. Mit **Save** bestätigen. Unter **Servers → Local Postgres → Databases** solltest du jetzt die Verbindung sehen.

### Troubleshooting
- **Password authentication failed**: Prüfe, ob das gespeicherte Passwort in pgAdmin mit `docker compose exec postgres env | grep POSTGRES_` übereinstimmt. Bei Bedarf Volume löschen (siehe oben) oder das Passwort im Container per `psql` ändern.
- **Keine Verbindung**: Stelle sicher, dass die Container laufen (`docker compose ... ps`) und Port 5432/5050 nicht durch andere Prozesse blockiert werden.

Diese README beschreibt nur den Datenbank-Stack. Für den gesamten Full-Stack siehe die Projekt-README im Repo-Stamm.

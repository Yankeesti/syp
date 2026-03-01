# Wir bleiben bei 3.13, da dein Projekt das verlangt
FROM python:3.13-slim

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry 2.1.2 installieren
ENV POETRY_VERSION=2.1.2
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Abhängigkeiten kopieren
COPY pyproject.toml poetry.lock* ./

# FEHLERBEHEBUNG:
# In Poetry 2.x heißt der Befehl zum reinen Synchronisieren der Lock-Datei einfach nur 'poetry lock'.
# Da wir im Container sind, ist es egal, wenn er die Datei kurz neu schreibt –
# er nutzt danach sofort 'install'.
RUN poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --no-interaction --no-ansi --no-root

# Quellcode kopieren
COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
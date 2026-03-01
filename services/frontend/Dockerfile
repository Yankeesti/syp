FROM node:20-slim

WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY package*.json ./
RUN npm install

# Restlichen Code kopieren
COPY . .

# Wir fügen die Vite-Binaries zum PATH hinzu, damit wir 'vite' direkt aufrufen können
ENV PATH /app/node_modules/.bin:$PATH

# Port für das Frontend
EXPOSE 5173

# --port 3000 stellt sicher, dass es wirklich dieser Port ist
# --no-open verhindert den xdg-open Fehler
CMD ["vite", "--host", "0.0.0.0", "--port", "3000", "--no-open"]
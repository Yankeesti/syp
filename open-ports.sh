#!/bin/bash

set -e

echo "Öffne Ports 3000 und 8000 in UFW..."

sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp

echo "Ports erfolgreich geöffnet."
sudo ufw status

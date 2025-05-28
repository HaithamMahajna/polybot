#!/bin/bash

# Stop on any error
set -e

echo "Starting deployment..."


if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Stop existing server if running
pkill -f "uvicorn" || true

sudo systemctl daemon-reload
sudo systemctl restart polybot.service
sudo systemctl enable polybot.service
sudo systemctl status polybot.service --no-pager

if ! systemctl is-active --quiet polybot.service; then
  echo "❌ polybot.service is not running."
  sudo systemctl status polybot.service --no-pager
  exit 1
fi



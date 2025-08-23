#!/bin/bash

echo "Starting GDG News Bot..."
echo

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it with your Discord token and channel ID."
    echo
    exit 1
fi

# Activate virtual environment and run the bot
if [ -d ".venv" ]; then
    source .venv/bin/activate
    python bot.py
else
    echo "Error: Virtual environment not found!"
    echo "Please run: python -m venv .venv"
    echo "Then: source .venv/bin/activate"
    echo "Then: pip install -r requirements.txt"
    echo
    exit 1
fi

#!/bin/bash

# Activate Python virtual environment
source mltbenv/bin/activate

# Run any update/preparation code required before bot starts
python3 update.py

# Start Flask app with Gunicorn in background on port 8080 with 2 workers
gunicorn app:app --workers 2 --bind 0.0.0.0:8080 --timeout 120 &

# Start your Telegram bot in foreground (replace 'bot' with your actual bot module/package if different)
python3 -m bot

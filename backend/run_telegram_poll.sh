#!/bin/bash
# Run the Telegram poll script with the venv's Python (no activation needed)
cd "$(dirname "$0")"
./venv/bin/python telegram_poll.py

#!/usr/bin/env python3
"""
Local testing: run the Telegram bot via long polling (no webhook needed).
Use this when testing on localhost — Telegram webhooks require a public HTTPS URL.

Usage:
  cd backend
  # Ensure backend has run at least once (uvicorn main:app) so DB exists
  ./run_telegram_poll.sh

  # Or: ./venv/bin/python telegram_poll.py

Then message your bot on Telegram. Press Ctrl+C to stop.
"""

import asyncio
import os
import sys

# Load env before importing routers
from dotenv import load_dotenv
load_dotenv()

if not os.getenv("TELEGRAM_BOT_TOKEN"):
    print("Error: TELEGRAM_BOT_TOKEN not set in backend/.env")
    sys.exit(1)

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from routers.telegram import process_update, TELEGRAM_BOT_TOKEN


async def poll():
    """Long-poll Telegram for updates and process them."""
    base = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    # Remove webhook so getUpdates works (webhook and polling are mutually exclusive)
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.get(f"{base}/deleteWebhook")

    url = f"{base}/getUpdates"
    offset = 0

    print("Mojify Telegram bot — polling for messages...")
    print("Message your bot on Telegram. Press Ctrl+C to stop.\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                r = await client.get(url, params={"offset": offset, "timeout": 30})
                data = r.json()
                if not data.get("ok"):
                    print(f"Telegram API error: {data}")
                    await asyncio.sleep(5)
                    continue

                for upd in data.get("result", []):
                    offset = upd["update_id"] + 1
                    await process_update(upd)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)


async def main():
    # Try to init DB (creates tables if needed). Skip if locked (e.g. backend running).
    try:
        from core.database import init_db
        await init_db()
    except Exception as e:
        if "locked" in str(e).lower() or "database" in str(e).lower():
            print("(DB in use by another process, continuing...)")
        else:
            raise
    await poll()


if __name__ == "__main__":
    asyncio.run(main())

# 🤖 OSINT Bot (API + Local)

A Telegram bot for phone number lookups using external API with local database fallback.

## Features
- 🔍 Search phone numbers via external API
- 📁 Local database fallback
- 📤 Add/delete records locally
- 📊 Database statistics
- 🐛 Debug mode for troubleshooting

## Commands
- `/start` — Show menu
- `/search 9876543210` — Lookup number
- `/debug 9876543210` — Show raw API response
- `/add` — Add local data
- `/stats` — Show database stats

## Deployment (Render Web Service)
1. Push this repo to GitHub
2. Go to Render.com → New Web Service
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`
5. Add Environment Variable: `BOT_TOKEN`
6. Deploy

## Environment Variables
- `BOT_TOKEN` — Your Telegram bot token
- `PORT` — (optional) Port for health check

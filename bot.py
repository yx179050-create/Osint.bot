import json
import os
import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from aiohttp import web

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "8836862263:AAGfdDIAUsbsGwXQgCjx5b0QN0-gIb6m_wQ")
DATA_FILE = "data.json"
API_BASE = "https://bronx-web-api.onrender.com/api/key-bronx/number?key=happy&num=9876543210"
PORT = int(os.getenv("PORT", 8080))
# ===================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

async def search_api(number: str):
    """Search number using external API with timeout and error handling"""
    url = API_BASE.format(number)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    raw = await response.text()
                    try:
                        return json.loads(raw)
                    except json.JSONDecodeError:
                        return {"status": False, "error": "Invalid JSON response", "raw": raw}
                else:
                    return {"status": False, "error": f"HTTP {response.status}"}
        except asyncio.TimeoutError:
            return {"status": False, "error": "Request timeout"}
        except Exception as e:
            return {"status": False, "error": str(e)}

def format_api_results(data: dict) -> str:
    """Format API results for display"""
    # Debug: if raw response is present
    if data.get("raw"):
        return f"⚠️ **Debug - Raw API Response:**\n```json\n{data['raw'][:3000]}\n```"
    
    if not data.get('status'):
        return f"❌ API Error: {data.get('error', 'Unknown error')}"
    
    records = data.get('data', [])
    if not records:
        return "❌ No records found for this number."
    
    result = f"🔍 **Phone Lookup Results** ({len(records)} records)\n\n"
    for i, record in enumerate(records, 1):
        result += f"**Record {i}:**\n"
        result += f"📱 Number: `{record.get('mobile', 'N/A')}`\n"
        result += f"👤 Name: {record.get('name', 'N/A')}\n"
        result += f"👨 Father: {record.get('father_name', 'N/A')}\n"
        result += f"📍 Address: {record.get('address', 'N/A')}\n"
        result += f"📞 Alt: {record.get('alt_number', 'N/A')}\n"
        result += f"📧 Email: {record.get('email', 'N/A')}\n"
        result += f"📶 Circle: {record.get('circle', 'N/A')}\n\n"
    return result

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Search Number", callback_data="search")],
        [InlineKeyboardButton("📤 Add Local Data", callback_data="add")],
        [InlineKeyboardButton("📊 Stats", callback_data="stats")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 **OSINT Bot v2 (API + Local)**\n\n"
        "🔹 Searches via external API\n"
        "🔹 Falls back to local database\n"
        "🔹 Private & secure\n\n"
        "📌 `/search 9876543210` — Search number\n"
        "📌 `/debug 9876543210` — Raw API response\n"
        "📌 `/add` — Add local data\n"
        "📌 `/stats` — Database stats",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "search":
        await query.edit_message_text(
            "📱 Send the **phone number**:\nExample: `9876543210`",
            parse_mode="Markdown"
        )
        context.user_data['mode'] = 'search'
    
    elif query.data == "add":
        await query.edit_message_text(
            "📤 Send data in format:\n`number|name|father|address|alt|email|circle`\n"
            "Example: `9876543210|John Doe|James Doe|123 Street|9876543211|john@email.com|AIRTEL`",
            parse_mode="Markdown"
        )
        context.user_data['mode'] = 'add'
    
    elif query.data == "stats":
        data = load_data()
        await query.edit_message_text(
            f"📊 **Database Stats**\n\nTotal entries: `{len(data)}`",
            parse_mode="Markdown"
        )
    
    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ **HELP**\n\n"
            "/start — Show menu\n"
            "/search `<number>` — Lookup number\n"
            "/debug `<number>` — Show raw API response\n"
            "/add — Add local data\n"
            "/stats — Show database stats",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode', 'search')
    text = update.message.text.strip()
    
    if mode == 'search':
        loading_msg = await update.message.reply_text("⏳ Searching...")
        
        api_result = await search_api(text)
        if api_result and api_result.get('status'):
            formatted = format_api_results(api_result)
            await loading_msg.delete()
            if len(formatted) > 4000:
                for i in range(0, len(formatted), 4000):
                    await update.message.reply_text(formatted[i:i+4000], parse_mode="Markdown")
            else:
                await update.message.reply_text(formatted, parse_mode="Markdown")
            return
        
        # Fallback to local database
        data = load_data()
        if text in data:
            record = data[text]
            result = f"📁 **Local Database Result**\n\n"
            result += f"📱 Number: `{text}`\n"
            result += f"👤 Name: {record.get('name', 'N/A')}\n"
            result += f"👨 Father: {record.get('father_name', 'N/A')}\n"
            result += f"📍 Address: {record.get('address', 'N/A')}\n"
            result += f"📞 Alt: {record.get('alt_number', 'N/A')}\n"
            result += f"📧 Email: {record.get('email', 'N/A')}\n"
            result += f"📶 Circle: {record.get('circle', 'N/A')}\n"
            await loading_msg.delete()
            await update.message.reply_text(result, parse_mode="Markdown")
        else:
            await loading_msg.delete()
            await update.message.reply_text("❌ Number not found in API or local database.")
    
    elif mode == 'add':
        parts = text.split('|')
        if len(parts) >= 3:
            data = load_data()
            data[parts[0]] = {
                'name': parts[1] if len(parts) > 1 else 'N/A',
                'father_name': parts[2] if len(parts) > 2 else 'N/A',
                'address': parts[3] if len(parts) > 3 else 'N/A',
                'alt_number': parts[4] if len(parts) > 4 else 'N/A',
                'email': parts[5] if len(parts) > 5 else 'N/A',
                'circle': parts[6] if len(parts) > 6 else 'N/A'
            }
            save_data(data)
            await update.message.reply_text(f"✅ Data added for `{parts[0]}`", parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "❌ Invalid format. Use:\n`number|name|father|address|alt|email|circle`",
                parse_mode="Markdown"
            )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        number = context.args[0]
        context.user_data['mode'] = 'search'
        await handle_message(update, context)
    else:
        await update.message.reply_text("📱 Usage: `/search 9876543210`", parse_mode="Markdown")
        context.user_data['mode'] = 'search'

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to show raw API response"""
    if not context.args:
        await update.message.reply_text("📱 Usage: `/debug 9876543210`", parse_mode="Markdown")
        return
    
    number = context.args[0]
    loading_msg = await update.message.reply_text(f"⏳ Fetching debug info for `{number}`...", parse_mode="Markdown")
    
    api_result = await search_api(number)
    
    result = f"🔍 **Debug Info for `{number}`**\n\n"
    result += f"**API Response:**\n```json\n{json.dumps(api_result, indent=2, ensure_ascii=False)[:3000]}\n```"
    
    await loading_msg.delete()
    await update.message.reply_text(result, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(f"📊 **Database Stats**\n\nTotal entries: `{len(data)}`", parse_mode="Markdown")

# ====== WEBHOOK + POLLING HYBRID ======
async def health_check(request):
    return web.Response(text="🤖 OSINT Bot is running!")

async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("debug", debug_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    while True:
        await asyncio.sleep(3600)

async def main():
    web_app = web.Application()
    web_app.router.add_get('/', health_check)
    web_app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    print(f"✅ Health check running on port {PORT}")
    print("🤖 OSINT Bot (API + Local) is running...")
    
    await run_bot()

if __name__ == "__main__":
    asyncio.run(main())

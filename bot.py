import json
import os
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "8836862263:AAGfdDIAUsbsGwXQgCjx5b0QN0-gIb6m_wQ")
DATA_FILE = "data.json"
API_BASE = "https://number-info-api-geniushacker29.vercel.app/api/lookup?number={}"
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
    url = API_BASE.format(number)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except:
            return None

def format_api_results(data: dict) -> str:
    if not data or not data.get('status'):
        return "❌ API returned error or no data."
    
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
        [InlineKeyboardButton("📤 Add Data", callback_data="add")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🤖 **OSINT Bot v2 (API + Local)**\n\n"
        "• Searches via external API\n"
        "• Falls back to local database\n"
        "• Private & secure",
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
            "📤 Send data in format:\n`number|name|father|address|alt|email|circle`",
            parse_mode="Markdown"
        )
        context.user_data['mode'] = 'add'
    
    elif query.data == "help":
        await query.edit_message_text(
            "ℹ️ **HELP**\n\n"
            "/start - Show menu\n"
            "/search <number> - Lookup number\n"
            "/add - Add local data\n"
            "/stats - Show database stats",
            parse_mode="Markdown"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get('mode', 'search')
    text = update.message.text.strip()
    
    if mode == 'search':
        api_result = await search_api(text)
        if api_result and api_result.get('status'):
            formatted = format_api_results(api_result)
            if len(formatted) > 4000:
                for i in range(0, len(formatted), 4000):
                    await update.message.reply_text(formatted[i:i+4000], parse_mode="Markdown")
            else:
                await update.message.reply_text(formatted, parse_mode="Markdown")
            return
        
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
            await update.message.reply_text(result, parse_mode="Markdown")
        else:
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
            await update.message.reply_text(f"✅ Data added for {parts[0]}")
        else:
            await update.message.reply_text("❌ Invalid format. Use: `number|name|father|address|alt|email|circle`")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        number = context.args[0]
        context.user_data['mode'] = 'search'
        await handle_message(update, context)
    else:
        await update.message.reply_text("📱 Usage: `/search 9876543210`", parse_mode="Markdown")
        context.user_data['mode'] = 'search'

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(f"📊 **Database Stats**\n\nTotal entries: `{len(data)}`")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 OSINT Bot (API + Local) is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

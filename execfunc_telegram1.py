from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
from telegram import Bot
import os
from kasperpylib.redis import send_text_to_redis_channel

TELEGRAM_BOT_KEY = os.getenv('EXECFUNC_DEV1_TELEGRAM_TOKEN')
TARGET_CHAT_ID = 1806003945  # Replace with the target chat_id
print('TELEGRAM_BOT_KEY:', TELEGRAM_BOT_KEY)

import asyncio
from telegram import Bot

async def send_message_async(bot_token, chat_id, message):
    bot = Bot(token=bot_token)
    try:
        await bot.send_message(chat_id=chat_id, text=message)
        print(f"Message sent successfully to chat_id: {chat_id}")
    except Exception as e:
        print(f"Failed to send message: {e}")

def send_message_nonasync(bot_token, chat_id, message):
    asyncio.run(send_message_async(bot_token, chat_id, message))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print('handling msg')
    print(update)
    print(update.message)
    send_text_to_redis_channel('chat_user_text_input', update.message.text)
    await update.message.reply_text("handled msg")

app = ApplicationBuilder().token(TELEGRAM_BOT_KEY).build()

app.add_handler(MessageHandler(filters.TEXT, handle_message))

print('polling...')
app.run_polling(poll_interval=3)
print('end')
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
from telegram import Bot
import os
import redis
import json

TELEGRAM_BOT_KEY = os.environ.get('EXECFUNC_DEV1_TELEGRAM_TOKEN')
TARGET_CHAT_ID = 1806003945  # Replace with the target chat_id

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


# start redis that listens to telegram_outport and parses the json message and uses send_message_nonasync to send the message
# use os.env password
r = redis.Redis(host='localhost', port=6379, password=os.environ.get('REDIS_PASSWORD'))
# use os.env password
pubsub = r.pubsub()
pubsub.subscribe('telegram_outport')
for message in pubsub.listen():
    if message['type'] == 'message':
        print(f"Received message: {message['data']}")
        try:
            data = json.loads(message['data'])
            send_message_nonasync(data['bot_token'], data['chat_id'], data['message'])
        except Exception as e:
            print(f"Error when trying to parse and send message: {e}")

# code for a script that uses this kind of server

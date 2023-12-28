from telethon import TelegramClient, events
from dotenv import load_dotenv
import os
<<<<<<< HEAD
=======
import config

>>>>>>> new-main

load_dotenv()
# Replace these with your own values
api_id = os.getenv('TELEGRAM_ID')
api_hash = os.getenv('TELEGRAM_HASH')
bot_token = os.getenv('TELEGRAM_BOT_KEY')
print(api_hash, api_id, bot_token)
channel_id = -1002011337092  # You can also use the channel ID

# The client will be using the bot token
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

async def send_message_to_channel(channel_id, message):
    await client.send_message(channel_id, message)

# Start the client
with client:
    client.loop.run_until_complete(send_message_to_channel(channel_id, '/last_week!'))
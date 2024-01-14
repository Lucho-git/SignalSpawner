"""Configures Various interconnected components"""
import os
import json
import platform
import pyrebase
import pytz
from binance.client import Client
from dotenv import load_dotenv, find_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession
import munch
# import discord
from discord.ext import commands

# Detect environment
environment = "local" if platform.system() == 'Windows' else "server"
print(f'{environment.capitalize()} Environment Detected...')

load_dotenv(override=True)

# Firebase Configuration
def get_firebase_config():
    with open('config/firebase_config.json', 'r') as file:
        config = json.load(file)
    config['apiKey'] = str(os.getenv("FIREBASE_API"))
    return pyrebase.initialize_app(config)

# Timezone Configuration
def get_timezone_config():
    """Returns consistent timezone"""
    return pytz.timezone('Australia/Perth')

# Binance Client Configuration
def get_binance_config():
    """Gets binance client"""
    r_api_key = os.getenv('LACH_BINANCE_KEY')
    r_api_secret = os.getenv('LACH_BINANCE_SECRET')
    return Client(r_api_key, r_api_secret)

# Telegram Client Configuration
def get_telegram_config():
    """Returns Telegram Client"""
    api_id = os.getenv('TELEGRAM_ID')
    api_hash = os.getenv('TELEGRAM_HASH')
    session_key = 'TELEGRAM_LOCALSAVE' if environment == 'local' else 'TELEGRAM_SERVERSAVE'
    session = StringSession(os.getenv(session_key))

    return TelegramClient(session, api_id, api_hash)

# Discord Client Configuration
def get_discord_config():
    token = os.getenv('DISCORD_TOKEN')
    bot = commands.Bot(command_prefix='!', self_bot=True)
    return bot, token

# Telegram Commands
def get_commands():
    """Returns set of telegram commands"""
    # Stream Commands Local
    with open('config/telegram_commands.json', 'r') as file:
        chat_commands = json.load(file)
    if not environment == 'local':
        # Stream Commands Heroku Hosted
        chat_commands = {key: command + '!' for key, command in chat_commands.items()}
    return munch.munchify(chat_commands)

# Telegram channels
def get_telegram_channels():
    """Returns set of telegram channels"""
    with open('config/telegram_channels.json', 'r') as file:
        telegram_channels = json.load(file)
    return munch.munchify(telegram_channels)

def get_storage_paths():
    """Returns filepaths"""
    UNIQUE_ID = 'heroku/'

    if environment == 'local':
        # Firebase Cloud Storage File Paths
        file_paths = {
        "ADD_MESSAGE": "trade_result/message_count/",
        "SAVE": "save_data/savefile",
        "SAVE_TRADE": "trade_result/",
        "LIVE_VIEW": "live_view/",
        "LOG": 'logs/',
        "REALTIME_SAVE": 'signal/',
        "DISCORD_CHANNEL": 'discord_channel/',
        "TELEGRAM_CHANNEL": 'telegram_channel/',
        "RAW_SIGNALS": 'raw_signals/',
        "SIGNAL_ENDPOINT_URL": 'https://luchodore.pythonanywhere.com/test_data',
        "RESULTS_ENDPOINT_URL": 'https://luchodore.pythonanywhere.com/results_data'
        }
    else:
        # Heroku Version
        file_paths = {
        "ADD_MESSAGE": UNIQUE_ID + "trade_results/message_count/",
        "SAVE": UNIQUE_ID + "save_data/savefile",
        "SAVE_TRADE": UNIQUE_ID + "trade_results/",
        "LIVE_VIEW": UNIQUE_ID + "live_view/",
        "LOG": UNIQUE_ID + 'logs/',
        "REALTIME_SAVE": UNIQUE_ID + 'signals/',
        "DISCORD_CHANNEL": UNIQUE_ID + 'discord_channels/',
        "TELEGRAM_CHANNEL": UNIQUE_ID + 'telegram_channels/',
        "RAW_SIGNALS": UNIQUE_ID + 'raw_signals/',
        "SIGNAL_ENDPOINT_URL": 'https://luchodore.pythonanywhere.com/save_data',
        "RESULTS_ENDPOINT_URL": 'https://luchodore.pythonanywhere.com/test_results_data'
        }
    return munch.munchify(file_paths)

def get_binance_exchange_info():
    with open('docs/binance_exchange_info.txt', 'r', encoding='utf-8') as f:
        data = f.read()
        json_data = json.loads(data)
        symbols_dict = {item['symbol']: item for item in json_data['symbols']}
        return symbols_dict
# 3rd Party libraries

from telethon import events, utils
from dotenv import load_dotenv
import requests
import asyncio
import sys
import time
import os
import traceback
import config
import backtesting
from types import SimpleNamespace


# Local imports

import utility
import handle_signal_message
from config import get_telegram_config, get_commands
import database_logging as db

class TelegramEvents:
    '''Handles telegram events'''
    def __init__(self, clientChannel):
        self.com = config.get_commands()
        self.clientChannel = clientChannel
        self.client = config.get_telegram_config()
        self.lock = asyncio.Lock()
        self.last_message = {
            'text': None,
            'time': 0
        }

    async def exit_self(self):
        '''Polls to see if should disconnect'''
        while True:
            msg = await self.clientChannel[1].get()
            if msg == 'close':
                print('Disconnecting Telebagger...')
                await self.client.disconnect()
                break

    async def generate_message(self, event):
        '''Builds a signal from the telegram event'''
        origin = SimpleNamespace()
        message = SimpleNamespace()
        sender_obj = await event.get_sender()
        chat = await event.get_chat()
        sender = str(chat.id)
        origin.name = utils.get_display_name(sender_obj)
        origin.id = sender
        message.origin, message.message, message.timestamp = origin, event.raw_text, event.date
        return message

    async def get_past_messages(self, channel_id):
        '''Gets past messages from a channel'''
        msgs = await self.client.get_messages(str(channel_id), limit=20)
        if msgs is not None:
            print("Messages:\n---------")
            for msg in msgs:
                print(msg)
                print(msg.chat_id)
                print(msg.signal_message.message)
                print('______________________')
                if not msg.photo:
                    #await self.client.send_message(1576065688, msg)
                    pass
                else:
                    print('has photo')

    async def is_duplicate(self, event):
        message = event.message
        current_time = time.time()
        is_same_text = self.last_message['text'] == message.text
        is_within_timeframe = (current_time - self.last_message['time']) < 1  # 1 second

        if is_same_text and is_within_timeframe:
            chat = await event.get_chat()
            print('Duplicate message from:', chat.id)
            return True

        self.last_message['text'] = message.text
        self.last_message['time'] = current_time
        return False

    async def telegram_command(self, signal_message):
        '''Commands which can be manually triggered through the telegram client'''
        print("Robot Section +++")
        db.gen_log('Telegram Robot: ' + signal_message.message)
        # Bot commands
        if signal_message.message == self.com.STOP:
            print('Disconnecting Telebagger...')
            await self.clientChannel[0].put('close')
            await self.client.disconnect()
        # Stream Commands

        elif signal_message.message == self.com.HIRN_SIGNAL:
            with open('docs/hirn_example.txt', 'r', encoding='utf-8') as f:
                signal_message.message = f.read()
            signal_message.origin.id = '1248393106'
            signal_message.origin.name = 'Hirn'
            await handle_signal_message.process_message(signal_message)

        elif signal_message.message == self.com.RAND_HIRN_SIGNAL:
            signal_message.origin.id = '1248393106'
            signal_message.origin.name = 'randomHirn'
            for m in await self.client.get_messages('https://t.me/HIRN_CRYPTO', limit=20):
                if 'Buy Price:' in m.message:
                    signal_message.message = m.message
                    await handle_signal_message.process_message(signal_message)
                    break

        elif signal_message.message == self.com.PAST:
            await self.get_past_messages('1248393106')

        elif signal_message.message == self.com.EXCEPT:
            raise Exception('Log this exception please')
        
        elif self.com.GET_DB in signal_message.message:
        #/get key
            try:
                data = db.get_from_realtime(signal_message.message.split(self.com.GET_DB)[1])
                for user in data.each():
                    print(f"{user.key()}: {user.val()}")
            except Exception as e:
                print(e)

        elif '/new_disc_channel ' in signal_message.message:
            #Format like  /newchannel guildid-channelid nameofchannel category(ignore/signal)
            channelinfo = signal_message.message.split(' ')
            channel_id_combo, channel_name, channel_category = channelinfo[1], channelinfo[2], channelinfo[3]
            if channel_category not in ['signal', 'ignore']:
                raise Exception('Wrong channel category, should be "signal" or "ignore"')
            db.add_discord_channel(channel_id_combo, channel_name, channel_category)

        elif '/new_tele_channel ' in signal_message.message:
            channelinfo = signal_message.message.split(' ')
            channel_id, channel_name, channel_category = channelinfo[1], channelinfo[2], channelinfo[3]
            if len(channel_id) == 10:
                db.add_telegram_channel(channel_id, channel_name, channel_category)

        elif '/channel_link' in signal_message.message:
            channel_link = signal_message.message.split(' ')[1]
            channel_id = await self.client.get_entity(channel_link)
            print(channel_id)

        elif signal_message.message == self.com.PREDICTUM:
            with open('docs/predictum_example.txt', 'r', encoding='utf-8') as f:
                signal_message.message = f.read()
            signal_message.origin.id = '1558766055'
            signal_message.origin.name = 'lastPredictum'
            await handle_signal_message.process_message(signal_message)

        elif signal_message.message == self.com.GGSHOT:
            with open('docs/ggshot_example.txt', 'r', encoding='utf-8') as f:
                signal_message.message = f.read()
            signal_message.origin.id = '1825288627'
            signal_message.origin.name = 'testGGshot'
            await handle_signal_message.process_message(signal_message)

        elif signal_message.message == self.com.GGSHOTVIP:
            with open('docs/ggshotvip_example.txt', 'r', encoding='utf-8') as f:
                signal_message.message = f.read()
            signal_message.origin.id = '1737189058'
            signal_message.origin.name = 'testGGshotVip'
            await handle_signal_message.process_message(signal_message)

        elif signal_message.message == self.com.LAST_WEEK:
            print('getting last week of signals')
            signals = db.generate_signals_from_timeframe(days = 7)
            db.generate_trades(signals)
            db.backtest_trades(signals)
            db.post_trades(signals)
            # db.save_signals(signals)

        elif signal_message.message == self.com.CHANGE_VALUE:
            print('changing value')
            db.change_database_value()   

        elif signal_message.message == self.com.BACK_TEST:
            signals = db.get_old_signals()
            for s in signals:
                backtesting.run_backtest_from_signal(s)

        elif signal_message.message == self.com.GET_SIGNALS:
            db.get_old_signals()

    async def start_telegram_handler(self, client):
        '''telegram message event handler'''
        '''Receive message logic!!!'''
        @client.on(events.NewMessage())
        async def my_event_handler(event):
            async with self.lock:
                if await self.is_duplicate(event):
                    return
            try:
                signal_message = await self.generate_message(event)

                if signal_message.origin.id in self.com.SIGNAL_GROUP:
                    print('From Signal Group:', signal_message.origin.name)
                    await handle_signal_message.process_message(signal_message)

                elif signal_message.origin.id == '5894740183' or signal_message.origin.id == '5935711140':
                    await self.telegram_command(signal_message)
                elif signal_message.origin.id in self.com.GENERAL_GROUP:
                    pass

                else:
                    print('new chat ID:', signal_message.origin.id, signal_message.origin.name)
                    db.gen_log('new chat ID:' + str(signal_message.origin.id) + signal_message.origin.name + 'Didnt match: ' + str(self.com.SIGNAL_GROUP))
                    #Deal with unrecognized telegram channels

            except Exception as e:
                db.error_log(str(e) + '\nMessage:' + event.raw_text + '\nExcept:' + str(traceback.format_exc()))

    async def run(self):
        '''Start recieving telegram events'''
        await self.start_telegram_handler(self.client)
        db.gen_log('Launching Telegram Scraper...')
        await self.client.start()
        print('Ready...')
        await self.client.run_until_disconnected()
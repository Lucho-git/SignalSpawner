# 3rd Party libraries

from telethon import events, utils
from dotenv import load_dotenv
import json
import requests
import asyncio
import sys
import time
import os
import traceback
import config
import backtesting
import collections
from types import SimpleNamespace
from threading import Lock
from collections import defaultdict

# Local imports

import utility
import handle_signal_message
import database_logging as db


class TelegramEvents:
    '''Handles telegram events'''
    def __init__(self, clientChannel):
        self.com = config.get_commands()
        self.channels = config.get_telegram_channels()
        self.clientChannel = clientChannel
        self.client = config.get_telegram_config()
        self.lock = asyncio.Lock()
        self.last_messages = defaultdict(list)

    async def get(self, source_id):
        async with self.lock:
            return self.last_messages[source_id]

    async def set(self, source_id, message_content):
        async with self.lock:
            if len(self.last_messages[source_id]) >= 2:  # if there are 2 or more messages
                self.last_messages[source_id].pop(0)  # remove the oldest message
            self.last_messages[source_id].append(message_content) # add new message

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

    def is_signal_in_group(self, signal_message):
        if any(signal_message.origin.id == channel['id'] for channel in self.channels['signal_groups']):
            return 'SIGNAL_GROUP'
        if any(signal_message.origin.id == channel['id'] for channel in self.channels['general_groups']):
            return 'GENERAL_GROUP'
        if any(signal_message.origin.id == channel['id'] for channel in self.channels['bot_groups']):
            return 'BOT_GROUP'
        else:
            return None


    async def update_true_id(self):
        # Retrieve all dialogs
        dialogs = await self.client.get_dialogs()

        # Load channel data from JSON file
        with open('config/telegram_channels.json', 'r') as file:
            channels = json.load(file)



        # Check for matching IDs and update trueId
        updated = False
        for group in channels.values():
            for channel in group:
                if not 'trueId' in channel:
                    for dialog in dialogs:
                        if str(dialog.entity.id) == channel['id']:
                            print('Found a trueId for channel', dialog.name)
                            channel['trueId'] = dialog.id
                            channel['telegram_name'] = dialog.name
                            updated = True
                            break

        # Save updated data back to JSON file if there was an update
        if updated:
            with open('config/telegram_channels.json', 'w') as file:
                json.dump(channels, file, indent=4)

    def shared_chars(self, str1, str2):
        counter1 = collections.Counter(str1)
        counter2 = collections.Counter(str2)
        # Subtract the counters
        remaining1 = counter1 - counter2
        remaining2 = counter2 - counter1
        # Join the remaining characters to form strings
        str1_remaining = ''.join([char * count for char, count in remaining1.items()])
        str2_remaining = ''.join([char * count for char, count in remaining2.items()])
        combined_remaining = str1_remaining + str2_remaining
        max_len = max(len(str1), len(str2))
        if not max_len > 0:
            return 0
        shared = ((max_len - len(combined_remaining))/max_len) *100
        return shared


    async def is_duplicate(self, source_id, message_content):
        # Check if message is duplicate
        last_messages = await self.get(source_id)
        for last_message in last_messages:
            similarity = self.shared_chars(last_message, message_content)
            if similarity > 95:
                print('Very Similar')
                print(similarity)
                db.realtime_signal_logs('Duplicate Message:' + str(source_id) + '|\n' + message_content + '|\n' + last_message+'\n')
                print(f"Ignoring duplicate message from {source_id}")
                return True

        # Update the latest message from this source
        db.realtime_signal_logs('Not a Duplicate Message:' + str(source_id) + '|\n' + message_content + '|\n' + str(last_messages)+'\n')
        await self.set(source_id, message_content)    
        # If it reaches here, the new message is not similar to any of the last two messages.
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
            await self.handle_new_message(signal_message)

        elif signal_message.message == self.com.RAND_HIRN_SIGNAL:
            signal_message.origin.id = '1248393106'
            signal_message.origin.name = 'randomHirn'
            for m in await self.client.get_messages('https://t.me/HIRN_CRYPTO', limit=20):
                if 'Buy Price:' in m.message:
                    signal_message.message = m.message
                    await self.handle_new_message(signal_message)
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

        elif signal_message.message == self.com.DELETE_DUPLICATES:
            db.delete_database_duplicates()
        elif signal_message.message == self.com.DELETE_NEAR_DUPLICATES:
            print('deleting near dups...')
            db.delete_database_almost_duplicates()
        elif '/new_disc_channel ' in signal_message.message:
            #Format like  /newchannel guildid-channelid nameofchannel category(ignore/signal)
            channelinfo = signal_message.message.split(' ')
            channel_id_combo, channel_name, channel_category = channelinfo[1], channelinfo[2], channelinfo[3]
            if channel_category not in ['signal', 'ignore']:
                raise Exception('Wrong channel category, should be "signal" or "ignore"')
            db.add_discord_channel(channel_id_combo, channel_name, channel_category)

        elif '/get_dialogs' in signal_message.message:
                    for dialog in await self.client.get_dialogs():
                        print(f"Found channel with ID: {dialog.id, dialog.name}")
                        entity = await self.client.get_entity(dialog.id)
                        print(entity)


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
            signal_message.origin.name = 'examplePredictum'
            await self.handle_new_message(signal_message)

        elif signal_message.message == self.com.PREDICTUM2:
            with open('docs/predictum2_example.txt', 'r', encoding='utf-8') as f:
                signal_message.message = f.read()
            signal_message.origin.id = '1558766055'
            signal_message.origin.name = 'examplePredictum2'
            await self.handle_new_message(signal_message)


        elif signal_message.message == self.com.GGSHOT:
            with open('docs/ggshot_example.txt', 'r', encoding='utf-8') as f:
                signal_message.message = f.read()
            signal_message.origin.id = '1480838869'
            signal_message.origin.name = 'testGGshotLeaked'
            await handle_signal_message.process_message(signal_message)

        elif signal_message.message == self.com.GGSHOTVIP:
            with open('docs/ggshotvip_example.txt', 'r', encoding='utf-8') as f:
                signal_message.message = f.read()
            signal_message.origin.id = '1737189058'
            signal_message.origin.name = 'testGGshotVip'
            await handle_signal_message.process_message(signal_message)

        elif signal_message.message == self.com.UPDATE:
            print('getting last week of signals')
            signals = db.generate_signals_from_timeframe(days = 200)
            db.generate_trades(signals)
            db.backtest_trades(signals)
            db.post_trades(signals)
            db.save_signals(signals)

        elif signal_message.message == self.com.LAST_WEEK:
            print('getting last week of signals')
            signals = db.generate_signals_from_timeframe(days = 7)
            db.generate_trades(signals, True)
            print('Generated all the trades\n\n')
            print('Backtesting....')
            db.backtest_trades(signals)
            print('Backtested all the trades\n\n')
            print('Posting...')
            db.post_trades(signals)
            print('Posted all the trades')
            print('Saving....')
            db.save_signals(signals)
            print('Saved all the trades\n\n')

        elif signal_message.message == self.com.NEW_WEEK:
            print('getting last week of signals')
            signals = db.generate_signals_from_timeframe(days = 7)
            db.generate_trades(signals)
            db.backtest_trades(signals)
            db.post_trades(signals)
            db.save_signals(signals)

        elif signal_message.message == self.com.UPDATE_HISTORY:
            signals = db.generate_signals_from_timeframe(days = 200)
            db.generate_trades(signals, True)
            print('\n\n\nGenerated new trade history:', signals,'\n\n\n')
            db.backtest_trades(signals)
            db.post_trades(signals)
            db.save_signals(signals)

        elif signal_message.message == self.com.CHANGE_VALUE:
            print('changing value')
            db.change_database_value()   

        elif signal_message.message == self.com.BACK_TEST:
            signals = db.generate_signals_from_timeframe(days = 90)
            db.backtest_signals(signals)
            db.post_backtest_results(signals)
            #db.save_signals(signals)

        elif signal_message.message == self.com.DEEP_BACK_TEST:
            signals = db.generate_signals_from_timeframe(days = 90)
            db.deep_backtest_signals(signals)
            db.save_signals(signals)


        elif signal_message.message == self.com.GET_SIGNALS:
            db.get_old_signals()

        elif signal_message.message == self.com.KNOWN_CHANNELS:
            i = 0
            for group in self.channels.values():
                for channel in group:  
                    i += 1
                    print(f"ID: {channel.id}, Name: {channel.telegram_name}")
            print(f"Known Channels: {i}")
                    

        elif signal_message.message == self.com.TRUE_ID:
            await self.update_true_id()


    async def start_telegram_handler(self, client):
        '''telegram message event handler'''
        '''Receive message logic!!!'''
        async def handle_new_telegram_event(event):
            #Coverts the actual telegram event object into a message object and sends it for processing
            try:
                signal_message = await self.generate_message(event)
                await self.handle_new_message(signal_message)
            except Exception as e:
                db.error_log(str(e) + '\nMessage:' + event.raw_text + '\nExcept:' + str(traceback.format_exc()))


        @client.on(events.NewMessage())
        #Sends telegram events to be processed
        async def my_event_handler(event):
            await handle_new_telegram_event(event)


    async def run(self):
        '''Start recieving telegram events'''
        await self.start_telegram_handler(self.client)
        db.gen_log('Launching Telegram Scraper...')
        await self.client.start()
        print('Ready...')
        await self.client.run_until_disconnected()

    def update_telegram_channels(self, new_channel):
        with open('config/telegram_channels.json', 'r') as file:
            data = json.load(file)

        # Append the new channel to general_groups
        data['general_groups'].append(new_channel)

        # Save the updated data back to the file
        with open('config/telegram_channels.json', 'w') as file:
            json.dump(data, file, indent=4)

    async def handle_new_message(self, signal_message):
        #Handles the logic for new messages
        channel_type = self.is_signal_in_group(signal_message)
        if channel_type == 'SIGNAL_GROUP':
            properties = [f'{name}: {getattr(signal_message, name)}' for name in dir(signal_message) if not name.startswith('__')]
            properties_string = '\n'.join(properties)
            logs = 'New Signal Message:' + properties_string
            db.realtime_signal_logs(logs)
            print('From Signal Group:', signal_message.origin.name)
            if await self.is_duplicate(signal_message.origin.id, signal_message.message):
                return
            await handle_signal_message.process_message(signal_message)

        elif channel_type == 'GENERAL_GROUP':
            pass

        elif channel_type == 'BOT_GROUP':
            await self.telegram_command(signal_message)

        else:
            print('new chat ID:', signal_message.origin.id, signal_message.origin.name)
            db.gen_log('new chat ID:' + str(signal_message.origin.id) + signal_message.origin.name + 'Didnt match: anything' )
            #Deal with unrecognized telegram channels
            new_channel = {
                "id": signal_message.origin.id,
                "telegram_name": signal_message.origin.name,
                "local_name": signal_message.origin.name  # Using telegram_name as placeholder
            }
            self.update_telegram_channels(new_channel)
            self.channels = config.get_telegram_channels()
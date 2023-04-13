from dotenv import load_dotenv
import config
from types import SimpleNamespace

import utility
import new_signal
from config import get_telegram_config, get_commands
import database_logging as db
import os
import discord
from discord.ext import commands
import asyncio


class DiscordEvents:
    '''Handles discord events'''
    def __init__(self, clientChannel):
        self.com = config.get_commands()
        self.channels = db.get_discord_channels()
        self.clientChannel = clientChannel
        self.client, self.key = config.get_discord_config()

    async def exit_self(self):
        '''Polls to see if should disconnect'''
        while True:
            # Check the queue for messages
            msg = await self.clientChannel[0].get()
            if msg == 'close':
                print('Disconnecting Discbagger...')
                await self.client.close()
                break
            await asyncio.sleep(1)

    async def start_discord_handler(self, client):
        '''discord message event handler'''
        @client.command()
        async def ping(ctx):
            print('Sending Ping')
            await ctx.send('pong')
        
        @client.event
        async def on_message(message):

            if message.channel.id == 1064541939640324137:
                print('Discord Robot ++')
                await self.telegram_command(message)

            elif message.author == client.user:
                return
            
            elif (message.guild):
                guid = str(message.guild.id)
                chuid = str(message.channel.id)
                if not guid in self.channels:
                    combined_id = guid + '-' + chuid
                    db.add_discord_channel(combined_id, message.channel.name, 'ignore')
                    self.channels = db.get_discord_channels()
                else:
                    id_found = any(item['channel_id'] == chuid for item in list(self.channels[guid].values())[:])
                    if (id_found):
                        if (self.channels[guid][chuid]['type'] == 'signal'):
                            print('New signal')
                            print(message)
                            print(message.content)
                    else:
                        print('No channel found in ')
                        print('Adding new channel: ', message)
                        combined_id = guid + '-' + chuid
                        db.add_discord_channel(combined_id, message.channel.name, 'ignore')
                        self.channels = db.get_discord_channels()
            else:
                print('No guild id')


        # async def my_event_handler(event):
        #     try:
        #         signal = await self.generate_signal(event)

        #         if signal.origin.id in self.com.SIGNAL_GROUPS:
        #             await new_signal.new_signal(signal)

        #         elif signal.origin.id == '5963551324' or signal.origin.id == '5935711140':
        #             await self.telegram_command(signal)
        #         elif signal.origin.id in self.com.GENERAL_GROUPS:
        #             pass

        #         else:
        #             print('new chat ID:', signal.origin.id, signal.origin.name)
        #             db.gen_log('new chat ID:' + str(signal.origin.id) + signal.origin.name)
        #             #Deal with unrecognized telegram channels

        #     except Exception as e:
        #         db.error_log(str(e) + '\nMessage:' + event.raw_text + '\nExcept:' + str(traceback.format_exc()))


    async def telegram_command(self, signal):
        '''Commands which can be manually triggered through the telegram client'''
        #db.gen_log('Telegram Robot: ' + signal.message)
        # Bot commands
        if signal.content == self.com.STOP:
            print('Disconnecting Discbagger...')
            await self.clientChannel[1].put('close')
            await self.client.close()
        # Stream Commands
        # elif signal.message == self.com.HIRN_SIGNAL:
        #     with open('docs/hirn_example.txt', 'r', encoding='utf-8') as f:
        #         signal.message = f.read()
        #     signal.origin.id = '1248393106'
        #     signal.origin.name = 'Hirn'
        #     await new_signal.new_signal(signal)
        # elif signal.message == '/hirn2':
        #     with open('docs/hirn_example2.txt', 'r', encoding='utf-8') as f:
        #         signal.message = f.read()
        #     signal.origin.id = '1248393106'
        #     signal.origin.name = 'Hirn'
        #     await new_signal.new_signal(signal)
        # elif signal.message == '/newhirn':
        #     signal.origin.id = '1248393106'
        #     signal.origin.name = 'randomHirn'
        #     for m in await self.client.get_messages('https://t.me/HIRN_CRYPTO', limit=20):
        #         if 'Buy Price:' in m.message:
        #             signal.message = m.message
        #             await new_signal.new_signal(signal)
        #             break
        # elif signal.message == '/past':
        #     await self.get_past_messages('1248393106')
        # elif signal.message == '/except':
        #     raise Exception('Log this exception please')




    async def run(self):
        '''Start recieving discord events'''
        await self.start_discord_handler(self.client)
        #db.gen_log('Launching Telegram Scraper...')
        print('Connecting to discord...')
        await self.client.start(self.key)
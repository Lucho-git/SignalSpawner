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
        
        @client.event
        async def on_message(message):
            if message.channel.id == 1064541939640324137:
                #Deals with command messages inside of command channel
                if message.content.startswith('!'):
                    print('Discord command:', message.content)
                    command = message.content[len('!'):].split()[0]
                    args = message.content.split()[1:]
                    if command == 'get_message_history':
                        chuid = str(args[0])
                        num_messages = int(args[1])
                        for guild_data in self.channels.values():
                            data = guild_data.get(str(chuid))
                            if data is not None:
                                guid = str(data['guild_id'])
                                id_found = any(item['channel_id'] == chuid for item in list(self.channels[guid].values())[:])
                                if (id_found):
                                    guild = await client.fetch_guild(message.guild.id)
                                if guild is None:
                                    print(f'Could not find guild with ID {guid}')
                                    return
                                channel = await client.fetch_channel(chuid)
                                if channel is None:
                                    print(f'Could not find channel with ID {data["channel_id"]}')
                                    return
       
                                messages = await channel.history(limit=num_messages).flatten()
                                for message in messages:
                                    print(f'{message.author}: {message.content}')
                                return
                    if command == self.com.STOP:
                        print('Disconnecting Discbagger...')
                        await self.clientChannel[1].put('close')
                        await self.client.close()
                            #await self.discord_command(message)
            elif message.author == client.user:
                #Ignore non command messages from self
                return
            
            elif (message.guild):
                #Regular Message and signal handler, will add new discord channels, and receive signals
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


    async def discord_command(self, message):
        '''Commands which can be manually triggered through the telegram client'''
        #db.gen_log('Telegram Robot: ' + signal.message)
        # Bot commands


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
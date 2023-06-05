"""Main entry point for telebagger"""
import asyncio
import nest_asyncio
import argparse
from colorama import init
from config import run_local
from telebagger import TelegramEvents
from discbagger import DiscordEvents

async def main(local):
    '''Bagger'''
    init()  # Initialising colorama
    if local:
        run_local()
        print('Running Locally')

    #communication clientChannel, so discord and telegram can exit simeltaneously
    c1 = asyncio.Queue()
    c2 = asyncio.Queue()
    clientChannel = [c1,c2]

    discbagger = DiscordEvents(clientChannel)
    telebagger = TelegramEvents(clientChannel)
    #This ensures program exits smoothly on command
    asyncio.create_task(telebagger.exit_self())
    asyncio.create_task(discbagger.exit_self())

    print('Connecting to telebagger...')
    await asyncio.gather(telebagger.run(), discbagger.run())
    print('Exiting....')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", help="activate some feature", action="store_true")
    args = parser.parse_args()

    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    
    loop.run_until_complete(main(args.local))


    
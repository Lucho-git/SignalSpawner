"""Main entry point for telebagger"""
import asyncio
import nest_asyncio
import argparse
import subprocess
import schedule
import os
from colorama import init
from telebagger import TelegramEvents
from discbagger import DiscordEvents
import config
import sys

async def run_scheduled_jobs():
    """ Coroutine to run scheduled jobs """
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)  # Check every minute

def scheduled_job():
    print("Running scheduled job.")
    venv_python = sys.executable
    subprocess.run([venv_python, "telegram_bot.py"])

async def run_scheduled_jobs():
    """ Coroutine to run scheduled jobs """
    while True:
        schedule.run_pending()
        await asyncio.sleep(60)  # Check every minute

def scheduled_job():
    print("Running scheduled job.")
    subprocess.run(["python", "telegram_bot.py"])

async def main(local):
    '''Bagger'''
    init()  # Initialising colorama
    # if local:
    #     config.run_local()
    #     print('Running Locally')

    #communication clientChannel, so discord and telegram can exit simeltaneously
    c1 = asyncio.Queue()
    c2 = asyncio.Queue()
    clientChannel = [c1,c2]

    #discbagger = DiscordEvents(clientChannel)
    telebagger = TelegramEvents(clientChannel)
    #This ensures program exits smoothly on command
    asyncio.create_task(telebagger.exit_self())
    # asyncio.create_task(discbagger.exit_self())

    print('Connecting to telebagger...')
    await asyncio.gather(telebagger.run()) # ,discbagger.run()
    print('Exiting....')

async def gather_tasks(local_arg):
    task1 = asyncio.create_task(main(local_arg))
    task2 = asyncio.create_task(run_scheduled_jobs())

    # Gather tasks and wait for all of them to complete
    await asyncio.gather(task1, task2)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", help="activate some feature", action="store_true")
    args = parser.parse_args()

    nest_asyncio.apply()

    # Schedule the scheduler.py script to run every minute
    schedule.every().day.at("00:00").do(scheduled_job)


    loop = asyncio.get_event_loop()
    loop.run_until_complete(gather_tasks(args.local))

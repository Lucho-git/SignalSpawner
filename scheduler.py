from apscheduler.schedulers.background import BackgroundScheduler
import subprocess

def run_telegram_bot():
    # Run the telegram_bot.py script
    subprocess.run(["python", "telegram_bot.py"], cwd="/app")

print('starting')
scheduler = BackgroundScheduler()

# Schedule run_telegram_bot to be called every day at midnight
scheduler.add_job(run_telegram_bot, 'cron', hour=0, minute=0)

scheduler.start()
print('going')

# Keep the scheduler running
try:
    # This is a blocking call that will keep the scheduler running
    scheduler._event.wait()
except (KeyboardInterrupt, SystemExit):
    # Not strictly necessary if you're running this script in Docker and stopping the container with SIGTERM,
    # but it's good practice to cleanly shutdown the scheduler
    scheduler.shutdown()
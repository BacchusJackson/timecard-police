import asyncio
import datetime
import logging
import os
import re

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from scheduler import Scheduler

app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))
scheduler = Scheduler(app.client)
tasks: list[asyncio.Task] = []
ADMIN = os.environ.get("TIMECARD_POLICE_ADMIN")
# Fri 10 Jun 2022 17:34
TIME_FORMAT = "%a %d %b %Y %H:%M"
# Set up logging
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO, datefmt=TIME_FORMAT)


def restart_scheduler():
    tasks[1].cancel()
    del tasks[1]
    tasks.append(asyncio.create_task(scheduler.start_async()))


async def admin_command(message, next):
    logging.info(f"Admin Command called by {message['user']} ->{message['text']}<-")
    if message["user"] == ADMIN:
        await next()


@app.message("hello")
async def message_hello(message, say):
    logging.info(message)
    await say(f"Howdy <@{message['user']}>!")


@app.message("yes")
async def message_yes(message, say):
    scheduler.mark_done(message['channel']['id'])
    await say("Sweet! I'll leave you alone until tomorrow :smile:")


@app.message("admin", middleware=[admin_command])
async def admin_list(message, say):
    if message["user"] == ADMIN:
        await say("Hello Admin, Here are the available commands:\n"
                  "```current time```\n"
                  "```list channels```\n"
                  "```list times```\n"
                  "```restart scheduler```\n"
                  "```new times 1000 1030 1100```\n"
                  "```pause```\n"
                  "```resume```\n"
                  "```shutdown```")


@app.message("current time")
async def current_time(say):
    await say(datetime.datetime.utcnow().strftime(TIME_FORMAT))


@app.message("list channels", middleware=[admin_command])
async def admin_list_channels(message, say):
    await say(f"Register Channels: {scheduler.channel_list()}")


@app.message("list times", middleware=[admin_command])
async def admin_list_times(message, say):
    await say(scheduler.times_list())


@app.message("reset scheduler", middleware=[admin_command])
async def admin_restart_scheduler(message, say):
    restart_scheduler()
    await say("scheduler has been reset")


@app.message(re.compile("new times .+"), middleware=[admin_command])
async def admin_new_times(message, say):
    if not scheduler.set_times(message['text'].replace("new times").strip().split(" ")):
        await say("Invalid format, try again")
        return
    restart_scheduler()
    await say(scheduler.times_list())


@app.message("pause", middleware=[admin_command])
async def admin_pause(message, say):
    scheduler.pause = True
    await say("Scheduler has been paused, no reminders will be sent.")


@app.message("resume", middleware=[admin_command])
async def admin_resume(message, say):
    scheduler.pause = False
    await say("Scheduler has been resumed, reminders will be sent.")


@app.message("shutdown", middleware=[admin_command])
async def admin_shutdown(message, say):
    await say("Entire app will be shutdown... Good bye!")
    raise KeyboardInterrupt


@app.command("/start")
async def reminders_start(ack, respond, body):
    await ack()
    await respond("You've got it bud! I'll make sure you don't forget! :thumbsup:")
    scheduler.add_channel(body["channel_id"])


@app.command("/stop")
async def reminders_stop(ack, respond, body):
    await ack()
    scheduler.remove_channel(body["channel_id"])
    await respond("Sorry, I know I'm annoying :cry: I'll leave you alone")


async def main():
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    tasks.append(asyncio.create_task(handler.start_async()))
    tasks.append(asyncio.create_task(scheduler.start_async()))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Keyboard Interrupt, Gracefully Shutting down")
        logging.debug("Cancelling Tasks...")
        for t in tasks:
            t.cancel()
        logging.info("Done!")

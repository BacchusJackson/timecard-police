import asyncio
import datetime
import logging
import os

import yaml
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from scheduler import Scheduler

app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))

logging.basicConfig(level=logging.DEBUG)
SCHEDULE_FILE = "/data/schedule.yaml"


def add_to_schedule(channel_id):
    logging.debug(f"Opening {SCHEDULE_FILE} to add {channel_id} to schedule")
    with open(SCHEDULE_FILE, "w+") as file:
        doc = yaml.full_load(file)
        logging.debug(doc)
        if doc is None:
            doc = dict()
        doc["channels"] = {channel_id: {"done": False}}
        logging.debug(doc)
        yaml.dump(doc, file)


@app.message("hello")
async def message_hello(message, say):
    await say(f"Howdy <@{message['user']}>!")


@app.message("yes")
async def message_yes(message, say):
    await say("Sweet! I'll leave you alone until tomorrow :smile:")


@app.command("/start")
async def reminders_start(ack, respond, body):
    await ack()
    # scheduled[result["channel"]].append(result["scheduled_message_id"])
    await respond("You've got it bud! I'll make sure you don't forget! :thumbsup:")
    add_to_schedule(body["channel_id"])


async def main():
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    task1 = asyncio.create_task(handler.start_async())

    scheduler = Scheduler(1)
    scheduler.add_channel("ABC-1")
    scheduler.add_channel("ABC-2")

    task2 = asyncio.create_task(scheduler.main())
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("INTERRUPTED, SHUTTING DOWN")
        pass

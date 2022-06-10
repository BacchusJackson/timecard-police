import asyncio
import datetime
import logging
import os

import yaml
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

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


async def scheduler():
    await asyncio.sleep(5)
    if not os.path.exists(SCHEDULE_FILE):
        logging.debug("schedule.yaml does not exist yet. Skip check schedule")
        return

    logging.debug(f"Scheduler Task is opening {SCHEDULE_FILE} to check for channels")
    schedule = []
    with open(SCHEDULE_FILE, "r") as file:
        doc = yaml.full_load(file)
        logging.debug(doc)
        if doc in None:
            logging.debug(f"{SCHEDULE_FILE} is None after loading yaml")
            return
        schedule = doc

    for c_id in schedule['channels'].keys():
        if schedule['channels'][c_id]["done"]:
            logging.debug(f"Sending a message to {c_id}")
            result = await app.client.chat_postMessage(
                channel=c_id,
                text="Hey! Did you complete your time card?"
            )
            logging.debug(f"API Result: {result}")


async def main():
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    task1 = asyncio.create_task(handler.start_async())
    task2 = asyncio.create_task(scheduler())
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("INTERRUPTED, SHUTTING DOWN")
        pass

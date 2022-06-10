import datetime
import logging
import os

import yaml
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))

logging.basicConfig(level=logging.DEBUG)


def add_to_schedule(channel_id):
    logging.debug("Opening schedule.yaml")
    with open("/data/schedule.yaml", "w+") as file:
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
async def reminders_start(ack, respond, body, logger, client, command):
    await ack()
    # scheduled[result["channel"]].append(result["scheduled_message_id"])
    await respond("You've got it bud! I'll make sure you don't forget! :thumbsup:")
    add_to_schedule(body["channel_id"])


async def test_func():
    await asyncio.sleep(2)
    print("TEST FUNCTION")


async def main():
    handler = AsyncSocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    task1 = asyncio.create_task(handler.start_async())
    task2 = asyncio.create_task(test_func())
    await asyncio.gather(task1, task2)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

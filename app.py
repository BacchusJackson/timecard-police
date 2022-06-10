import asyncio
import logging
import os

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from scheduler import Scheduler

app = AsyncApp(token=os.environ.get("SLACK_BOT_TOKEN"))
scheduler = Scheduler(app.client)
tasks: list[asyncio.Task] = []

# Set up logging
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

app.logger.addHandler(ch)


@app.message("hello")
async def message_hello(message, say):
    await say(f"Howdy <@{message['user']}>!")


@app.message("yes")
async def message_yes(message, say):
    await say("Sweet! I'll leave you alone until tomorrow :smile:")


@app.command("/start")
async def reminders_start(ack, respond, body):
    await ack()
    await respond("You've got it bud! I'll make sure you don't forget! :thumbsup:")
    scheduler.add_channel(body["channel_id"])


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

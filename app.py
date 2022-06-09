import datetime
import logging
import os

import yaml
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

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
def message_hello(message, say):
    say(f"Howdy <@{message['user']}>!")


@app.message("yes")
def message_yes(message, say):
    say("Sweet! I'll leave you alone until tomorrow :smile:")


@app.command("/start")
def reminders_start(ack, respond, body, logger, client, command):
    ack()
    # scheduled[result["channel"]].append(result["scheduled_message_id"])
    respond("You've got it bud! I'll make sure you don't forget! :thumbsup:")
    add_to_schedule(body["channel_id"])


if __name__ == "__main__":
    print(f"Logging set to {app.logger.level}")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

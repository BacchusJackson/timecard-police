import datetime
import logging
import os

from slack_bolt import App
from slack_bolt.error import BoltError
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

logging.basicConfig(level=logging.DEBUG)

channels = []


@app.message("hello")
def message_hello(message, say):
    say(f"Howdy <@{message['user']}>!")


@app.message("yes")
def message_yes(message, say, client):
    if message["channel_id"] in channels:
        say("Sweet! I'll leave you alone until tomorrow :smile:")
        return


@app.command("/start")
def reminders_start(ack, respond, body, logger, client):
    ack()
    logger.info(body)
    try:
        result = client.chat_scheduleMessage(
            channel=body["channel_id"],
            text="Did you finish your time card?",
            post_at=(datetime.date.today() + datetime.timedelta(minutes=1)).strftime('%s')
        )
        logger.info(result)
        respond("You've got it bud! I'll bug you to finish your time card")

    except SlackApiError as e:
        respond("Sorry... something went wrong :sad:")
        logger.error(f"Error scheduling message: {e}")
    except BoltError as e:
        respond("Sorry... something went really wrong :sad:")
        logger.error(f"Error in /start command execution {e}")


if __name__ == "__main__":
    print(f"Logging set to {app.logger.level}")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

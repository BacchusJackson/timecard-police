import datetime
import logging
import os

from slack_bolt import App, BoltRequest
from slack_bolt.error import BoltError
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from slack_sdk.webhook.webhook_response import WebhookResponse

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

logging.basicConfig(level=logging.DEBUG)

scheduled = {}


@app.message("hello")
def message_hello(message, say):
    say(f"Howdy <@{message['user']}>!")


@app.message("yes")
def message_yes(message, say, logger):
    if message["channel"] in scheduled.keys() :
        scheduled[message["channel"]].pop()
        say("Sweet! I'll leave you alone until tomorrow :smile:")


@app.command("/start")
def reminders_start(ack, respond, body, logger, client, command, request):
    ack()
    logger.info(command)

    try:
        post_time = (datetime.datetime.utcnow() + datetime.timedelta(minutes=1)).strftime('%s')
        result = client.chat_scheduleMessage(
            channel=body["channel_id"],
            text="Did you finish your time card?",
            post_at=post_time
        )
        if result["channel"] not in scheduled:
            scheduled[result["channel"]] = []

        scheduled[result["channel"]].append(result["scheduled_message_id"])
        result2: WebhookResponse = respond("You've got it bud! I'll bug you to finish your time card")
        logger.info(result2.headers)

    except SlackApiError as e:
        respond("Sorry... something went wrong :cry:")
        logger.error(f"Error scheduling message: {e}")
    except BoltError as e:
        respond("Sorry... something went really wrong :cry:")
        logger.error(f"Error in /start command execution {e}")


if __name__ == "__main__":
    print(f"Logging set to {app.logger.level}")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

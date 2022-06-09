import logging
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

logging.basicConfig(level=logging.DEBUG)


@app.message("hello")
def message_hello(message, say):
    say(f"Howdy <@{message['user']}>!")


if __name__ == "__main__":
    print(f"Logging set to {app.logger.level}")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()

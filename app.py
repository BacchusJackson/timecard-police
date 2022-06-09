import logging
import os

from slack_bolt import App

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

app.logger.setLevel(logging.DEBUG)


@app.message("hello")
def message_hello(message, say):
    say(f"Howdy <@{message['user']}>!")


if __name__ == "__main__":
    print(f"Logging set to {app.logger.level}")
    app.start(port=int(os.environ.get("PORT", 3000)))

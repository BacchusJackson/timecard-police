import os

from slack_bolt import App

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)


@app.command("/howdy")
def handle_some_command(ack, body, respond, command, logger):
    ack()
    logger.info(body)
    respond("Howdy! From Timecard Police Bot")


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))

import os

from slack_bolt import App

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)


@app.command("/howdy")
async def command(ack, body, respond):
    await ack()
    await respond(f"Howdy! <@{body['user_id']}!")


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))

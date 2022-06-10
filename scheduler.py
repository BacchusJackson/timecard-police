import asyncio
import logging
import os
import datetime
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient

import yaml

# Initialize SocketModeClient with an app-level token + WebClient
client = SocketModeClient(
    app_token=os.environ.get("SLACK_APP_TOKEN"),
    web_client=AsyncWebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
)


logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

SCHEDULE_FILE = "/data/schedule.yaml"


async def send_reminder_at(sometime: datetime):
    sleep_for = sometime.timestamp() - datetime.datetime.utcnow().timestamp()
    await asyncio.sleep(sleep_for)
    logger.info(f"Task Activated, Slept for {sleep_for:.2f} seconds")
    check_schedule()


def check_schedule():
    logger.debug("check_schedule Opening the schedule.yaml file")
    schedule: dict
    if not os.path.exists(SCHEDULE_FILE):
        logger.debug("schedule.yaml does not exist yet. Skip check schedule")
        return
    with open(SCHEDULE_FILE, "r") as file:
        doc = yaml.full_load(file)
        logging.debug(doc)
        if doc is None:
            logger.debug("schedule.yaml could not be parsed")
            return
        channels: dict = doc.get("channels")

    logger.debug("Checking keys for the channel id")
    for c_id in channels.keys():
        if not channels[c_id].get("done"):
            logger.debug(f"Sending a Reminder to {c_id} ...")


def send_message(channel_id: str):
    try:
        result = client.web_client.chat_postMessage(channel=channel_id, text="Hey! Did you complete your time card?")
        logger.info(result)
    except SlackApiError as e:
        logger.error(f"Error posting Message to channel {channel_id}: {e}")


def reset_reminders():
    logger.debug("Opening the schedule.yaml file to reset done values")
    schedule: dict
    if not os.path.exists(SCHEDULE_FILE):
        logger.debug("schedule.yaml does not exist yet. Skip reset")
        return

    with open(SCHEDULE_FILE, "r") as file:
        doc = yaml.full_load(file)
        logging.debug(doc)
        if doc is None:
            logger.debug("schedule.yaml could not be parsed")
            return
        schedule = doc
    for c_id in schedule.get("channels").keys():
        schedule[c_id]["done"] = False
    with open(SCHEDULE_FILE, "w") as file:
        yaml.dump(schedule, file)


def today_at(hour, minutes) -> datetime:
    now = datetime.datetime.utcnow()
    return datetime.datetime(now.year, now.month, now.day, hour, minutes)


def et_to_utc(et_date: datetime) -> datetime:
    return et_date + datetime.timedelta(hours=4)


def filter_expired(dt_schedule: list[datetime]):
    logger.info(f"Current UTC Time: {datetime.datetime.utcnow()}")
    return [element for element in dt_schedule if element > datetime.datetime.utcnow()]


def get_schedule_times() -> list[datetime]:
    lines: list[str]
    schedule_times: list[datetime] = []
    h: str
    m: str

    # Read lines from file
    with open("times.txt", "r") as file:
        lines = file.readlines()
        if len(lines) < 1:
            return []

    # Parse lines into schedule times
    for line in lines:
        h, m = line.split(" ")
        schedule_times.append(et_to_utc(today_at(int(h), int(m))))

    return schedule_times


async def main():
    await client.connect()
    await asyncio.sleep(float("inf"))
    # while True:
    #
    #     schedule_times = []
    #     try:
    #         schedule_times = get_schedule_times()
    #     except ValueError as e:
    #         logger.error("Invalid value in times file")
    #         exit(-1)
    #
    #     logger.info(f"Schedule Times: {schedule_times}")
    #     filtered_schedule = filter_expired(schedule_times)
    #     logger.info(f'Filtered Schedule Times: {filtered_schedule}')
    #     tasks = []
    #     for dt in filtered_schedule:
    #         tasks.append(asyncio.create_task(send_reminder_at(dt)))
    #
    #     await asyncio.gather(*tasks)
    #     logger.info("All Schedule tasks complete for the day!")
    #     logger.info("Resetting statuses on Schedule...")
    #     reset_reminders()
    #     logger.info(f"Current UTC Time is: {datetime.datetime.utcnow().isoformat()}")
    #     wake_time = today_at(0, 1) + datetime.timedelta(days=1)
    #     logger.info(f"Sleeping until {wake_time.isoformat()}")
    #     await asyncio.sleep(wake_time.timestamp() - datetime.datetime.utcnow().timestamp())


if __name__ == "__main__":
    print("STARTING SCHEDULER")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("INTERRUPTED, SHUTTING DOWN")
        pass

import asyncio
import logging
import os
import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import yaml

client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)


async def send_reminder_at(sometime: datetime):
    sleep_for = sometime.timestamp() - datetime.datetime.utcnow().timestamp()
    await asyncio.sleep(sleep_for)
    logger.info(f"Task Activated, Slept for {sleep_for:.2f} seconds")
    check_schedule()


def check_schedule():
    logger.debug("Opening the schedule.yaml file")
    schedule: dict
    with open("schedule.yaml", "r+") as file:
        content = file.read()
        logger.debug(content)
        if file.tell() < 1:
            logger.info("schedule.yaml has no content, cannot check schedule")
            return
        schedule = yaml.full_load(content)

    logger.debug(schedule)
    channels: dict = schedule.get("channels")
    logger.debug("Checking keys for the channel id")
    for c_id in channels.keys():
        if not channels[c_id].get("done"):
            logger.debug(f"Sending a Reminder to {c_id} ...")


def send_message(channel_id: str):
    try:
        result = client.chat_postMessage(channel=channel_id, text="Hey! Did you complete your time card?")
        logger.info(result)
    except SlackApiError as e:
        logger.error(f"Error posting Message to channel {channel_id}: {e}")


def reset_reminders():
    logger.debug("Opening the schedule.yaml file to reset done values")
    schedule: dict
    with open("schedule.yaml", "w+") as file:
        content = file.read()
        logger.debug(content)
        # Check for a blank file
        if file.tell() < 1:
            logger.info("schedule.yaml has no content, cannot reset reminders")
            return
        schedule = yaml.full_load(content)
        channels: dict = schedule.get("channels")
        for c_id in channels.keys():
            channels[c_id]["done"] = False
        yaml.dump(schedule, file)


def today_at(hour, minutes) -> datetime:
    now = datetime.datetime.utcnow()
    return datetime.datetime(now.year, now.month, now.day, hour, minutes)


def et_to_utc(et_date: datetime) -> datetime:
    return et_date + datetime.timedelta(hours=4)


def filter_expired(dt_schedule: list[datetime]):
    logger.info(f"Current UTC Time: {datetime.datetime.utcnow()}")
    return [element for element in dt_schedule if element > datetime.datetime.utcnow()]


async def main():
    while True:
        schedule = [
            et_to_utc(today_at(15, 0)),
            et_to_utc(today_at(15, 1)),
            et_to_utc(today_at(15, 2)),
            et_to_utc(today_at(15, 51)),
            et_to_utc(today_at(17, 24)),
            et_to_utc(today_at(17, 25)),
            et_to_utc(today_at(17, 26)),
        ]

        filtered_schedule = filter_expired(schedule)
        logger.info(f"Schedule: {schedule}")
        logger.info(f'Filtered Schedule: {filtered_schedule}')
        tasks = []
        for dt in filtered_schedule:
            tasks.append(asyncio.create_task(send_reminder_at(dt)))

        await asyncio.gather(*tasks)
        logger.info("All Schedule tasks complete for the day!")
        logger.info("Resetting statuses on Schedule...")
        reset_reminders()
        logger.info(f"Current UTC Time is: {datetime.datetime.utcnow().isoformat()}")
        wake_time = today_at(0, 1) + datetime.timedelta(days=1)
        logger.info(f"Sleeping until {wake_time.isoformat()}")
        await asyncio.sleep(wake_time.timestamp() - datetime.datetime.utcnow().timestamp())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("INTERRUPTED, SHUTTING DOWN")
        pass

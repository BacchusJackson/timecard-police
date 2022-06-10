import asyncio
import datetime

from slack_bolt.app.async_app import AsyncWebClient
import logging

TIME_FORMAT = "%a %d %b %Y %H:%M"


class Channel:
    name: str
    timecard_done: bool
    client: AsyncWebClient

    def __init__(self, channel_id: str, client):
        self.name = channel_id
        self.timecard_done = False
        self.client = client

    async def send_message(self):
        logging.info(f"Sending a message to {self.name}")
        res = await self.client.chat_postMessage(channel=self.name, text="Have you completed your time card?")
        logging.debug(res)


class Scheduler:
    client: AsyncWebClient
    tasks: list
    channels: list[Channel]
    times: list[datetime]

    def __init__(self, client):
        self.client = client
        self.channels = []
        self.times = []

    async def start_async(self):
        logging.info("Scheduler Started")
        while True:
            self.times = _get_schedule_times()
            logging.info(f"Current Time UTC: {datetime.datetime.utcnow().strftime(TIME_FORMAT)}")
            times_str = ', '.join([t.strftime(TIME_FORMAT) for t in self.times])
            logging.info(f"Scheduled Times [{len(self.times)}]: {times_str}")
            self.tasks = []
            for t in self.times:
                self.tasks.append(asyncio.create_task(self.send_at(t)))

            logging.info(f"Tasks Scheduled: {len(self.tasks)}")
            await asyncio.gather(*self.tasks)
            logging.info("Done, resetting Channel reminders")
            for c in self.channels:
                c.timecard_done = False

            logging.info(f"Current UTC Time is: {datetime.datetime.utcnow().strftime(TIME_FORMAT)}")
            wake_time = today_at(0, 1) + datetime.timedelta(days=1)
            logging.info(f"Sleeping until {wake_time.strftime(TIME_FORMAT)}")
            await asyncio.sleep(wake_time.timestamp() - datetime.datetime.utcnow().timestamp())

    def add_channel(self, channel_id):
        self.channels.append(Channel(channel_id, self.client))
        logging.info(f"New Channel Register -> {channel_id}")

    async def send_at(self, sometime: datetime):
        sleep_for = sometime.timestamp() - datetime.datetime.utcnow().timestamp()
        if sleep_for < 0:
            return
        await asyncio.sleep(sleep_for)
        for c in self.channels:
            if not c.timecard_done:
                await c.send_message()


def today_at(hour, minutes, seconds=0) -> datetime:
    now = datetime.datetime.utcnow()
    return datetime.datetime(now.year, now.month, now.day, hour, minutes, seconds)


def et_to_utc(et_date: datetime) -> datetime:
    return et_date + datetime.timedelta(hours=4)


def _gen_time_list(count) -> list[datetime]:
    temp_times = []
    for i in range(count):
        temp_times.append(datetime.datetime.utcnow() + datetime.timedelta(seconds=5 * (i + 1)))
    return temp_times


def _get_schedule_times() -> list[datetime]:
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

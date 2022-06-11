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
    pause: bool

    def __init__(self, client):
        self.client = client
        self.channels = []
        self.times = []
        self.pause = False

    async def start_async(self):
        logging.info("Scheduler Started")
        self.times = _get_schedule_times()
        while True:
            logging.info(f"Current Time UTC: {datetime.datetime.utcnow().strftime(TIME_FORMAT)}")
            logging.info(self.times_list())
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
        if len([c for c in self.channels if c.name == channel_id]) == 0:
            self.channels.append(Channel(channel_id, self.client))
            logging.info(f"New Channel Register -> {channel_id}")
            return
        logging.warning(f"Prevented duplicate registration -> {channel_id}")

    def remove_channel(self, channel_id):
        logging.info(f"Removing Channel {channel_id}")
        self.channels = [c for c in self.channels if c.name != channel_id]
        logging.info(f"New Channel List: {self.channels}")

    def mark_done(self, channel_id):
        logging.info(f"Marking Channel {channel_id} as done")
        for index, c in enumerate(self.channels):
            if c.name == channel_id:
                self.channels[index].timecard_done = True

    def set_times(self, times: list[str]) -> bool:
        temp_times = []
        for item in times:
            if len(item) != 4:
                logging.warning(f"Invalid times string provided, no change made ->{times}<-")
                return False
            try:
                h = int(item[0:1])
                m = int(item[2:3])
            except ValueError:
                logging.warning(f"Cannot convert times string to integers ->{item}-<")
                return False
            temp_times.append(today_at(h, m))
        self.times = temp_times
        return True

    async def send_at(self, sometime: datetime):
        sleep_for = sometime.timestamp() - datetime.datetime.utcnow().timestamp()
        logging.info(f"Scheduled Task, sleep for: {sleep_for}")
        if sleep_for < 0:
            return
        await asyncio.sleep(sleep_for)
        logging.info(f"Schedule Task awake, checking active channels")
        for channel in [c for c in self.channels if not c.timecard_done]:
            if self.pause:
                logging.warning(f"Schedule is paused, suppressing message to {channel.name}")
                return
            await channel.send_message()

    def channel_list(self) -> str:
        return ", ".join([c.name for c in self.channels])

    def times_list(self) -> str:
        times_str = ', '.join([t.strftime(TIME_FORMAT) for t in self.times])
        return f"Scheduled Times [{len(self.times)}]: {times_str}"


def today_at(hour: int, minutes: int, seconds=0) -> datetime:
    now = datetime.datetime.utcnow()
    return datetime.datetime(now.year, now.month, now.day, hour, minutes, seconds)


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
        schedule_times.append(today_at(int(h), int(m)))

    return schedule_times

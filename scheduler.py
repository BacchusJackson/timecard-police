import asyncio
import datetime

from slack_bolt.app.async_app import AsyncWebClient
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Channel:
    name: str
    timecard_done: bool
    client: AsyncWebClient

    def __init__(self, channel_id: str, client):
        self.name = channel_id
        self.timecard_done = False
        self.client = client

    async def send_message(self):
        logger.info(f"Sending a message to {self.name} with client: {self.client}")
        res = await self.client.chat_postMessage(channel=self.name, text="Have you completed your time card?")
        logger.debug(res)


class Scheduler:
    client: AsyncWebClient
    tasks: list
    channels: list[Channel]
    times: list[datetime]

    def __init__(self, client):
        self.client = client
        self.channels = []
        self.times = _gen_time_list(2)

    async def start_async(self):
        logger.info("STARTED PROCESS")
        while True:
            self.times = _gen_time_list(5)
            self.tasks = []
            for t in self.times:
                for c in self.channels:
                    self.tasks.append(asyncio.create_task(send_at(c, t)))

            await asyncio.gather(*self.tasks)
            logger.info("Done, reset")
            for c in self.channels:
                c.timecard_done = False
            logger.info("Sleeping for 5")
            await asyncio.sleep(5)

    def add_channel(self, channel_id):
        self.channels.append(Channel(channel_id, self.client))


async def send_at(c: Channel, sometime: datetime):
    sleep_for = sometime.timestamp() - datetime.datetime.utcnow().timestamp()
    if sleep_for < 0:
        return
    await asyncio.sleep(sleep_for)
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

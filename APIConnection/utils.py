import time
from asyncio import AbstractEventLoop, get_running_loop, sleep
from calendar import monthrange
from datetime import date

from APIConnection.logger import logger


class Monitor:
    lag: float = 0

    def __init__(self, interval: float = 0.25):
        self.active_tasks = None
        self._interval = interval

    def start(self):
        loop = get_running_loop()
        loop.create_task(self.monitor_loop(loop))

    async def monitor_loop(self, loop: AbstractEventLoop):
        logger.debug("Monitor loop started")
        while loop.is_running():
            start = loop.time()
            await sleep(self._interval)
            time_slept = loop.time() - start
            self.lag = time_slept - self._interval
            # tasks = [t for t in Task.all_tasks(loop) if not t.done()]
            # self.active_tasks = len(tasks)
            logger.debug(f"Lag time is {self.lag} s")
            # logger.debug(f"active_tasks = {self.active_tasks}")


def get_last_date_of_month(year: int, month: int) -> date:
    """Given a year and a month returns an instance of the date class
    containing the last day of the corresponding month.
    """
    return date(year, month, monthrange(year, month)[1])


def convert_dates_to_timeframe(start: date, stop: date) -> str:
    """Given two dates, returns a stringified version of the interval between
    the two dates which is used to retrieve data for a specific time frame
    from Google Trends.
    """
    return f"{start.strftime('%Y-%m-%d')} {stop.strftime('%Y-%m-%d')}"


def timeit(method):
    def timed(*args, **kwargs):
        ts = time.time()
        result = method(*args, **kwargs)
        te = time.time()
        if "log_time" in kwargs:
            name = kwargs.get("log_name", method.__name__.upper())
            kwargs["log_time"][name] = int(te - ts)
        else:
            print("%r  %2.22f s" % (method.__name__, te - ts))
        return result

    return timed

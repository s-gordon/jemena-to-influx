import datetime
import logging
import sys
from os import environ
from time import sleep
from typing import Any, Collection, Dict, Union

import pytz
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from src.electricity_outlook import (
    do_login,
    get_latest_interval,
    get_periodic_data,
    trigger_latest_data_fetch,
)
from src.util import build_influx_measurements, create_session


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

BASE_URL = environ.get("BASE_URL", "https://electricityoutlook.jemena.com.au")
JEMENA_USERNAME = environ["JEMENA_USERNAME"]
JEMENA_PASSWORD = environ["JEMENA_PASSWORD"]
USERAGENT = environ.get(
    "USERAGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36",
)

INFLUX_BUCKET = environ.get("INFLUX_BUCKET", "jemena")
BACKFILL_DAYS = int(environ.get("BACKFILL_DAYS", "28"))


def do_it():
    influx_client = InfluxDBClient.from_env_properties()
    influx_write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    s = create_session(user_agent=USERAGENT)
    tz = pytz.timezone("Australia/Melbourne")
    now_dt = pytz.utc.localize(
        datetime.datetime.utcnow(), is_dst=None
    ).astimezone(tz)

    for i in range(1, BACKFILL_DAYS + 1):
        backfill_dt = now_dt - datetime.timedelta(days=i)
        print(f"Backfilling today - {i} ({backfill_dt})")
        do_login(JEMENA_USERNAME, JEMENA_PASSWORD, s, BASE_URL)
        periodic_data = get_periodic_data(s, BASE_URL, i)
        influx_data = build_influx_measurements(
            tz, periodic_data, backfill_dt, now_dt.replace(tzinfo=None)
        )

        logging.info("submitting stats to Influx")
        influx_write_api.write(INFLUX_BUCKET, record=influx_data)


if __name__ == "__main__":
    do_it()

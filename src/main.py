import datetime
import logging
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

CHECK_INTERVAL = 3600


def do_it():
    influx_client = InfluxDBClient.from_env_properties()
    influx_write_api = influx_client.write_api(write_options=SYNCHRONOUS)
    s = create_session(user_agent=USERAGENT)
    tz = pytz.timezone("Australia/Melbourne")

    while True:
        do_login(JEMENA_USERNAME, JEMENA_PASSWORD, s, BASE_URL)

        periodic_data = get_periodic_data(s, BASE_URL)
        latest_interval = get_latest_interval(periodic_data)
        # 2021-04-20:17
        # the day is divided into half-hours, so 17 = 8:30 am

        # don't do this if within 3 hours of latest data?
        trigger_latest_data_fetch_response = trigger_latest_data_fetch(
            latest_interval, s, BASE_URL
        )
        i = 0

        if trigger_latest_data_fetch_response.polling:
            logging.info("Waiting for backend to update...")
            params = {"lastKnownInterval": latest_interval}
            while True:
                # https://electricityoutlook.jemena.com.au/electricityView/isElectricityDataUpdated?lastKnownInterval=2021-04-20:17
                # n.b. data for 2021-04-20:24 (midday) was only available after 12:30
                #
                logging.info("polling...")
                res = s.get(
                    f"{BASE_URL}/electricityView/isElectricityDataUpdated",
                    params=params,
                )
                res.raise_for_status()
                if "true" in res.text:
                    periodic_data = get_periodic_data(s, BASE_URL)
                    latest_interval = get_latest_interval(periodic_data)
                    break

                if i == 9:
                    logging.info("Unable to retrieve any new data!")
                    break

                i += 1
                sleep(3)

            # reget the data, e.g.
            # https://electricityoutlook.jemena.com.au/electricityView/period/day/0?_=1618885953690

        else:
            logging.info("Had latest data")

        # 2021-04-20:17
        half_hour_sections = int(latest_interval.split(":")[-1])

        measurement_base_dt = pytz.utc.localize(
            datetime.datetime.utcnow(), is_dst=None
        ).astimezone(tz)

        threshold_dt = (
            datetime.datetime(
                day=measurement_base_dt.day,
                month=measurement_base_dt.month,
                year=measurement_base_dt.year,
                hour=0,
                minute=0,
                second=0,
            )
            + datetime.timedelta(minutes=(half_hour_sections * 30))
        )

        influx_data = build_influx_measurements(
            tz, periodic_data, measurement_base_dt, threshold_dt
        )

        logging.info("submitting stats to Influx")
        logging.info(influx_data)
        influx_write_api.write(INFLUX_BUCKET, record=influx_data)
        logging.info(f"sleeping for {CHECK_INTERVAL}")
        sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    do_it()

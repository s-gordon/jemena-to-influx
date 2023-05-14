import datetime
import json
import logging
from os import environ
from pathlib import Path
from typing import Any, Collection, Dict, Union

import pytz
import requests
from requests import Session, cookies
from requests.cookies import RequestsCookieJar
from requests.utils import dict_from_cookiejar


PERSIST_FILE = environ.get(
    "PERSIST_FILE", Path.joinpath(Path.home(), "jemenacookies.txt")
)


def build_influx_measurements(
    tz: Any,
    periodic_data: Dict[str, Any],
    measurement_base_dt: datetime.datetime,
    threshold_dt: datetime.datetime,
):
    assert threshold_dt.tzinfo is None
    influx_data = []

    for i, usage in enumerate(
        periodic_data["selectedPeriod"]["consumptionData"]["peak"]
    ):
        measurement_dt = (
            datetime.datetime(
                day=measurement_base_dt.day,
                month=measurement_base_dt.month,
                year=measurement_base_dt.year,
                hour=0,
                minute=0,
                second=0,
            )
            + datetime.timedelta(hours=i)
        )
        if measurement_dt > threshold_dt:
            break

        logging.info(f"{measurement_dt}: {usage}")
        ts = tz.localize(measurement_dt).isoformat("T")
        influx_data.append(
            {
                "measurement": "GridUsage",
                "time": ts,
                "fields": {"kWH": float(usage)},
            }
        )

    for i, usage in enumerate(
        periodic_data["selectedPeriod"]["consumptionData"]["generation"]
    ):
        measurement_dt = (
            datetime.datetime(
                day=measurement_base_dt.day,
                month=measurement_base_dt.month,
                year=measurement_base_dt.year,
                hour=0,
                minute=0,
                second=0,
            )
            + datetime.timedelta(hours=i)
        )
        if measurement_dt > threshold_dt:
            break

        logging.info(f"{measurement_dt}: {usage}")
        ts = tz.localize(measurement_dt).isoformat("T")
        influx_data.append(
            {
                "measurement": "Generation",
                "time": ts,
                "fields": {"kWH": float(usage)},
            }
        )

    for i, usage in enumerate(
        periodic_data["selectedPeriod"]["costData"]["peak"]
    ):
        measurement_dt = (
            datetime.datetime(
                day=measurement_base_dt.day,
                month=measurement_base_dt.month,
                year=measurement_base_dt.year,
                hour=0,
                minute=0,
                second=0,
            )
            + datetime.timedelta(hours=i)
        )
        if measurement_dt > threshold_dt:
            break

        logging.info(f"{measurement_dt}: {usage}")
        ts = tz.localize(measurement_dt).isoformat("T")
        influx_data.append(
            {
                "measurement": "GridCost",
                "time": ts,
                "fields": {"$": float(usage)},
            }
        )

    for i, usage in enumerate(
        periodic_data["selectedPeriod"]["costData"]["generation"]
    ):
        measurement_dt = (
            datetime.datetime(
                day=measurement_base_dt.day,
                month=measurement_base_dt.month,
                year=measurement_base_dt.year,
                hour=0,
                minute=0,
                second=0,
            )
            + datetime.timedelta(hours=i)
        )
        if measurement_dt > threshold_dt:
            break

        logging.info(f"{measurement_dt}: {usage}")
        ts = tz.localize(measurement_dt).isoformat("T")
        influx_data.append(
            {
                "measurement": "GenerationCost",
                "time": ts,
                "fields": {"$": float(usage)},
            }
        )

    return influx_data


def create_session(user_agent: str = "python/requests") -> Session:
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent})
    s.cookies = _load_cookies()
    return s


def save_cookies(s: Session):
    data: Collection[str] = dict_from_cookiejar(s.cookies)
    out = json.dumps(data, indent=2)
    with open(PERSIST_FILE, "wt") as fh:
        logging.info(f"Writing {PERSIST_FILE}")
        fh.write(out)


def _load_cookies() -> RequestsCookieJar:
    data = {}

    if Path(PERSIST_FILE).exists():
        with open(PERSIST_FILE, "rt") as fh:
            logging.info(f"Loading {PERSIST_FILE}")
            data = json.loads(fh.read())

    return cookies.cookiejar_from_dict(data)

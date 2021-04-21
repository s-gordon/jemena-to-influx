import dataclasses
import json
import logging
import time
from typing import Any, Dict

from requests import Session

from src.util import save_cookies


@dataclasses.dataclass
class LatestTriggerResponse:
    polling: bool


def do_login(user: str, password: str, s: Session, base_url: str):
    res = s.get(f"{base_url}/electricityView/index")
    must_login = "Sign In" in res.text

    if must_login:
        logging.info(f"Logging in as {user}")
        data = {
            "login_email": user,
            "login_password": password,
            "submit": "Sign+In",
        }
        res = s.post(f"{base_url}/login_security_check", data=data)
        res.raise_for_status()
        save_cookies(s)


def get_periodic_data(
    s: Session, base_url: str, day_offset: int = 0
) -> Dict[str, Any]:
    logging.info("fetching periodic data")
    now_ms = int(time.time() * 1000)
    res = s.get(
        f"{base_url}/electricityView/period/day/{day_offset}?_={now_ms}"
    )
    res.raise_for_status()
    return json.loads(res.text)


def get_latest_interval(periodic_data: Dict[str, Any]) -> str:
    return periodic_data["latestInterval"]


def trigger_latest_data_fetch(
    last_known_interval: str, s: Session, base_url: str
) -> LatestTriggerResponse:
    now_ms = int(time.time() * 1000)
    params = {"lastKnownInterval": last_known_interval, "_": now_ms}
    res = s.get(f"{base_url}/electricityView/latestData", params=params)
    res.raise_for_status()
    data = json.loads(res.text)
    return LatestTriggerResponse(polling=data["poll"])

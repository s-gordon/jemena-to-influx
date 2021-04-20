import dataclasses
import json
import logging
import time
from typing import Any, Dict

from requests import Session


@dataclasses.dataclass
class LatestTriggerResponse:
    polling: bool


def get_periodic_data(s: Session, base_url: str) -> Dict[str, Any]:
    logging.info("fetching periodic data")
    now_ms = int(time.time() * 1000)
    res = s.get(f"{base_url}/electricityView/period/day/0?_={now_ms}")
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

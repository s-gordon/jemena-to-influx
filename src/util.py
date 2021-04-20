import json
import logging
from os import environ
from pathlib import Path
from typing import Collection

import requests
from requests import Session, cookies
from requests.cookies import RequestsCookieJar
from requests.utils import dict_from_cookiejar


PERSIST_FILE = environ.get(
    "PERSIST_FILE", Path.joinpath(Path.home(), "jemenacookies.txt")
)


def do_login(user: str, password: str, s: Session, base_url: str):
    logging.info(f"Logging in as {user}")
    data = {
        "login_email": user,
        "login_password": password,
        "submit": "Sign+In",
    }
    res = s.post(f"{base_url}/login_security_check", data=data)
    res.raise_for_status()
    save_cookies(s)


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

import datetime
import json
import os
from time import sleep
from typing import Any, Dict, Optional
from urllib.parse import urlencode

from dotenv import load_dotenv
import redis
import requests

import gcal

load_dotenv()

CONFIG_FILE = "config.json"

CLIENT_ID = os.environ["CLIENT_ID"]
TRAKT_CLIENT_SECRET = os.environ["TRAKT_CLIENT_SECRET"]
IFTTT_KEY = os.environ["IFTTT_KEY"]
IFTTT_EVENT = os.environ["IFTTT_EVENT"]
TRAKT_URL = os.environ["TRAKT_URL"]
REDIS_URL = os.environ["REDIS_URL"]

R = redis.from_url(REDIS_URL)

DEVICE_CODE = "DEVICE_CODE"
ACCESS_TOKEN = "ACCESS_TOKEN"
REFRESH_TOKEN = "REFRESH_TOKEN"
TOKEN_EXPIRY = "TOKEN_EXPIRY"


def redis_string(key: str) -> Optional[str]:
    b = R.get(key)
    return b.decode("utf-8") if b is not None else None


def device_code() -> Dict[str, Any]:
    payload = {
        "client_id": CLIENT_ID
    }

    headers = {
        "Content-Type": "application/json"
    }

    res = requests.post("{}/oauth/device/code".format(TRAKT_URL),
                        data=json.dumps(payload),
                        headers=headers)

    response_data = json.loads(res.text)

    print(
        "Enter {} at {}".format(
            response_data["user_code"],
            response_data["verification_url"]))

    return response_data


def get_token(interval: float, refresh: bool = False):
    if not refresh:
        payload = {
            "code": redis_string(DEVICE_CODE),
            "client_id": CLIENT_ID,
            "client_secret": TRAKT_CLIENT_SECRET
        }
        url = "{}/oauth/device/token"
    else:
        payload = {
            "refresh_token": redis_string(REFRESH_TOKEN),
            "client_id": CLIENT_ID,
            "client_secret": TRAKT_CLIENT_SECRET,
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
            "grant_type": "refresh_token"
        }
        url = "{}/oauth/token"

    headers = {
        "Content-Type": "application/json"
    }

    res = requests.post(url.format(TRAKT_URL),
                        data=json.dumps(payload),
                        headers=headers)
    code = res.status_code

    if code == 200:
        print("Success")
        return json.loads(res.text)
    elif code == 400:
        sleep(interval)
        return get_token(interval)
    elif code == 404:
        print("Not Found")
        exit()
    elif code == 409:
        print("Already Used")
        exit()
    elif code == 410:
        print("Expired")
        code = device_code()
        R.set(DEVICE_CODE, code["device_code"])
        return get_token(code["interval"])
    elif code == 418:
        print("Denied")
        exit()
    elif code == 429:
        print("Slow Down")
    return None


def refresh_token():
    return get_token(5, True)


def checkin(event):
    event = gcal.current_event()

    movie = search(event[0])["movie"]

    payload = {
        "movie": movie,
        "sharing": {
            "facebook": False,
            "twitter": False,
            "tumblr": False
        },
        "message": "",
        "app_version": "1.0",
        "app_date": "2018-04-03"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(redis_string(ACCESS_TOKEN)),
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID
    }

    requests.post("{}/checkin".format(TRAKT_URL),
                  data=json.dumps(payload),
                  headers=headers)

    notify(movie["title"])

    return None


def search(movie):
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': CLIENT_ID
    }

    params = {
        "query": movie,
        "fields": "title"
    }

    params = urlencode(params)

    res = requests.get("{}/search/movie?{}".format(TRAKT_URL, params),
                       headers=headers)

    response_body = json.loads(res.text)

    return response_body[0]


def notify(movie: str) -> None:
    payload = {"value1": movie}
    post_data = urlencode(payload).encode("utf-8")

    res = requests.get("https://maker.ifttt.com/trigger/{}/with/key/{}".format(
                           IFTTT_EVENT,
                           IFTTT_KEY),
                       data=json.dumps(payload))

    print("Checked into {}".format(movie))


def sleep_until(dt: datetime.datetime) -> None:
    sleep_seconds = (dt - datetime.datetime.utcnow()).seconds
    print("Sleeping for {:.2f} minutes".format(sleep_seconds / 60))
    sleep((dt - datetime.datetime.utcnow()).seconds)


def main() -> None:
    interval = 1
    if redis_string(DEVICE_CODE) is None:
        code = device_code()
        interval = code["interval"]
        R.set(DEVICE_CODE, code["device_code"])
    if redis_string(ACCESS_TOKEN) is None:
        token = get_token(interval)
        R.set(ACCESS_TOKEN, token["access_token"])
        R.set(REFRESH_TOKEN, token["refresh_token"])
        R.set(TOKEN_EXPIRY, token["created_at"] + token["expires_in"])

    while True:
        if datetime.datetime.utcnow() >= datetime.datetime.utcfromtimestamp(
                float(redis_string(TOKEN_EXPIRY))):
            print("Access tokens expired, refreshing")
            new_tokens = refresh_token()
            R.set(ACCESS_TOKEN, new_tokens["access_token"])
            R.set(REFRESH_TOKEN, new_tokens["refresh_token"])
            R.set(TOKEN_EXPIRY,
                  new_tokens["created_at"] + new_tokens["expires_in"])

        print("Checking for event")
        event = gcal.current_event()
        if event is not None:
            checkin(event)
            sleep_until(event[-1])
            print("Finished sleeping\n")
            continue
        print("No event found")
        print("Sleeping for 1 minute")
        sleep(60)


if __name__ == "__main__":
    main()

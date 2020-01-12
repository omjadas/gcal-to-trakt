import datetime
from datetime import date
import json
import os
from time import sleep
from typing import Any, Dict
import urllib.error
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv
import redis

import gcal
load_dotenv()

CONFIG_FILE = "config.json"

CLIENT_ID = os.environ["CLIENT_ID"]
TRAKT_CLIENT_SECRET = os.environ["TRAKT_CLIENT_SECRET"]
IFTTT_KEY = os.environ["IFTTT_KEY"]
TRAKT_URL = os.environ["TRAKT_URL"]
REDIS_URL = os.environ["REDIS_URL"]

R = redis.from_url(REDIS_URL)

DEVICE_CODE = R.get("DEVICE_CODE").decode("utf-8") if R.get("DEVICE_CODE") is not None else None
ACCESS_TOKEN = R.get("ACCESS_TOKEN").decode("utf-8") if R.get("ACCESS_TOKEN") is not None else None
REFRESH_TOKEN = R.get("REFRESH_TOKEN").decode("utf-8") if R.get("REFRESH_TOKEN") is not None else None
TOKEN_EXPIRY = R.get("TOKEN_EXPIRY").decode("utf-8") if R.get("TOKEN_EXPIRY") is not None else None


def device_code() -> Dict[str, Any]:
    global CLIENT_ID
    values = {
        "client_id": CLIENT_ID
    }
    post_data = json.dumps(values).encode("utf-8")

    headers = {
        "Content-Type": "application/json"
    }

    request = Request(
        "{}/oauth/device/code".format(TRAKT_URL),
        data=post_data,
        headers=headers)

    response = urlopen(request)

    response_body = response.read()

    response_data = json.loads(response_body)

    print(
        "Enter {} at {}".format(
            response_data["user_code"],
            response_data["verification_url"]))

    return response_data


def get_token(interval: float, refresh: bool = False):
    global DEVICE_CODE, CLIENT_ID, TRAKT_CLIENT_SECRET, REFRESH_TOKEN

    if not refresh:
        values = {
            "code": DEVICE_CODE,
            "client_id": CLIENT_ID,
            "client_secret": TRAKT_CLIENT_SECRET
        }
        url = "{}/oauth/device/token"
    else:
        values = {
            "refresh_token": REFRESH_TOKEN,
            "client_id": CLIENT_ID,
            "client_secret": TRAKT_CLIENT_SECRET,
            "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
            "grant_type": "refresh_token"
        }
        url = "{}/oauth/token"        
    post_data = json.dumps(values).encode("utf-8")

    headers = {
        "Content-Type": "application/json"
    }

    request = Request(url.format(TRAKT_URL), data=post_data, headers=headers)

    try:
        response = urlopen(request)
        code = response.getcode()
    except urllib.error.HTTPError as err:
        code = err.code

    if code == 200:
        print("Success")
        data = json.loads(response.read())
        return data
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
        DEVICE_CODE = code["device_code"]
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
    global ACCESS_TOKEN, CLIENT_ID
    
    event = gcal.current_event()

    movie = search(event[0])["movie"]

    values = {
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
    post_data = json.dumps(values).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(ACCESS_TOKEN),
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID
    }

    request = Request(
        "{}/checkin".format(TRAKT_URL),
        data=post_data,
        headers=headers)

    response = urlopen(request)

    notify(movie["title"])

    return None


def search(movie):
    global CLIENT_ID
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

    request = Request(
        "{}/search/movie?{}".format(TRAKT_URL, params),
        headers=headers)

    response_body = json.loads(urlopen(request).read())

    return response_body[0]


def notify(movie: str) -> None:
    values = {"value1": movie}
    post_data = urlencode(values).encode("utf-8")

    request = Request(
        "https://maker.ifttt.com/trigger/google_cal_trakt_checkin/with/key/{}".format(
            IFTTT_KEY),
        data=post_data)

    urlopen(request)

    print("Checked into {}".format(movie))


def sleep_until(dt: datetime.datetime) -> None:
    sleep_seconds = (dt - datetime.datetime.utcnow()).seconds
    print("Sleeping for {:.2f} minutes".format(sleep_seconds / 60))
    sleep((dt - datetime.datetime.utcnow()).seconds)


def main() -> None:
    global DEVICE_CODE, ACCESS_TOKEN, REFRESH_TOKEN, TOKEN_EXPIRY
    interval = 1
    if DEVICE_CODE is None:
        code = device_code()
        interval = code["interval"]
        DEVICE_CODE = code["device_code"]
        R.set("DEVICE_CODE", DEVICE_CODE)
    if ACCESS_TOKEN is None:
        token = get_token(interval)
        ACCESS_TOKEN = token["access_token"]
        REFRESH_TOKEN = token["refresh_token"]
        TOKEN_EXPIRY = token["created_at"] + token["expires_in"]

    while True:
        if datetime.datetime.utcnow() >= datetime.datetime.utcfromtimestamp(
                TOKEN_EXPIRY):
            print("Access tokens expired, refreshing")
            new_tokens = refresh_token()
            ACCESS_TOKEN = new_tokens["access_token"]
            REFRESH_TOKEN = new_tokens["refresh_token"]
            TOKEN_EXPIRY = (
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

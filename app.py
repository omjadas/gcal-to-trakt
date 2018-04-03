from urllib.request import Request, urlopen
from urllib.parse import urlencode
import urllib.error
import json
import datetime
from time import sleep
import gcal
from copy import deepcopy

TRAKT_URL = "https://api.trakt.tv"
# TRAKT_URL = "https://private-anon-e286eacc07-trakt.apiary-mock.com"


def read_config():
    with open("config.json") as f:
        config_data = json.loads(f.read())
    return config_data


def write_config(config_data):
    with open("config.json", "w") as f:
        json.dump(config_data, f, indent=4)
    print("Written tokens to disk.\n")
    return None


def device_code(config_data):
    values = {
        "client_id": config_data["client_id"]
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


def get_token(config_data, interval):
    values = {
        "code": config_data["device_code"],
        "client_id": config_data["client_id"],
        "client_secret": config_data["client_secret"]
    }
    post_data = json.dumps(values).encode("utf-8")

    headers = {
        "Content-Type": "application/json"
    }

    request = Request(
        "{}/oauth/device/token".format(TRAKT_URL),
        data=post_data,
        headers=headers)

    try:
        response = urlopen(request)
        code = response.getcode()
    except urllib.error.HTTPError as e:
        code = e.code

    if code == 200:
        print("Success")
        data = json.loads(response.read())
        print(data)
        return data
    elif code == 400:
        sleep(interval)
        return get_token(config_data, interval)
    elif code == 404:
        print("Not Found")
    elif code == 409:
        print("Already Used")
    elif code == 410:
        print("Expired")
        code = device_code(config_data)
        config_data["device_code"] = code["device_code"]
        return get_token(config_data, code["interval"])
    elif code == 418:
        print("Denied")
        exit()
    elif code == 429:
        print("Slow Down")
    return None


def refresh_token(config_data):
    my_data = deepcopy(config_data)
    my_data["device_code"] = my_data["refresh_token"]
    return(get_token(my_data, 5))


def checkin(config_data, event):
    event = gcal.current_event("Movies")

    movie = search(config_data, event[0])["movie"]

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
        "Authorization": config_data["access_token"],
        "trakt-api-version": "2",
        "trakt-api-key": config_data["client_id"]
    }

    request = Request(
        "{}/checkin".format(TRAKT_URL),
        data=post_data,
        headers=headers)

    response = urlopen(request)

    notify(config_data, movie["title"])

    return None


def search(config_data, movie):
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': config_data["client_id"]
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


def notify(config_data, movie):
    values = {"value1": movie}
    post_data = urlencode(values).encode("utf-8")

    request = Request(
        "https://maker.ifttt.com/trigger/google_cal_trakt_checkin/with/key/{}".format(
            config_data["ifttt_key"]),
        data=post_data)

    urlopen(request)

    print("Checked into {}".format(movie))
    return None


def sleep_until(dt):
    sleep_seconds = (dt - datetime.datetime.utcnow()).seconds
    print("Sleeping for {:.2f} minutes".format(sleep_seconds / 60))
    sleep((dt - datetime.datetime.utcnow()).seconds)
    return None


def main():
    config_data = read_config()
    if "device_code" not in config_data:
        code = device_code(config_data)
        config_data["device_code"] = code["device_code"]
    if "access_token" not in config_data:
        token = get_token(config_data, code["interval"])
        config_data["access_token"] = token["access_token"]
        config_data["refresh_token"] = token["refresh_token"]
        config_data["token_expiry"] = token["created_at"] + token["expires_in"]
        write_config(config_data)

    while True:
        if datetime.datetime.utcnow() >= datetime.datetime.fromtimestamp(
                config_data["token_expiry"]):
            token = refresh_token(config_data)
            config_data["access_token"] = token["access_token"]
            config_data["refresh_token"] = token["refresh_token"]
            config_data["token_expiry"] = (
                token["created_at"] + token["expires_in"])

        print("Checking for event")
        event = gcal.current_event("Movies")
        if event is not None:
            checkin(config_data, event)
            sleep_until(event[-1])
            print("Finished sleeping\n")
            continue
        print("No event found")
        print("Sleeping for 5 minutes")
        sleep(300)


if __name__ == "__main__":
    main()

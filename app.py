from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json
from time import sleep


def read_config():
    config_file = open("config.json")
    config_str = config_file.read()
    config_file.close()
    config_data = json.loads(config_str)
    return config_data


def device_code(config_data):
    values = {
        "client_id": config_data["client_id"]
    }
    post_data = json.dumps(values).encode("utf-8")

    headers = {
        "Content-Type": "application/json"
    }

    request = Request(
        "https://private-anon-e286eacc07-trakt.apiary-mock.com/oauth/device/code",
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


def get_token(config_data):
    values = {
        "code": config_data["code"],
        "client_id": config_data["client_id"],
        "client_secret": config_data["client_secret"]
    }
    post_data = json.dumps(values).encode("utf-8")

    headers = {
        "Content-Type": "application/json"
    }

    request = Request(
        "https://private-anon-e286eacc07-trakt.apiary-mock.com/oauth/device/token",
        data=post_data,
        headers=headers)

    response = urlopen(request)

    if response.getcode() == 200:
        print("Success")
        return json.loads(response.read())
    elif response.getcode() == 400:
        sleep(5.0)
        return device_code(config_data)
    elif response.getcode() == 404:
        print("Not Found")
    elif response.getcode() == 409:
        print("Already Used")
    elif response.getcode() == 410:
        print("Expired")
    elif response.getcode() == 418:
        print("Denied")
    elif response.getcode() == 429:
        print("Slow Down")
    return None


def checkin(config_data):
    values = {
        "movie": {
            "title": "Guardians of the Galaxy",
            "year": 2014,
            "ids": {
                "trakt": 28,
                "slug": "guardians-of-the-galaxy-2014",
                "imdb": "tt2015381",
                "tmdb": 118340
            }
        },
        "sharing": {
            "facebook": False,
            "twitter": False,
            "tumblr": False
        },
        "message": "Guardians of the Galaxy FTW!",
        "app_version": "1.0",
        "app_date": "2014-09-22"
    }
    post_data = json.dumps(values).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": config_data["access_token"],
        "trakt-api-version": "2",
        "trakt-api-key": config_data["client_id"]
    }

    request = Request(
        "https://private-anon-e286eacc07-trakt.apiary-mock.com/checkin",
        data=post_data,
        headers=headers)

    response = urlopen(request)

    notify(config_data, "Avengers")

    return None


def search():
    headers = {
        'Content-Type': 'application/json',
        'trakt-api-version': '2',
        'trakt-api-key': '[client_id]'
    }

    request = Request(
        'https://private-anon-e286eacc07-trakt.apiary-mock.com/search/type',
        headers=headers)

    pass


def notify(config_data, movie):
    values = {"value1": movie}
    post_data = urlencode(values).encode("utf-8")

    request = Request(
        "https://maker.ifttt.com/trigger/google_cal_trakt_checkin/with/key/{}".format(
            config_data["ifttt_key"]),
        data=post_data)

    response = urlopen(request).read()

    print(response)
    return None


def main():
    config_data = read_config()
    code = device_code(config_data)
    config_data["code"] = code["device_code"]
    token = get_token(config_data)
    config_data["access_token"] = token["access_token"]
    config_data["refresh_token"] = token["refresh_token"]
    checkin(config_data)


if __name__ == "__main__":
    main()

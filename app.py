from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json
import datetime
import pause


def read_config():
    with open("config.json") as f:
        config_data = json.loads(f.read())
    return config_data


def write_config(config_data):
    with open("config.json", "w") as f:
        json.dump(config_data, f, indent=4)
    print("Written tokens to disk.")
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
        "code": config_data["device_code"],
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
        pause.seconds(5.0)
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
        "https://private-anon-e286eacc07-trakt.apiary-mock.com/search/movie?{}".format(
            params),
        headers=headers)

    response_body = json.loads(urlopen(request).read())

    print(response_body[0])

    pass


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


def main():
    config_data = read_config()
    code = device_code(config_data)
    config_data["device_code"] = code["device_code"]
    token = get_token(config_data)
    config_data["access_token"] = token["access_token"]
    config_data["refresh_token"] = token["refresh_token"]
    write_config(config_data)

    checkin(config_data)


if __name__ == "__main__":
    main()

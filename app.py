from urllib.request import Request, urlopen
import json


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

    response_body = urlopen(request).read()

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

    print(response)

    response_body = response.read()

    print(response_body)

    return json.loads(response_body)


def checkin(movie, config_data):
    values = {}

    headers = {
        "Content-Type": "application/json",
        "Authorization": config_data["access_token"],
        "trakt-api-version": "2",
        "trakt-api-key": config_data["client_id"]
    }

    print(headers)

    request = Request(
        "https://private-anon-e286eacc07-trakt.apiary-mock.com/checkin",
        data=values,
        headers=headers)

    response_body = urlopen(request).read()

    pass


def main():
    config_data = read_config()
    code = device_code(config_data)
    config_data["code"] = code["device_code"]
    token = get_token(config_data)
    config_data["access_token"] = token["access_token"]
    config_data["refresh_token"] = token["refresh_token"]
    print(config_data)
    # checkin(config_data)


if __name__ == "__main__":
    main()

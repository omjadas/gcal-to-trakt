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
        "client_id": config_data["trakt"]["client_id"]
    }

    post_data = json.dumps(values).encode("utf-8")

    headers = {
        'Content-Type': 'application/json'
    }

    request = Request(
        'https://private-anon-e286eacc07-trakt.apiary-mock.com/oauth/device/code',
        data=post_data,
        headers=headers)

    response_body = urlopen(request).read()

    response_data = json.loads(response_body)

    print(
        "Enter {} at {}".format(
            response_data["user_code"],
            response_data["verification_url"]))

    return response_data


def main():
    config_data = read_config()
    device_code(config_data)


if __name__ == "__main__":
    main()

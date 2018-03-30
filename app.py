import config
from urllib.request import Request, urlopen
import json

values = {
        "client_id": config.trakt["client_id"]
    }

data = json.dumps(values).encode("utf-8")

headers = {
    'Content-Type': 'application/json'
}
request = Request(
    'https://private-anon-e286eacc07-trakt.apiary-mock.com/oauth/device/code',
    data=data,
    headers=headers)

response_body = urlopen(request).read()
print(response_body)

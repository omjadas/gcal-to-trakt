import datetime
import os
from typing import Optional, Tuple

from dotenv import load_dotenv
from google_calendar_api.client import GoogleCalendarClient

load_dotenv()

CALENDAR_ID = os.environ["CALENDAR_ID"]
GCAL_CLIENT_SECRET = os.environ["GCAL_CLIENT_SECRET"]
CLIENT_SECRET_LOCATION = "client_secret.json"

with open(CLIENT_SECRET_LOCATION, "w") as client_secret_file:
    client_secret_file.write(GCAL_CLIENT_SECRET)

CLIENT = GoogleCalendarClient(
    calendar_id=CALENDAR_ID,
    client_secrete_file=CLIENT_SECRET_LOCATION)

os.remove(CLIENT_SECRET_LOCATION)


def current_event() -> Optional[Tuple[Optional[str],
                                      Optional[str],
                                      datetime.datetime]]:
    """Finds the current event in the calendar with the summary cal_summary"""
    events = CLIENT.get_events()
    current = datetime.datetime.utcnow()

    if not events:
        print('No event found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        start_utc = convert_to_datetime(start)
        end_utc = convert_to_datetime(end)

        if start_utc < current < end_utc:
            return(event.get("summary"), event.get("description"), end_utc)
    return None


def convert_to_datetime(date_string: str) -> datetime.datetime:
    time = datetime.datetime.strptime(date_string[0:-6], "%Y-%m-%dT%H:%M:%S")
    t = datetime.datetime.strptime(date_string[-5:], "%H:%M")
    delta = datetime.timedelta(hours=t.hour, minutes=t.minute)
    utc = (time - delta if (date_string[-6] == "+") else time + delta)
    return utc


if __name__ == "__main__":
    print(current_event())

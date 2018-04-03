from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = os.path.dirname(os.path.realpath(__file__))
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path + '\n')
    return credentials


def current_event(cal_summary):
    """Finds the current event in the calendar with the summary cal_summary"""
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    current = datetime.datetime.utcnow()

    now = current.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    calendars = service.calendarList().list().execute().get('items', [])

    calendar = next(
        item for item in calendars if item["summary"] == cal_summary)

    eventsResult = service.events().list(
        calendarId=calendar["id"], timeMin=now, maxResults=1, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        start_utc = convert_to_datetime(start)
        end_utc = convert_to_datetime(end)

        if (start_utc < current < end_utc):
            return(event.get("summary"), event.get("description"), end_utc)
    return None


def convert_to_datetime(date_string):
    time = datetime.datetime.strptime(date_string[0:-6], "%Y-%m-%dT%H:%M:%S")
    t = datetime.datetime.strptime(date_string[-5:], "%H:%M")
    delta = datetime.timedelta(hours=t.hour, minutes=t.minute)
    utc = (time - delta if (date_string[-6] == "+") else time + delta)
    return utc


if __name__ == '__main__':
    print(current_event("Movies"))

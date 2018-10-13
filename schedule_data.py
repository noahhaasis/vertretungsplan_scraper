import dropbox
import requests
from datetime import datetime
from itertools import count
from os import environ
from time import sleep
from typing import List


def is_friday() -> bool:
    return current_weekday() == 4

def is_weekend() -> bool:
    return current_weekday() in [5, 6]

def current_day() -> int:
    return datetime.today().day

def current_weekday() -> int:
    return datetime.today().weekday()

def current_week() -> int:
    return datetime.today().isocalendar()[1]

def current_year() -> int:
    return datetime.today().year

BASE_URL = "https://www.wvsgym.de/vertretungsplans/"
def url_for_class(class_index: int) -> str:
    return '{0}{1:02d}/c/c{2:05d}.htm'.format(BASE_URL, current_week(), class_index)

def url_for_week_summary():
    return '{0}{1:02d}/w/w00000.htm'.format(
            BASE_URL,
            current_week())

USERNAME = environ['school_username']
PASSWORD = environ['school_password']
def fetch_table(class_index: int) -> str:
    url = url_for_class(class_index)
    response = requests.get(url, auth=(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.text
    return None

def fetch_week_summary() -> str:
    url = url_for_week_summary()
    response = requests.get(url, auth=(USERNAME, PASSWORD))
    if response.status_code == 200:
        return response.text
    return None

def fetch_tables() -> List[str]:
    tables = []
    for i in count(1):
        table = fetch_table(i)
        if not table:
            return tables

        tables.append(table)

def filename_for_class(class_index: int) -> str:
    return '{}_{}__{}.html'.format(current_year(), current_week(), class_index)

def filename_for_week_summary() -> str:
    return '{}_{}_{}__summary.html'.format(
            current_year(), current_day(), current_week())

def store_table_in_dropbox(dbx, table: str, filename: str) -> None:
    dbx.files_upload(table.encode(), '/' + filename)

last_stored_day = None
def store_tables(tables: List[str]) -> None:
    global last_stored_day
    dbx = dropbox.Dropbox(environ['dropbox_access_token'])
    for i, table in enumerate(tables):
        filename = filename_for_class(i+1)
        store_table_in_dropbox(dbx, table, filename)
    last_stored_day = current_day()

last_stored_summary_day = None
def store_week_summary(summary: str):
    global last_stored_summary_day
    dbx = dropbox.Dropbox(environ['dropbox_access_token'])
    dbx.files_upload(summary.encode(), '/' + filename_for_week_summary())
    last_stored_summary_day = current_day()

def already_stored_tables_today() -> bool:
    return last_stored_day is not None and last_stored_day == current_day()

def already_stored_summary_today() -> bool:
    stored_today = last_stored_summary_day == current_day()
    return last_stored_summary_day is not None and stored_today

def main() -> None:
    HOUR = 60 * 60

    while True:
        if is_friday() and not already_stored_tables_today():
            store_tables(fetch_tables())

        if not (is_weekend() or already_stored_summary_today()):
            store_week_summary(fetch_week_summary())

        sleep(HOUR * 5)

if __name__ == '__main__':
    main()

import dropbox
import requests from datetime import datetime
from itertools import count
from os import environ
from time import sleep
from typing import List


def is_friday() -> bool:
    return datetime.today().weekday() == 4

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

def fetch_all_tables() -> List[str]:
    tables = []
    for i in count(1):
        table = fetch_table(i)
        if not table:
            return tables

        tables.append(table)

def filename_for_class(class_index: int) -> str:
    return '{}_{}__{}.html'.format(current_year(), current_week(), class_index)

def filename_for_week_summary() -> str:
    return '{}_{}__summary'.format(current_year(), current_week())

def store_table_in_dropbox(dbx, table: str, filename: str) -> None:
    dbx.files_upload(table.encode(), '/' + filename)

last_stored_day = None
def store_tables(tables: List[str]) -> None:
    dbx = dropbox.Dropbox(environ['dropbox_access_token'])
    for i, table in enumerate(tables):
        filename = filename_for_class(i+1)
        store_table_in_dropbox(dbx, table, filename)
    last_stored_day = datetime.today().day

def store_week_summary(summary: str):
    dbx = dropbox.Dropbox(environ['dropbox_access_token'])
    dbx.files_upload(summary.encode, '/' + filename_for_week_summary)

def already_stored_today() -> bool:
    return last_stored_day is not None and last_stored_day == datetime.today().day

def main() -> None:
    HOUR = 60 * 60
    DAY = HOUR * 24

    while True:
        if is_friday() and not already_stored_today():
            tables = fetch_all_tables()
            store_tables(tables)

            summary = fetch_week_summary(summary)
            store_week_summary(summary)
            sleep(DAY * 4)

        sleep(HOUR * 5)

if __name__ == '__main__':
    main()

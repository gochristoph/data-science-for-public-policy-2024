"""
Template scraping script for a rate-limited API that is returning documents
in a paginated manner. 

2023, Christoph Goessmann (ETH Zurich)
"""

from datetime import date, timedelta
import requests
import base64
import json
from cachetools import cached, TTLCache
from tenacity import retry, stop_after_attempt, wait_fixed
from limit import limit
import psycopg
import logging

logging.basicConfig(format='%(asctime)s  %(message)s', 
                    datefmt='%y-%m-%d %H:%M:%S', 
                    filename='lexis_cases_scraper.log', 
                    #encoding='utf-8', 
                    level=logging.INFO)

# manually set scraping parameters
start_date = date.fromisoformat('2017-01-01')
start_offset = 0
end_date = date.fromisoformat('2022-12-31')

# create auth headers once and cache it for, e.g., 12 hours
@cached(cache=TTLCache(maxsize=1, ttl=43200))
def create_auth_headers():
    # TODO: implement header retrieval
    return headers

def render_url(offset, start_date, end_date):
    # TODO: render url, e.g., 
    # url= f"https://some_service_api.url/v1/Cases?$start={offset}&$date1={start_date}&$date2={end_date}"
    return url

# limit the number of requests to, e.g., 1 per 88 seconds (= 1000 per day)
@limit(1, 88)
@retry(stop=stop_after_attempt(5), wait=wait_fixed(88))
def get_cases(offset, start_date, end_date):
    url = render_url(offset, start_date, end_date)
    auth_headers = create_auth_headers()
    r = requests.get(url, headers=auth_headers)
    if r.status_code != 200:
            logging.error(f'Error: {r.status_code} {r.text} for date {date}, offset {offset}.')
            raise Exception (f'Error: {r.status_code} {r.text} for date {date}, offset {offset}.')
    # TODO: need to adapt here depending on how the API is returning its data
    data = r.json()
    cases = data['value']
    n_cases = len(cases)
    n_cases_total = data['@odata.count']
    return cases, n_cases, n_cases_total

@retry(stop=stop_after_attempt(5), wait=wait_fixed(30))
def write_cases_to_db(cases):
    # TODO: this could also be writing to a csv file
    sql = "INSERT INTO api_scrape_20170101_to_20221231 (document_id, response_json) VALUES (%s, %s) ON CONFLICT (resultid) DO NOTHING"
    with psycopg.connect("dbname=led") as conn:
        with conn.cursor() as cur:
            for case in cases:
                # here we extract the document_id from the json, but also write the entire document json
                cur.execute(sql, (case['doument_id'], json.dumps(case)))
    logging.info('  -> Writing to db is done.')


# this is where this actual scrape is performed
logging.info(f'STARTING NEW SCRAPE FOR DATE RANGE {start_date} to {end_date}.')

date = start_date

while date <= end_date:
    offset = 0
    
    # if we are starting from a specific offset, use that
    if start_offset is not None:
        offset = start_offset
        start_offset = None
    
    # n_cases = None

    # loop through all pages of cases for a given date
    while True:
        cases, n_cases, n_cases_total = get_cases(offset, date, date)
        logging.info(f'Found {n_cases_total} cases in total for date {date}, {n_cases} with offset {offset}.')
        write_cases_to_db(cases)
        
        # if there are less than 50 cases, there are no more pages
        if n_cases != 50:
            break
        else:
            offset = offset + 50 
    
    date = date + timedelta(days=1)

logging.info(f'FINISHED SCRAPE FOR DATE RANGE {start_date} to {end_date}.')
import utils
import config
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests_ip_rotator import ApiGateway
import json

proxy = {
    "https": 'https://104.248.57.192:8080',
    "http": 'https://104.248.57.192:8080'
}


missing_jobs = pd.read_sql_query(config.missing_job_details_select_sql, con=utils.db_connection())
missing_jobs_list = missing_jobs.to_dict('records')

with open('../1. Admin/gateway_setup.json') as json_data:
    api_data = json.load(json_data)
    gateway = ApiGateway("https://www.seek.com.au",
                         access_key_id=api_data['access_key_id'],
                         access_key_secret=api_data['access_key_secret'])
    gateway.start()

session = requests.Session()
session.mount("https://www.seek.com.au", gateway)

for x in missing_jobs_list[0:10]:
    try:
        base_link = 'https://www.seek.com.au'
        job_link = base_link + x['job_link']
        job_page = session.get(job_link, headers=config.headers)
        job_page_soup = BeautifulSoup(job_page.text, 'html.parser')
        x['job_ad_details'] = job_page_soup.find(attrs={'data-automation': 'jobAdDetails'}).getText()
        print(x['job_ad_details'])
    except:
        print(f'Temp fix only for {x["job_link"]}')

gateway.shutdown()

#exception_list = utils.search_job_ad_details(missing_jobs_list)

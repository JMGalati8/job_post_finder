import utils
import config
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests_ip_rotator import ApiGateway
import json

print('Job details process starting')
missing_jobs = pd.read_sql_query(config.missing_job_details_select_sql, con=utils.db_connection())
missing_jobs_list = missing_jobs.to_dict('records')
#exception_list = utils.search_job_ad_details(missing_jobs_list)


output_list = []
for x in missing_jobs_list[0:3]:
    output_list.append(x)

print(output_list)
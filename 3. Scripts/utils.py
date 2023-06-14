import requests
from bs4 import BeautifulSoup
import time
import random
import datetime
import config
import pandas as pd
import numpy as np
import psycopg2
from psycopg2 import OperationalError
import json
import re
import logging
from requests_ip_rotator import ApiGateway

logger = logging.getLogger(__name__)


def sleeper(min_second=0.2, max_second=2):
    """

    :param min_second: minimum seconds
    :param max_second: maximum seconds
    :return: sleep for random period between min and max seconds

    :note: Need to update this to have proper handling for the seconds
    """
    multiplier = 10
    min_time = min_second * multiplier
    max_time = max_second * multiplier
    time.sleep(random.randint(min_time, max_time) / multiplier)


def db_connection():
    with open('../1. Admin/db_data.json') as json_data:
        db_data = json.load(json_data)
        conn = create_connection(
            db_data['db_name'], db_data['db_user'], db_data['db_password'], db_data['db_host'], db_data['db_port']
        )

    return conn


def job_info_handler(job_soup):
    """
    :param job_soup: The html of the jobs - This is a list of the html for each job. Each entry is one job.
    :return: Return a list of jobs in dictionaries. Details of the jobs are contained in the dictionaries.
    """
    job_output = []
    for j in job_soup:

    #Create the dictionary that gets output for each job. Specific handling for each item is in the config file.
        job_info = {
            'job_type': '',
            "job_name": "",
            "company": "",
            "location": "",
            "pay": "",
            "category": "",
            'sub_category': '',
            "first_seen": datetime.datetime.now(),
            "job_link": "",
            "site_id": ""
        }

        for k, v in config.attributes.items():
            var = j.find(attrs=v)
            if var:
                job_info[k] = var.getText()

            # This is terrible, look for a solution
            job_info['job_link'] = j.find(attrs={'data-automation': 'jobTitle'})['href']
            job_info['site_id'] = re.search('(\d+)', job_info['job_link']).group(0)

        job_output.append(job_info)

    return job_output


def search_site(site_link):
    """
    :param site_link: The site link that is to be searched - Currently just a an entry in config, will need to consider how to develop further.
    :return: Returns all jobs from the page after looping through all pages.
    """
    page_number = 1
    output_list = []
    start_flag = True
    while start_flag:
        link = site_link + str(page_number)
        page = requests.get(link)
        html_soup = BeautifulSoup(page.text, 'html.parser')
        norm_jobs = html_soup.find_all("article", {"data-automation": "normalJob"})
        prem_job = html_soup.find_all("article", {"data-automation": "premiumJob"})
        norm_jobs.extend(prem_job)

        if not norm_jobs:
            break

        output_list.extend(job_info_handler(norm_jobs))
        sleeper()
        page_number += 1

    return output_list


def remove_previous_entries(job_ad_list):
    """
    Moved this out of the 'search site' function as there were times where we were dropping all records and it was causing issues
    :param job_ad_list: List of job ads from the 'search site' function
    :return: Same list but with all entries already in db removed
    """
    existing_id = pd.read_sql_query(config.existing_id_sql, con=db_connection())['site_id'].tolist()
    job_ad_list[:] = [d for d in job_ad_list if d.get('site_id') not in existing_id]

    return job_ad_list


def search_job_ad_details(job_info_list):
    """
    :param job_info_list: Cleaned list of jobs broken into individual dictionaries
    :return: Returns the cleaned list of jobs with the job description added to each entry.
    """
    with open('../1. Admin/gateway_setup.json') as json_data:
        api_data = json.load(json_data)
        gateway = ApiGateway("https://www.seek.com.au",
                             access_key_id=api_data['access_key_id'],
                             access_key_secret=api_data['access_key_secret'])
        gateway.start()

    session = requests.Session()
    session.mount("https://www.seek.com.au", gateway)

    exception_list = []
    for x in job_info_list:
        try:
            base_link = 'https://www.seek.com.au'
            job_link = base_link + x['job_link']
            job_page = session.get(job_link, headers=config.headers)
            job_page_soup = BeautifulSoup(job_page.text, 'html.parser')
            x['job_ad_details'] = job_page_soup.find(attrs={'data-automation': 'jobAdDetails'}).getText()
            print('Success')
        except AttributeError:
            exception_list.extend(x)
            logger.error('Attribute Error in Job Ad Details')
        except requests.exceptions.TooManyRedirects:
            exception_list.extend(x)
            logger.error('Too Many Redirects Error in Job Ad Details')
            print('Too many redirects')
        sleeper()

    gateway.shutdown()
    print('Job Details Completed')
    return exception_list


def remove_exception_jobs(results_list, exceptions_list):
    exception_ids = [x for x in ((d.get('id', -9999) for d in exceptions_list))]
    results_list[:] = [d for d in results_list if d.get('site_id') not in exception_ids]


def create_sql_insert_query(df, table):

    # Comma-separated dataframe columns
    cols = ','.join(list(df.columns))
    tuple_values = ','.join(['%%s' for x in list(df.columns)])
    # SQL quert to execute
    query = f"INSERT INTO %s(%s) VALUES({tuple_values})" % (table, cols)

    return query


def create_connection(db_name, db_user, db_password, db_host, db_port):
    """

    :param db_name: database name
    :param db_user: username
    :param db_password: password
    :param db_host: host location
    :param db_port: port to access
    :return: Gives us the connection to db
    """
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


def execute_many(conn, df, table):
    """
    This is an insert command, so the table needs to be created already.
    :param conn: pre-created connection to db
    :param df: df to insert
    :param table: table to insert df into
    :return: insert records into a table
    """
    # Create a list of tupples from the dataframe values
    tuples = [tuple(x) for x in df.to_numpy()]
    query = create_sql_insert_query(df, table)
    cursor = conn.cursor()
    try:
        cursor.executemany(query, tuples)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    print("execute_many() done")
    cursor.close()


def job_info_process():

    print('Search Site')
    results = []
    for job_classification in config.classification_search_list:
        seek_link = f'https://www.seek.com.au/{job_classification}?daterange={config.daterange}&page='
        print(job_classification)
        site_results = search_site(seek_link)
        print(len(site_results))
        results.extend(site_results)
    results = remove_previous_entries(results)
    conn = db_connection()
    job_details_df = pd.DataFrame(results)
    execute_many(conn, job_details_df, 'jobs_details')
    conn.cursor().execute(config.missing_job_details_insert_sql)
    conn.commit()
    print('Job info search complete')


def job_details_process():
    print('Job details process starting')
    missing_jobs = pd.read_sql_query(config.missing_job_details_select_sql, con=db_connection())
    missing_jobs_list = missing_jobs.to_dict('records')
    exception_list = search_job_ad_details(missing_jobs_list)
    pd.DataFrame(exception_list).to_csv('../4. Testing/Exception_List.csv', index=False)
    remove_exception_jobs(missing_jobs_list, exception_list)
    df = pd.DataFrame(missing_jobs_list)
    df = df.replace(r'^\s*$', np.nan, regex=True)
    print(f'Writing data to db - {df.shape[0]} rows')
    conn = db_connection()
    execute_many(conn, df, 'jobs_details')


def seek_process():
    """
    Complete seek process, scraping details and saving these into the pre-defined table
    :return: update db

    :note: Need to improve this with logging and messages. Also update the connection details to work off a json before we save to git
    """

    #print(f'Getting job details for {len(results)} jobs')
    #exception_list = search_job_ad_details(results)
    #remove_exception_jobs(results, exception_list)
    #pd.DataFrame(exception_list).to_csv('../4. Testing/Exception_List.csv', index=False)
    #df = pd.DataFrame(results)
    #df = df.replace(r'^\s*$', np.nan, regex=True)
    #print(f'Writing data to db - {df.shape[0]} rows')
    #execute_many(conn, df, 'jobs_details')
    return None

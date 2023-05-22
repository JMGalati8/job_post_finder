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
            "posted_date": datetime.datetime.now(),
            "job_link": "",
            "site_id": ""
        }

        for k, v in config.attributes.items():
            var = j.find(attrs=v)
            if var:
                job_info[k] = var.getText()

            # This is terrible, look for a solution
            job_info['job_link'] = j.find(attrs={'data-automation': 'jobTitle'})['href']

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


def search_job_ad_details(job_info_list):
    """
    :param job_info_list: Cleaned list of jobs broken into individual dictionaries
    :return: Returns the cleaned list of jobs with the job description added to each entry.
    """
    for x in job_info_list:
        base_link = 'https://www.seek.com.au'
        job_link = base_link + x['job_link']
        job_page = requests.get(job_link)
        job_page_soup = BeautifulSoup(job_page.text, 'html.parser')
        x['job_ad_details'] = job_page_soup.find(attrs={'data-automation': 'jobAdDetails'}).getText()
        sleeper()

    print('Job Details Completed')


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
    # Comma-separated dataframe columns
    cols = ','.join(list(df.columns))
    # SQL quert to execute
    query = "INSERT INTO %s(%s) VALUES(%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s,%%s)" % (table, cols)
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


def seek_process():
    """
    Complete seek process, scraping details and saving these into the pre-defined table
    :return: update db

    :note: Need to improve this with logging and messages. Also update the connection details to work off a json before we save to git
    """
    seek_link = 'https://www.seek.com.au/jobs?daterange=1&page='
    print('Search Site')
    results = search_site(seek_link)
    print('Getting job details')
    search_job_ad_details(results)
    df = pd.DataFrame(results)
    df = df.replace(r'^\s*$', np.nan, regex=True)
    df['site_id'] = df['job_link'].str.extract('(\d+)')
    print('Writing data to db')

    with open('../1. Admin/db_data.json') as json_data:
        db_data = json.load(json_data)
        conn = create_connection(
            db_data['db_name'], db_data['db_user'], db_data['db_password'], db_data['db_host'], db_data['db_port']
        )

    execute_many(conn, df, 'jobs_details')

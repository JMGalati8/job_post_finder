job_types = {
    'normal':{"data-automation": "normalJob"},
    'sponsored':{"data-automation": "premiumJob"}
}

attributes ={
    'job_name': {'data-automation': 'jobTitle'},
    'company': {'data-automation': 'jobCompany'},
    'location': {'data-automation': 'jobLocation'},
    'pay': {'data-automation': 'jobSalary'},
    'category': {'data-automation': 'jobClassification'},
    'sub_category': {'data-automation': 'jobSubClassification'},
    'job_link': {'data-automation': 'jobSubClassification'}
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
           'Accept-Language': 'en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
           'Accept-Encoding': 'gzip, deflate, br',
           'upgrade-insecure-requests': '1',
           'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
           'sec-ch-ua-platform': '"Windows"'
           }

daterange=2

existing_id_sql = f'select site_id from jobs_details where first_seen >= current_date-{daterange}'

classification_search_list = [
    'jobs-in-administration-office-support',
    'jobs-in-accounting',
    'jobs-in-advertising-arts-media',
    'jobs-in-banking-financial-services',
    'jobs-in-call-centre-customer-service',
    'jobs-in-ceo-general-management',
    'jobs-in-community-services-development',
    'jobs-in-construction',
    'jobs-in-consulting-strategy',
    'jobs-in-design-architecture',
    'jobs-in-education-training',
    'jobs-in-engineering',
    'jobs-in-farming-animals-conservation',
    'jobs-in-government-defence',
    'jobs-in-healthcare-medical',
    'jobs-in-hospitality-tourism',
    'jobs-in-human-resources-recruitment',
    'jobs-in-information-communication-technology',
    'jobs-in-insurance-superannuation',
    'jobs-in-legal',
    'jobs-in-manufacturing-transport-logistics',
    'jobs-in-marketing-communications',
    'jobs-in-mining-resources-energy',
    'jobs-in-real-estate-property',
    'jobs-in-retail-consumer-products',
    'jobs-in-sales',
    'jobs-in-science-technology',
    'jobs-in-self-employment',
    'jobs-in-sport-recreation',
    'jobs-in-trades-services'
]

missing_job_details_insert_sql = """
insert into missing_job_details(id, job_link) 
select
    id,
    job_link 
from jobs_details 
where job_ad_details is null
	"""

missing_job_details_select_sql = """
select 
	*
from jobs_details
where id in (select id from missing_job_details)
"""

missing_job_details_delete_sql = """
delete from missing_job_details
where id in (
    select 
        a.id
    from missing_job_details a
    inner join jobs_details b 
        on a.id = b.id 
    where b.job_ad_details is not null 
    );
"""
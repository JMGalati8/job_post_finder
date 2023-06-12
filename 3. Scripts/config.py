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
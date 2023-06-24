import utils
import config
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests_ip_rotator import ApiGateway
import json

df = pd.read_csv('../4. Testing/test_df_output.csv')
print(df.loc[~df['job_ad_details'].isna()])
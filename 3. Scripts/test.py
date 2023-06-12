import utils
import config
import pandas as pd

conn = utils.sql_conn()
cur = conn.cursor()
cur.execute(config.missing_job_details_insert_sql)
conn.commit()
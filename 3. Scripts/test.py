import utils
import config
import pandas as pd

df = pd.DataFrame(config.attributes)

print(utils.create_sql_insert_query(df, 'table_name'))
import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import calendar
from clickhouse_driver import Client
from dash.dependencies import Input, Output
from datetime import datetime
import warnings
warnings.filterwarnings(action='once')
from time import sleep
# DF TO COPY FROM
client = Client(host='54.227.137.142',
                user='default',
                password='',
                port='9000',
                database='superstore')

column_names_ch = client.execute(f'SHOW CREATE telco')
string = column_names_ch[0][0]
lst = string.split('`')
column_names_duplicated = lst[1::2]
# MAINTAIN THE ORDER
column_names = list(dict.fromkeys(column_names_duplicated))

df = pd.DataFrame(client.execute(f'select * from superstore.telco;'))
df.columns = column_names



# PART OF THE DF
client = Client(host='10.0.0.218',
                user='aisurgeclick',
                password='M9YfSU7P1R',
                port='9000',
                database='aisurgeclickdb')


df_1 = df[:8000].copy()
# print(len(df_1))
# df_2 = df[9000:18000].copy()
# df_3 = df[18000:27000].copy()
# df_4 = df[27000:36000].copy()
# df_5 = df[36000:45000].copy()
# print(len(df_5))

print(df_1)
client.execute(f"INSERT INTO aisurgeclickdb.telco VALUES", df_1.values.tolist())
print(f"NEW ROWS WERE ADDED SUCCESSFULY")
print(client.execute(f"SELECT count(*) FROM aisurgeclickdb.telco"))

















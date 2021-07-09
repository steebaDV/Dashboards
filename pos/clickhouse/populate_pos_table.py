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

df = pd.DataFrame(client.execute(f'select * from superstore.point_of_sales'))

columns = client.execute((f'SHOW CREATE point_of_sales'))
string = columns[0][0]
lst = string.split('`')
column_names = lst[1::2]
df.columns = column_names

# POS
# PART OF THE DF
client = Client(host='10.0.0.218',
                user='aisurgeclick',
                password='M9YfSU7P1R',
                port='9000',
                database='aisurgeclickdb')


df_1 = df[:7000].copy()
print(len(df_1))
df_2 = df[7000:14000].copy()
df_3 = df[14000:21000].copy()

df_parts = [df_1, df_2, df_3]

for part in df_parts:
    client.execute(f"INSERT INTO aisurgeclickdb._PointOfSales VALUES", part.values.tolist())
    print(f"NEW ROWS WERE ADDED SUCCESSFULY")
    sleep(1)


print(client.execute(f"SELECT count(*) FROM aisurgeclickdb._PointOfSales"))


















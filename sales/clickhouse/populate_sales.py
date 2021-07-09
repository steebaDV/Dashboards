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

df = pd.DataFrame(client.execute(f'select * from superstore.sales'))
# sales
df.columns = ['DateTime', 'Customer', 'Country', 'Product', 'Business Line', 'Total Sales', 'Sales Amount Target', 'Total Sold Quantity', 'Total Sales Margin']

# PART OF THE DF
client = Client(host='10.0.0.218',
                user='aisurgeclick',
                password='M9YfSU7P1R',
                port='9000',
                database='aisurgeclickdb')


df_1 = df[:9000].copy()
print(len(df_1))
df_2 = df[9000:18000].copy()
df_3 = df[18000:27000].copy()
df_4 = df[27000:36000].copy()
df_5 = df[36000:45000].copy()
print(len(df_5))

client.execute(f"INSERT INTO aisurgeclickdb.sales VALUES", df_1.values.tolist())
print(f"NEW ROWS WERE ADDED SUCCESSFULY")
print(client.execute(f"SELECT count(*) FROM aisurgeclickdb.sales_cockpit_matview_v2"))


# client = Client(host='10.0.0.218',
#                 user='aisurgeclick',
#                 password='M9YfSU7P1R',
#                 port='9000',
#                 database='aisurgeclickdb')
#
# for i in range(1, 46):
#     i_now = i
#     i_then = i-1
#     rows = 1000
#     if i_then == 0:
#         integer = i_now*rows
#         df_new = df[:integer].copy()
#     else:
#         integer_1 = i_now * rows
#         integer_2 = i_then * rows
#         df_new = df[i_then:i_now].copy()
#
#     # INSERT ROWS INTO SALES
#
#     client.execute(f"INSERT INTO aisurgeclickdb.sales VALUES", df_new.values.tolist())
#     print(f"NEW ROWS WERE ADDED SUCCESSFULY FOR {i_now}")
#     sleep(1)


# Check Years
# df_v2 = pd.DataFrame(client.execute(f'select * from aisurgeclickdb.sales_cockpit_matview_v2'))
# df_v2.columns = ['Current Year', 'Current Month', 'Current Date', 'DateTime', 'Customer', 'Country',
#                  'Business Line', 'Total Sales', 'Sales Amount Target', '% of Target', 'Sales per Customer', # 10 by index
#                  'Average Selling Price', 'Total Sold Quantity', 'Total Sales Margin', 'Sales Margin %', # 14
#                  'Total Sales Costs', 'Sales Costs %', 'Active Customers', 'New Customers', 'Distinct Items Sold'] #19
#
# print(f"DISTINCT YEARS : {df_v2['DateTime'].dt.year.unique()}")
















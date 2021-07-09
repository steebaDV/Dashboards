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
client = Client(host='10.0.0.218',
                user='aisurgeclick',
                password='M9YfSU7P1R',
                port='9000',
                database='aisurgeclickdb')


client.execute((f'ALTER TABLE _PointOfSales DELETE WHERE 1=1'))
sleep(5)
print(client.execute(f"SELECT count(*) FROM aisurgeclickdb._PointOfSales"))















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

# CREATE MATVIEW FOR SALES DATASET
client = Client(host='10.0.0.218',
                 user='aisurgeclick',
                 password='M9YfSU7P1R',
                 port='9000',
                 database='aisurgeclickdb')


client.execute('''
CREATE MATERIALIZED VIEW aisurgeclickdb.telco_matview
(
    `Current Year` UInt16,
    `Current Month` String,
    `Current Date` Date,
    `DateTime` DateTime,
    `Conversation Time` Float64,
    `Total Calls` UInt64,
    `Dropped Calls` UInt64,
    `Dropped Calls %` Float64,
    `Avg Setup Time` Float64,
    `Avg Conversation Time` Float64,
    `Total Handovers` UInt64,
    `Avg Handovers` Float64,
    `Drop Calls: Avg Conversation Time` Float64,
    `Nb of Cell Towers` UInt64,
    `Calls per Cell Tower` Float64,
    `Call Direction` String,
    `Phone Type` String,
    `Network` String,
    `Last Cell Tower` String,
    `Dropped Reason` String
)
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(DateTime)
ORDER BY toYYYYMM(DateTime)
SETTINGS index_granularity = 8192 POPULATE
AS
SELECT 
    toYear(Call_Date_Time) AS `Current Year`,
    caseWithExpression(toMonth(Call_Date_Time), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn') AS `Current Month`,
    toDate(Call_Date_Time) AS `Current Date`,
    Call_Date_Time AS DateTime,
    Conversation_Time AS `Conversation Time`,
    count(Call_Date_Time) AS `Total Calls`,
    sum(Dropped_Call) AS `Dropped Calls`,
    sum(Dropped_Call) / count(Call_Date_Time) AS `Dropped Calls %`,
    avg(Setup_Time) AS `Avg Setup Time`,
    avg(Conversation_Time) AS `Avg Conversation Time`,
    sum(Handovers) AS `Total Handovers`,
    avg(Handovers) AS `Avg Handovers`,
    (
        SELECT avg(Conversation_Time)
        FROM aisurgeclickdb.telco
        WHERE Dropped_Call = 1
    ) AS `Drop Calls: Avg Conversation Time`,
    countDistinct(Last_Cell_Tower) AS `Nb of Cell Towers`,
    count(Call_Date_Time) / countDistinct(Last_Cell_Tower) AS `Calls per Cell Tower`,
    Call_Direction as `Call Direction`,
    Phone_Type as `Phone Type`,
    Network as `Network`,
    Last_Cell_Tower as `Last Cell Tower`,
    Dropped_Reason as `Dropped Reason`
FROM aisurgeclickdb.telco
GROUP BY 
    toYear(Call_Date_Time),
    caseWithExpression(toMonth(Call_Date_Time), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn'),
    toDate(Call_Date_Time),
    Call_Date_Time,
    Conversation_Time,
    Call_Direction,
    Phone_Type,
    Network,
    Last_Cell_Tower,
    Dropped_Reason
''')

print('Matview Created!')

print('NUMBER OF ROWS: ')
print(client.execute('select count(*) from telco_matview'))







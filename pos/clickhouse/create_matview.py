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
CREATE MATERIALIZED VIEW aisurgeclickdb.point_of_sales_matview
(
    `Current Year` UInt16,
    `Current Month` String,
    `Current Date` Date,
    `Date` DateTime,
    `Country` String,
    `State` String,
    `Store` String,
    `Brand` String,
    `Product` String,
    `Total Sales` UInt64,
    `Total On-Hand Amount` UInt64,
    `Days Sales of Inventory` Float64,
    `Average Selling Price` Float64,
    `Total On-Hand Units` UInt64,
    `Total Sales Units` UInt64
)
ENGINE = MergeTree()
ORDER BY toYYYYMM(Date)
SETTINGS index_granularity = 8192 POPULATE
AS
WITH
    SUM(Sold_Amount) AS sum_sold_amount,
    SUM(On_Hand_Amount) AS sum_hand_amount,
    SUM(sold_units) AS sum_sold_units,
    SUM(On_Hand_Units) AS sum_on_hand_units
SELECT
    toYear(Date) AS `Current Year`,
    caseWithExpression(toMonth(Date), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn') AS `Current Month`,
    toDate(Date) AS `Current Date`,
    Date,
    Country,
    State,
    Store,
    Brand,
    Product,
    sum_sold_amount AS `Total Sales`,
    sum_hand_amount AS `Total On-Hand Amount`,
    sum_hand_amount / sum_sold_amount AS `Days Sales of Inventory`,
    sum_sold_units AS `Total Sales Units`,
    sum_on_hand_units AS `Total On-Hand Units`,
    sum_sold_amount / sum_sold_units AS `Average Selling Price`
FROM aisurgeclickdb._PointOfSales
GROUP BY
    toYear(Date),
    caseWithExpression(toMonth(Date), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn'),
    toDate(Date),
    Date,
    Country,
    State,
    Store,
    Brand,
    Product
'''
)

print('Matview Created!')

# PREV
# client.execute('''
# CREATE MATERIALIZED VIEW aisurgeclickdb.point_of_sales_matview
# (
#     `Current Year` UInt16,
#     `Current Month` String,
#     `Current Date` Date,
#     `Date` DateTime,
#     `Country` String,
#     `State` String,
#     `Store` String,
#     `Brand` String,
#     `Product` String,
#     `Total Sales` UInt64,
#     `Sales per Store` Float64,
#     `Average Inventory Amount` Float64,
#     `Total On-Hand Amount` UInt64,
#     `Inventory Turns` Float64,
#     `Days Sales of Inventory` Float64,
#     `Nb of Stores` UInt64,
#     `Nb of New Stores` UInt64,
#     `Nb of Products` UInt64,
#     `Nb of New Products` UInt64,
#     `Share of Sold Products %` Float64,
#     `Average Selling Price` Float64,
#     `Average On-hand Price` Float64,
#     `Nb of Sold Products` UInt64,
#     `Total On-Hand Units` UInt64,
#     `Total Sales Units` UInt64,
#     `Nb of Out-of-Stocks` UInt64,
#     `Nb of Inventory Positions` UInt64,
#     `Out-of-Stocks %` Float64
# )
# ENGINE = MergeTree()
# PARTITION BY toYYYYMM(Date)
# ORDER BY toYYYYMM(Date)
# SETTINGS index_granularity = 8192 POPULATE
# AS
# SELECT
#     toYear(Date) AS `Current Year`,
#     caseWithExpression(toMonth(Date), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn') AS `Current Month`,
#     toDate(Date) AS `Current Date`,
#     Date,
#     Country,
#     State,
#     Store,
#     Brand,
#     Product,
#     sum(Sold_Amount) AS `Total Sales`,
#     sum(Sold_Amount) / countDistinct(Store) AS `Sales per Store`,
#     sum(On_Hand_Amount) / countDistinct(Date) AS `Average Inventory Amount`,
#     sum(On_Hand_Amount) AS `Total On-Hand Amount`,
#     (365 * sum(Sold_Amount)) / sum(On_Hand_Amount) AS `Inventory Turns`,
#     sum(On_Hand_Amount) / sum(Sold_Amount) AS `Days Sales of Inventory`,
#     countDistinct(Store) AS `Nb of Stores`,
#     uniq(Store) AS `Nb of New Stores`,
#     countDistinct(Product) AS `Nb of Products`,
#     uniq(Product) AS `Nb of New Products`,
#     (
#         SELECT countDistinct(Product)
#         FROM aisurgeclickdb._PointOfSales
#         WHERE sold_units >= 1
#     ) / countDistinct(Product) AS `Share of Sold Products %`,
#     sum(sold_units) AS `Total Sales Units`,
#     sum(On_Hand_Units) AS `Total On-Hand Units`,
#     sum(Sold_Amount) / sum(sold_units) AS `Average Selling Price`,
#     sum(On_Hand_Amount) / sum(On_Hand_Units) AS `Average On-hand Price`,
#     (
#         SELECT countDistinct(Product)
#         FROM aisurgeclickdb._PointOfSales
#         WHERE sold_units >= 1
#     ) AS `Nb of Sold Products`,
#     (
#         SELECT sum(1)
#         FROM aisurgeclickdb._PointOfSales
#         WHERE On_Hand_Units = 0
#     ) AS `Nb of Out-of-Stocks`,
#     sum(1) AS `Nb of Inventory Positions`,
#     (
#         SELECT sum(1)
#         FROM aisurgeclickdb._PointOfSales
#         WHERE On_Hand_Units = 0
#     ) / sum(1) AS `Out-of-Stocks %`
# FROM aisurgeclickdb._PointOfSales
# GROUP BY
#     toYear(Date),
#     caseWithExpression(toMonth(Date), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn'),
#     toDate(Date),
#     Date,
#     Country,
#     State,
#     Store,
#     Brand,
#     Product
# '''
# )








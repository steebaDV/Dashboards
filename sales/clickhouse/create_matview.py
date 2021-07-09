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
CREATE MATERIALIZED VIEW aisurgeclickdb.sales_cockpit_matview_v2 (`Current Year` UInt16,
                                                                  `Current Month` String,
                                                                  `Current Date` Date,
                                                                  `DateTime` DateTime,
                                                                  `Customer` String,
                                                                  `Country` String,
                                                                  `Business Line` String,
                                                                  `Total Sales` UInt64,
                                                                  `Sales Amount Target` UInt64,
                                                                  `% of Target` Float64,
                                                                  `Sales per Customer` Float64,
                                                                  `Average Selling Price` Float64,
                                                                  `Total Sold Quantity` UInt64,
                                                                  `Total Sales Margin` UInt64,
                                                                  `Sales Margin %` Float64,
                                                                  `Total Sales Costs` Float64,
                                                                  `Sales Costs %` Float64,
                                                                  `Distinct Items Sold #` UInt64
) ENGINE = MergeTree()
ORDER BY (Customer, toYYYYMM(DateTime))
SETTINGS index_granularity = 8192 POPULATE
AS
WITH
    SUM(sales_amount) AS sum_sales_amount,
    SUM(sales_margin) AS sum_sales_margin,
    SUM(sales_amount_target) AS sum_sales_amount_target,
    SUM(sales_quantity) AS sum_sales_quantity,
    COUNTDistinct(customer) AS count_distinct_customer
SELECT
    toYear(date) AS `Current Year`,
    caseWithExpression(toMonth(date), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn') AS `Current Month`,
    toDate(date) AS `Current Date`,
    date AS DateTime,
    customer AS Customer,
    country AS Country,
    business_line AS `Business Line`,
    sum_sales_amount AS `Total Sales`,
    sum_sales_amount_target AS `Sales Amount Target`,
    (sum_sales_amount / sum_sales_amount_target) * 100 AS `% of Target`,
    sum_sales_amount / count_distinct_customer AS `Sales per Customer`,
    sum_sales_amount / sum_sales_quantity AS `Average Selling Price`,
    sum_sales_quantity AS `Total Sold Quantity`,
    sum_sales_margin AS `Total Sales Margin`,
    (sum_sales_margin / sum_sales_amount) * 100 AS `Sales Margin %`,
    sum_sales_amount - sum_sales_margin AS `Total Sales Costs`,
    ((sum_sales_amount - sum_sales_margin) / sum_sales_amount) * 100 AS `Sales Costs %`,
    COUNTDistinct(product) AS `Distinct Items Sold #`
FROM aisurgeclickdb.sales
GROUP BY
    toYear(date),
    caseWithExpression(toMonth(date), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn'),
    toDate(date),
    date,
    customer,
    country,
    business_line
''')

print('Matview Created!')



# PREV
# client.execute('''
# CREATE MATERIALIZED VIEW sales_cockpit_matview_v2 (`Current Year` UInt16,
#                                                    `Current Month` String,
#                                                    `Current Date` Date,
#                                                    `DateTime` DateTime,
#                                                    `Customer` String,
#                                                    `Country` String,
#                                                    `Business Line` String,
#                                                    `Total Sales` UInt64,
#                                                    `Sales Amount Target` UInt64,
#                                                    `% of Target` Float64,
#                                                    `Sales per Customer` Float64,
#                                                    `Average Selling Price` Float64,
#                                                    `Total Sold Quantity` UInt64,
#                                                    `Total Sales Margin` UInt64,
#                                                    `Sales Margin %` Float64,
#                                                    `Total Sales Costs` Float64,
#                                                    `Sales Costs %` Float64,
#                                                    `Distinct Items Sold #` UInt64
#                                                    ) ENGINE = MergeTree()
# ORDER BY
#     (Customer, toYYYYMM(DateTime)) SETTINGS index_granularity = 8192 POPULATE
# AS
#    WITH SUM(sales_amount) as sum_sales_amount,
#          SUM(sales_margin) as sum_sales_margin,
#          SUM(sales_amount_target) as sum_sales_amount_target,
#          SUM(sales_quantity) as sum_sales_quantity,
#          COUNT(DISTINCT customer) as count_distinct_customer
#    SELECT
#       toYear(date) AS `Current Year`,
#       caseWithExpression(toMonth(date), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn') AS `Current Month`,
#       toDate(date) AS `Current Date`,
#       date AS `DateTime`,
#       customer AS `Customer`,
#       country AS `Country`,
#       business_line AS `Business Line`,
#       sum_sales_amount AS `Total Sales`,
#       sum_sales_amount_target AS `Sales Amount Target`,
#       (
#          sum_sales_amount / sum_sales_amount_target
#       )
#       * 100 AS `% of Target`,
#       sum_sales_amount / count_distinct_customer AS `Sales per Customer`,
#       sum_sales_amount / sum_sales_quantity AS `Average Selling Price`,
#       sum_sales_quantity AS `Total Sold Quantity`,
#       sum_sales_margin AS `Total Sales Margin`,
#       (
#          sum_sales_margin / sum_sales_amount
#       )
#       * 100 AS `Sales Margin %`,
#       sum_sales_amount - sum_sales_margin AS `Total Sales Costs`,
#       (
#           (sum_sales_amount - sum_sales_margin) / sum_sales_amount
#       )
#       * 100 AS `Sales Costs %`
#    FROM
#       sales
#    GROUP BY
#       toYear(date),
#       caseWithExpression(toMonth(date), 1, 'Jan', 2, 'Feb', 3, 'Mar', 4, 'Apr', 5, 'May', 6, 'Jun', 7, 'Jul', 8, 'Aug', 9, 'Sep', 10, 'Oct', 11, 'Nov', 12, 'Dec', 'Unkn'),
#       toDate(date),
#       date,
#       customer,
#       country,
#       business_line
# ''')






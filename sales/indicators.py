import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, get_currency_sign, value_format

currency_sign = get_currency_sign()


def get_current_and_prev_data(current_year, current_month, df, chart_type, country, customer):
    # FILTER BY DATE
    # current_year = 2011
    # current_int = 7
    # current_month = calendar.month_abbr[current_int]
    # country = None
    # customer = None

    prev_year = current_year - 1
    # print(f'current_year: {current_year}, current_month: {current_month}, country: {country}, customer: {customer}')
    df_current = df[(df['Current Year'] == current_year) & (df['Current Month'] == current_month)]
    df_prev = df[(df['Current Year'] == prev_year) & (df['Current Month'] == current_month)]
    # FILTER BY COUNTRY
    if country is not None:
        df_current = df_current[(df_current['Country'] == country)]
        df_prev = df_prev[(df_prev['Country'] == country)]

    if customer is not None:
        df_current = df_current[(df_current['Customer'] == customer)]
        df_prev = df_prev[(df_prev['Customer'] == customer)]

    # print(df_current)
    # prev_year = current_year - 1
    # df_current = df[(df['Current Year'] == current_year) & (df['Current Month'] == current_month)]
    # # df_current = df[(df['Current Year'] == current_year)]
    # df_prev = df[(df['Current Year'] == prev_year) & (df['Current Month'] == current_month)]

    total_sales_current = df_current['Total Sales'].sum()
    total_sales_prev = df_prev['Total Sales'].sum()

    if chart_type == 'Total Sales':
        df_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Total Sales': ['sum']}).reset_index()
        df_groupby.columns = ['DateTime', 'Total Sales']

        diff_percent = round((total_sales_current - total_sales_prev) / total_sales_prev * 100, 1)
        return df_groupby, total_sales_current, total_sales_prev, diff_percent

    elif chart_type == 'Sales per Customer':
        df_current_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Customer': ['count'], 'Total Sales': ['sum']}).reset_index()
        # print(df_current_groupby)
        df_current_groupby.columns = ['DateTime', 'Customer', 'Total Sales']
        # df_current_grouped_by_customers = df_current.groupby(['Current Month', 'Customer', 'Country']).agg(
        #     {'Total Sales': 'sum'}).reset_index()
        # df_current_groupby = df_current.groupby('Current Month').agg({'Total Sales': 'sum'}).reset_index()
        # df_prev_grouped_by_customers = df_prev.groupby(['Current Month', 'Customer', 'Country']).agg(
        #     {'Total Sales': 'sum'}).reset_index()
        df_prev_grouped_by_customers = df_prev.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Customer': ['count'], 'Total Sales': ['sum']}).reset_index()
        unique_customers_current = df_current.value_counts(['Customer', 'Country']).shape[0]
        # unique_customers_current_2 = df_current.groupby(['Customer', 'Country']).ngroups
        # print(f'unique_customers_current: {unique_customers_current}, unique_customers_current_2: {unique_customers_current_2}')
        unique_customers_prev = df_prev.value_counts(['Customer', 'Country']).shape[0]
        sales_per_customer_current = total_sales_current / unique_customers_current
        sales_per_customer_prev = total_sales_prev / unique_customers_prev
        diff_percent = round((sales_per_customer_current - sales_per_customer_prev) / sales_per_customer_prev * 100, 1)
        return df_current_groupby, sales_per_customer_current, sales_per_customer_prev, diff_percent

    elif chart_type == 'Total Sold Quantity':
        total_sales_quantity_current = df_current['Total Sold Quantity'].sum()
        total_sales_quantity_prev = df_prev['Total Sold Quantity'].sum()
        df_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Total Sold Quantity': ['sum']}).reset_index()
        df_groupby.columns = ['DateTime', 'Total Sold Quantity']
        # df_groupby = df_current.groupby('Current Month').agg({'Total Sold Quantity': 'sum'}).reset_index()
        diff_percent = round(
            (total_sales_quantity_current - total_sales_quantity_prev) / total_sales_quantity_prev * 100, 1)
        return df_groupby, total_sales_quantity_current, total_sales_quantity_prev, diff_percent

    elif chart_type == 'Average Selling Price':
        df_groupby_date_current = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Total Sales': ['sum'], 'Total Sold Quantity': ['sum']}).reset_index()
        df_groupby_date_current.columns = ['DateTime', 'Total Sales', 'Total Sold Quantity']
        df_groupby_date_prev = df_prev.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Total Sales': ['sum'], 'Total Sold Quantity': ['sum']}).reset_index()
        df_groupby_date_prev.columns = df_groupby_date_current.columns
        # df_groupby_date_current = df_current.groupby('Current Month').agg(
        #     {'Total Sales': 'sum', 'Total Sold Quantity': 'sum'}).reset_index()
        # df_groupby_date_prev = df_prev.groupby('Current Month').agg(
        #     {'Total Sales': 'sum', 'Total Sold Quantity': 'sum'}).reset_index()
        df_groupby_date_current['Average Selling Price'] = df_groupby_date_current['Total Sales'] / \
                                                           df_groupby_date_current['Total Sold Quantity']
        df_groupby_date_current = df_groupby_date_current.fillna(0)
        # print('df_groupby_date_current')
        # print(df_groupby_date_current)

        average_selling_price_current = round(
            df_groupby_date_current['Total Sales'].sum() / df_groupby_date_current['Total Sold Quantity'].sum(), 1)
        average_selling_price_prev = round(
            df_groupby_date_prev['Total Sales'].sum() / df_groupby_date_prev['Total Sold Quantity'].sum(), 1)
        diff_percent = round(
            (average_selling_price_current - average_selling_price_prev) / average_selling_price_prev * 100, 1)
        return df_groupby_date_current, average_selling_price_current, average_selling_price_prev, diff_percent

    elif chart_type == 'Active Customers':
        df_groupby_date_current = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Customer': ['count']}).reset_index()
        df_groupby_date_current.columns = ['DateTime', 'Customer']
        df_groupby_date_prev = df_prev.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Customer': ['count']}).reset_index()
        df_groupby_date_prev.columns = df_groupby_date_current.columns

        # df_groupby_date_current = df_current.groupby(['Current Month']).agg({'Customer': 'count'}).reset_index()
        # df_groupby_date_prev = df_prev.groupby('Current Month').agg({'Customer': 'count'}).reset_index()
        active_customers_current = df_current.groupby(['Current Month', 'Customer', 'Country']).ngroups
        active_customers_prev = df_prev.groupby(['Current Month', 'Customer', 'Country']).ngroups

        diff_percent = round((active_customers_current - active_customers_prev) / active_customers_prev * 100,
                             1) if active_customers_prev != 0 else np.nan
        return df_groupby_date_current, active_customers_current, active_customers_prev, diff_percent

    elif chart_type == 'Total Sales Margin':
        df_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Total Sales Margin': ['sum']}).reset_index()
        df_groupby.columns = ['DateTime', 'Total Sales Margin']
        # df_groupby = df_current.groupby('Current Month').agg({'Total Sales Margin': 'sum'}).reset_index()
        total_sales_margin_current = df_current['Total Sales Margin'].sum()
        total_sales_margin_prev = df_prev['Total Sales Margin'].sum()
        df_groupedby_date_current = df_current.groupby('Current Date').agg({'Total Sales Margin': 'sum'}).reset_index()
        diff_percent = round((total_sales_margin_current - total_sales_margin_prev) / total_sales_margin_prev * 100, 1)
        return df_groupby, total_sales_margin_current, total_sales_margin_prev, diff_percent
    #
    elif chart_type == 'Sales Margin %':
        sales_margin_percent_current = df_current['Total Sales Margin'].sum() / df_current['Total Sales'].sum() * 100
        sales_margin_percent_prev = df_prev['Total Sales Margin'].sum() / df_prev['Total Sales'].sum() * 100
        df_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'Total Sales Margin': ['sum'], 'Total Sales': ['sum']}).reset_index()
        # df_groupby = df_current.groupby('Current Month').agg(
        #     {'Total Sales Margin': 'sum', 'Total Sales': 'sum'}).reset_index()
        df_groupby.columns = ['DateTime', 'Total Sales Margin', 'Total Sales']
        df_groupby['Sales Margin %'] = df_groupby['Total Sales Margin'] / df_groupby['Total Sales'] * 100
        diff_percent = round(
            (sales_margin_percent_current - sales_margin_percent_prev) / sales_margin_percent_prev * 100, 1)
        return df_groupby, sales_margin_percent_current, sales_margin_percent_prev, diff_percent
    #
    elif chart_type == 'New Customers':
        new_customers_col = []

        count_of_new_customers_prev = 0
        count_of_new_customers_current = 0
        for date, customer in zip(df_current['Current Date'], df_current['Customer']):
            if customer not in list(df[df['Current Date'] < date]['Customer']):
                new_customers_col.append(1)
                count_of_new_customers_current += 1
            else:
                new_customers_col.append(0)
        for date, customer in zip(df_prev['Current Date'], df_prev['Customer']):
            if customer not in list(df[df['Current Date'] < date]['Customer']):
                count_of_new_customers_prev += 1

        df_current['New Customers'] = new_customers_col

        count_of_new_customers_current = df_current['New Customers'].sum()
        df_groupby_date = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {'New Customers': ['sum']}).reset_index()
        df_groupby_date.columns = ['DateTime', 'New Customers']
        # df_groupby_date = df_current.groupby('Current Month').agg({'New Customers': 'sum'}).reset_index()
        diff_percent = round(
            (count_of_new_customers_current - count_of_new_customers_prev) / count_of_new_customers_current * 100, 1)

        return df_groupby_date, count_of_new_customers_current, count_of_new_customers_prev, diff_percent


def create_figure(df_x, df_y, value, reference, chart_type):
    if chart_type in ['New Customers', 'Active Customers']:
        valueformat_2 = ""
    else:
        valueformat_2 = ".2s"
    if chart_type in ['Total Sales', 'Sales per Customer', 'Total Sales Margin', 'Average Selling Price']:
        prefix = currency_sign
    else:
        prefix = ''
    if chart_type == 'Average Selling Price':
        suffix = ' d'
    elif chart_type == 'Sales Margin %':
        suffix = '%'
    else:
        suffix = ''
    if chart_type in ['New Customers', 'Sales Margin %']:
        fig = go.Figure(go.Bar(x=df_x,
                               y=df_y,
                               marker_color='#E8E8E8'))
    else:
        fig = go.Figure(go.Scatter(x=df_x,
                                   y=df_y,
                                   mode='lines',
                                   fill='tozeroy',
                                   # hovertemplate='<extra></extra>',
                                   line_color='#E8E8E8'))
    fig.add_trace(go.Indicator(mode="number+delta",
                               value=int(value_format(value)[0]),
                               title={"text": chart_type,
                                      'font': {'size': 17,
                                               },
                                      },
                               number={'prefix': prefix,
                                       'suffix': f'{value_format(value)[1:]}{suffix}',
                                       'font': {'size': 17,
                                                },
                                       },
                               delta={'position': 'left',
                                      'reference': reference,
                                      'valueformat': valueformat_2,
                                      'font': {'size': 13,
                                               },
                                      },
                               domain={'y': [0, 0.7], 'x': [0.25, 0.75]}))
    # SET FONT
    fig.update_layout(autosize=True,
                      font={
                          'family': font_family,
                          # 'color': 'black',
                          # 'size': 12
                      },
                      )
    return fig


from funcs import augment_days


def get_indicator_plot(current_year, current_month, df, chart_type, country=None, customer=None):
    prev_year = current_year - 1
    df_1, dim_1, dim_2, diff = get_current_and_prev_data(current_year, current_month, df, chart_type, country, customer)
    month_int = list(calendar.month_abbr).index(current_month)  # month abr to int
    # print(f'current_month indicator: {month_int}')
    df_1 = augment_days(month_int, current_year, df_1)
    # print('df_1')
    # print(df_1)
    df_x = df_1['DateTime']
    # print('df_x')
    # print(df_x)
    # df_x = df_1['Current Month']
    if chart_type in ['Total Sales']:
        df_y = df_1['Total Sales']
    elif chart_type in ['Sales per Customer']:
        df_y = df_1['Total Sales']
    elif chart_type in ['Active Customers']:
        df_y = df_1['Customer']
    elif chart_type in ['Sales Margin %']:
        df_y = df_1['Sales Margin %']
    elif chart_type in ['New Customers']:
        df_y = df_1['New Customers']
    elif chart_type in ['Average Selling Price']:
        df_y = df_1['Average Selling Price']
    elif chart_type in ['Total Sold Quantity']:
        # df_1.columns = ['DateTime', 'Total Sold Quantity']
        # print(df_1['Total Sold Quantity'].sum())
        df_y = df_1['Total Sold Quantity']
    elif chart_type in ['Total Sales Margin']:
        df_y = df_1['Total Sales Margin']

    # print(f'df_y: {df_y}')
    fig = create_figure(df_x, df_y, dim_1, dim_2, chart_type)
    fig.update_layout(xaxis={'showgrid': False,
                             'showticklabels': False},
                      yaxis={'showgrid': False,
                             'showticklabels': False},
                      plot_bgcolor='#FFFFFF',
                      # width=800,
                      # height=500,
                      xaxis_title=f"<b>{'+' if diff > 0 else ''}{value_format(diff)}%</b> vs {current_month}-{prev_year}",  # YTD
                      xaxis_title_font={'color': 'grey',
                                        'size': 12,
                                        },
                      margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                                  r=0,
                                  b=0,
                                  t=15,
                                  #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                                  ),
                      autosize=True,
                      )

    # fig.show()
    return fig

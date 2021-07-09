import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, augment_days, value_format, get_currency_sign

currency_sign = get_currency_sign()


def get_current_and_prev_data(current_year, current_month, df, chart_type, state=None, store=None):
    # chart_type = 'Avg Selling Price'
    # current_year = 2020
    # month_int = 12
    # country = None
    # state = None
    previous_year = current_year - 1
    # current_month = calendar.month_abbr[month_int] # 'Dec', 'Nov'
    month_int = list(calendar.month_abbr).index(current_month)  # 1, 2, 3
    prev_month = calendar.month_abbr[month_int - 1]
    # print(prev_month)

    from calendar import monthrange
    _, max_days_current = monthrange(current_year, month_int)
    _, max_days_prev = monthrange(current_year, month_int - 1)

    # Current Month VS Previous Month
    df_current = df[(df['Current Year'] == current_year) & (df['Current Month'] == current_month)]
    df_prev = df[(df['Current Year'] == current_year) & (df['Current Month'] == prev_month)]
    # FILTER BY COUNTRY
    if store is not None:
        df_current = df_current[(df_current['Store'] == store)]
        df_prev = df_prev[(df_prev['Store'] == store)]

    if state is not None:
        df_current = df_current[(df_current['City'] == state)]
        df_prev = df_prev[(df_prev['City'] == state)]

    total_sales_current = df_current['Total Sales'].sum()
    total_sales_prev = df_prev['Total Sales'].sum()

    # Agg by Month
    # start with Oct and up to the current month, including
    start_month = 10
    start_date, end_date = f'{previous_year}-{start_month}-01', f'{current_year}-{month_int}-{max_days_current}'
    print(start_date, end_date)  # 2019-10-01 2020-12-31
    df_range = df[df['Date'].between(start_date, end_date, inclusive=True)].copy()  # Oct Prev to Current Month

    # SALES
    if chart_type == 'Total Sales':
        df_groupby = df_current.groupby(pd.Grouper(key='Date', freq='1D')).agg({'Total Sales': ['sum']}).reset_index()
        df_groupby.columns = ['Date', 'Total Sales']
        diff_percent = round((total_sales_current - total_sales_prev) / total_sales_prev * 100, 1)
        return df_groupby, total_sales_current, total_sales_prev, diff_percent

    elif chart_type == 'Sales per Store':
        df_current_groupby = df_current.groupby(pd.Grouper(key='Date', freq='1D')).agg(
            {'Store': ['count'], 'Total Sales': ['sum']}).reset_index()
        df_current_groupby.columns = ['Date', 'Store', 'Total Sales']
        df_current_groupby['Sales per Store'] = df_current_groupby['Total Sales'] / df_current_groupby['Store']
        df_current_groupby = df_current_groupby.fillna(0.0)

        unique_stores_current = df_current.value_counts(['Store', 'Country']).shape[0]
        unique_stores_prev = df_prev.value_counts(['Store', 'Country']).shape[0]

        sales_per_store_current = total_sales_current / unique_stores_current
        sales_per_store_prev = total_sales_prev / unique_stores_prev
        diff_percent = round((sales_per_store_current - sales_per_store_prev) / sales_per_store_prev * 100, 1)
        return df_current_groupby, sales_per_store_current, sales_per_store_prev, diff_percent

    # INVENTORY
    elif chart_type == 'Average Inventory Amount':
        '''Average Inventory Amount = Total On-Hand Amount /Number of Dates'''
        df_current_groupby = df_current.groupby(pd.Grouper(key='Date', freq='1D')).agg(
            {'Total On-Hand Amount': ['sum']}).reset_index()
        df_current_groupby.columns = ['Date', 'Total On-Hand Amount']
        df_current_groupby['Average Inventory Amount'] = df_current_groupby['Total On-Hand Amount'] / 1  # 1 for 1 D

        df_prev_groupby = df_prev.groupby(pd.Grouper(key='Date', freq='1D')).agg(
            {'Total On-Hand Amount': ['sum']}).reset_index()
        df_prev_groupby.columns = ['Date', 'Total On-Hand Amount']
        df_prev_groupby['Average Inventory Amount'] = df_prev_groupby['Total On-Hand Amount'] / 1  # 1 for 1 D

        avg_inv_current = df_current_groupby['Average Inventory Amount'].sum() / max_days_current
        avg_inv_prev = df_prev_groupby['Average Inventory Amount'].sum() / max_days_prev

        diff_percent = round((avg_inv_current - avg_inv_prev) / avg_inv_prev * 100, 1)
        return df_current_groupby, avg_inv_current, avg_inv_prev, diff_percent

        # PREV
        # '''Total On-Hand Amount /Number of Dates'''
        # df_current_groupby = df_current.groupby(pd.Grouper(key='Date', freq='1D')).agg(
        #     {'Average Inventory Amount': ['sum']}).reset_index()
        # df_current_groupby.columns = ['Date', 'Average Inventory Amount']
        # df_prev_groupby = df_prev.groupby(pd.Grouper(key='Date', freq='1D')).agg(
        #     {'Average Inventory Amount': ['sum']}).reset_index()
        # df_prev_groupby.columns = df_current_groupby.columns
        #
        # avg_inv_current = df_current_groupby['Average Inventory Amount'].sum() / max_days_current
        # avg_inv_prev = df_prev_groupby['Average Inventory Amount'].sum() / max_days_prev
        #
        # diff_percent = round((avg_inv_current - avg_inv_prev) / avg_inv_prev * 100, 1)
        # return df_current_groupby, avg_inv_current, avg_inv_prev, diff_percent

    elif chart_type == 'Total On-Hand Amount':
        '''SUM Total On-Hand Amount by days'''
        df_current_groupby = df_current.groupby(pd.Grouper(key='Date', freq='1D')).agg(
            {'Total On-Hand Amount': ['sum']}).reset_index()
        df_current_groupby.columns = ['Date', 'Total On-Hand Amount']
        df_prev_groupby = df_prev.groupby(pd.Grouper(key='Date', freq='1D')).agg(
            {'Total On-Hand Amount': ['sum']}).reset_index()
        df_prev_groupby.columns = df_current_groupby.columns

        on_hand_current = df_current_groupby['Total On-Hand Amount'].sum()
        on_hand_prev = df_prev_groupby['Total On-Hand Amount'].sum()

        diff_percent = round((on_hand_current - on_hand_prev) / on_hand_prev * 100, 1)
        return df_current_groupby, on_hand_current, on_hand_prev, diff_percent

    elif chart_type == 'Inventory Turns':
        # CALCULCATE Inventory Turns
        '''(Dates in Year * Total Sales) / Total On-Hand Amount over the period'''  # 1M, 12M+
        df_current_groupby = df_range.groupby(pd.Grouper(key='Date', freq='M')).agg(
            {'Total Sales': ['sum'], 'Total On-Hand Amount': ['sum']}).reset_index()
        df_current_groupby.columns = ['Date', 'Total Sales x365', 'Total On-Hand Amount']
        df_current_groupby['Total Sales x365'] = df_current_groupby['Total Sales x365'] * 365
        df_current_groupby['Inventory Turns'] = (
                    df_current_groupby['Total Sales x365'] / df_current_groupby['Total On-Hand Amount']).round(1)

        inv_turns_current = df_current_groupby[
            (df_current_groupby['Date'].dt.year == current_year) & (df_current_groupby['Date'].dt.month == month_int)]
        inv_turns_current = float(inv_turns_current['Inventory Turns'].values[0])
        inv_turns_prev = df_current_groupby[(df_current_groupby['Date'].dt.year == current_year) & (
                    df_current_groupby['Date'].dt.month == month_int - 1)]  # prev month data
        inv_turns_prev = float(inv_turns_prev['Inventory Turns'].values[0])
        diff_percent = round((inv_turns_current - inv_turns_prev) / inv_turns_prev * 100, 1)
        return df_current_groupby, inv_turns_current, inv_turns_prev, diff_percent

    elif chart_type == 'Days Sales of Inventory':
        # CALCULCATE Days Sales of Inventory
        '''Total On-Hand Amount over the period / Total Sales'''  # 1M, 12M+
        df_current_groupby = df_range.groupby(pd.Grouper(key='Date', freq='M')).agg(
            {'Total Sales': ['sum'], 'Total On-Hand Amount': ['sum']}).reset_index()
        df_current_groupby.columns = ['Date', 'Total Sales', 'Total On-Hand Amount']
        df_current_groupby['Days Sales of Inventory'] = (
                    df_current_groupby['Total On-Hand Amount'] / df_current_groupby['Total Sales']).round(1)

        days_sales_current = float(df_current_groupby.iloc[-1].at['Days Sales of Inventory'])  # index, key
        days_sales_prev = float(df_current_groupby.iloc[-2].at['Days Sales of Inventory'])  # index, key
        diff_percent = round((days_sales_current - days_sales_prev) / days_sales_prev * 100, 1)
        return df_current_groupby, days_sales_current, days_sales_prev, diff_percent

    # STORES
    elif chart_type == 'Nb of Stores':
        # CALCULCATE Nb of Stores
        '''Nb of Stores'''  # 1M, 12M+
        df_range['store_state'] = df_range[['Store', 'City']].agg(' '.join, axis=1)
        df_current_groupby = df_range.groupby(pd.Grouper(key='Date', freq='M'))['store_state'].nunique()
        # convert series to DF
        df_current_groupby = df_current_groupby.to_frame().reset_index()
        df_current_groupby.columns = ['Date', 'Nb of Stores']

        nb_stores_current = int(df_current_groupby.iloc[-1].at['Nb of Stores'])  # index, key
        nb_stores_prev = int(df_current_groupby.iloc[-2].at['Nb of Stores'])  # index, key
        diff_percent = round((nb_stores_current - nb_stores_prev) / nb_stores_prev * 100, 1)
        return df_current_groupby, nb_stores_current, nb_stores_prev, diff_percent


    elif chart_type == 'Nb of New Stores':
        # CALCULCATE Nb of New Stores
        # new store and first active date
        df_min_date = df_range.groupby(['Store', 'City']).Date.min().reset_index()
        new_stores_groupby = df_min_date.groupby(pd.Grouper(key='Date', freq='M'))['Store'].nunique().reset_index()

        new_stores_current = new_stores_groupby.iloc[-1].values  # DateTime, n of new stores
        new_stores_current = int(new_stores_current[1]) if new_stores_current[0].month == month_int else 0
        # new_stores_groupby include the current month else last row
        new_stores_prev = int(new_stores_groupby.iloc[-2].at['Store']) if new_stores_groupby.iloc[-2].at['Date'].month == month_int - 1 else int(new_stores_groupby.iloc[-1].at['Store'])

        diff_percent = round((new_stores_current - new_stores_prev) / new_stores_prev * 100, 1)
        return new_stores_groupby, new_stores_current, new_stores_prev, diff_percent

    # PRODUCTS
    elif chart_type == 'Nb of Products':
        # CALCULCATE Nb of Products
        '''Nb of Products'''  # 1M, 12M+
        df_range['product_brand'] = df_range[['Product', 'Brand']].agg(' '.join, axis=1)
        df_current_groupby = df_range.groupby(pd.Grouper(key='Date', freq='M'))[
            'product_brand'].nunique()
        # convert series to DF
        df_current_groupby = df_current_groupby.to_frame().reset_index()
        df_current_groupby.columns = ['Date', 'Nb of Products']

        nb_products_current = int(df_current_groupby.iloc[-1].at['Nb of Products'])  # index, key
        nb_products_prev = int(df_current_groupby.iloc[-2].at['Nb of Products'])  # index, key
        diff_percent = round((nb_products_current - nb_products_prev) / nb_products_prev * 100, 1)
        return df_current_groupby, nb_products_current, nb_products_prev, diff_percent

    elif chart_type == 'Average Selling Price':
        # CALCULCATE Nb of Products
        '''Total Sales / Total Sales Units = Average Selling Price'''  # 1M, 12M+
        df_current_groupby = df_range.groupby(pd.Grouper(key='Date', freq='M')).agg(
            {'Average Selling Price': ['sum']}).reset_index()
        df_current_groupby.columns = ['Date', 'Average Selling Price']

        avg_price_current = int(df_current_groupby.iloc[-1].at['Average Selling Price'])  # index, key
        avg_price_prev = int(df_current_groupby.iloc[-2].at['Average Selling Price'])  # index, key
        diff_percent = round((avg_price_current - avg_price_prev) / avg_price_prev * 100, 1)
        return df_current_groupby, avg_price_current, avg_price_prev, diff_percent


def create_figure(df_x, df_y, value, reference, chart_type):
    if chart_type in ['Inventory Turns', 'Days Sales of Inventory', 'Nb of Stores', 'Nb of New Stores', 'Nb of Products']:
        prefix = ""
    else:
        prefix = currency_sign
    if chart_type == 'Days Sales of Inventory':
        suffix = ' d'
    else:
        suffix = ''
    if chart_type in ['Nb of Stores', 'Nb of New Stores', 'Nb of Products', 'Days Sales of Inventory']: # integer
        valueformat_2 = ""
    else:
        valueformat_2 = ".2s"

    # Bars
    if chart_type in ['Inventory Turns', 'Nb of New Stores']:
        fig = go.Figure(go.Bar(x=df_x,
                               y=df_y,
                               marker_color='#E8E8E8',
                               ))
        fig.update_layout(bargap=0.3)

    # Lines
    else:
        fig = go.Figure(go.Scatter(x=df_x,
                                   y=df_y,
                                   mode='lines',
                                   fill=None if chart_type in ['Days Sales of Inventory', 'Nb of Stores', 'Nb of Products'] else 'tozeroy',
                                   hovertemplate='<extra></extra>',
                                   line_color='#E8E8E8'))
    value = value_format(value)
    fig.add_trace(go.Indicator(mode="number+delta",
                               value=int(value[0]),
                               title={"text": chart_type,
                                      'font': {'size': 17,
                                               },
                               },
                               number={'prefix': prefix,
                                       'suffix': f'{value[1:]}{suffix}',
                                       'font': {'size': 17,
                                                },
                               },
                               delta={'position': 'left',
                                      'reference': reference,
                                      # 'valueformat': valueformat_2,
                                      'font': {'size': 13,
                                               },
                               },
                               domain={'y': [0, 0.7], 'x': [0.25, 0.75]}))
    # SET FONT
    fig.update_layout(autosize=True,
                      font={
                            'family': font_family,
                            # 'color': 'black',
                            'size': 12
                      },
    )
    return fig


def get_indicator_plot(current_year, current_month, df, chart_type,
                      state=None,
                      store=None,
                      brand=None,
                      product=None,
                      country=None):

    if store:
        df = df[df['Store'] == store]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]
    if state:
        df = df[df['City'] == state]
        
    prev_year = current_year - 1
    month_int = list(calendar.month_abbr).index(current_month)  # 1, 2, 3
    prev_month = calendar.month_abbr[month_int - 1] # 'Nov', 'Oct'

    df_1, dim_1, dim_2, diff = get_current_and_prev_data(current_year, current_month, df, chart_type, state, country)
    month_int = list(calendar.month_abbr).index(current_month)  # month abr to int
    if chart_type in ['Total Sales', 'Sales per Store', 'Average Inventory Amount', 'Total On-Hand Amount']:
        df_1 = augment_days(month_int, current_year, df_1)

    df_x = df_1['Date']
    df_y = df_1['Store'] if chart_type == 'Nb of New Stores' else df_1[chart_type]  # one exception

    fig = create_figure(df_x, df_y, dim_1, dim_2, chart_type)
    fig.update_layout(xaxis={'showgrid': False,
                             'showticklabels': False},
                      yaxis={'showgrid': False,
                             'showticklabels': False},
                      plot_bgcolor='#FFFFFF',
                      # width=800,
                      # height=500,
                      xaxis_title=f"<b>{'+' if diff > 0 else ''}{value_format(diff)}%</b> vs {prev_month}-{str(current_year)[-2:]}",
                      # YTD
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

    return fig







from clickhouse_driver import Client
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import calendar
import json
import sys

# ALL USEFUL FUNCTIONS AND MODULES FOR DATA PROCESSING ARE STORED HERE
import seaborn as sns

diverging_palette = sns.color_palette("RdBu", 7).as_hex()

red_palette = sns.color_palette("OrRd", 7).as_hex()

orange_palette = ['#ecda9a',
                  '#efc47e',
                  '#f3ad6a',
                  '#f7945d',
                  '#f97b57',
                  '#f66356',
                  '#ee4d5a',
                  ]

blue_palette = ['#d2fbd4',
                '#a5dbc2',
                '#7bbcb0',
                '#559c9e',
                '#3a7c89',
                '#235d72',
                '#123f5a',
                ]

grey_palette = {1: '#f9f9f9',
                2: '#ececec',
                3: '#dfdfdf',
                4: '#d3d3d3',
                5: '#c6c6c6',
                6: '#b9b9b9',
                7: '#acacac',
                }

bubbles_palette_1 = {1: '#009392',  # Temps
                     2: '#39b185',
                     3: '#9ccb86',
                     4: '#e9e29c',
                     5: '#eeb479',
                     6: '#e88471',
                     7: '#cf597e',
                     }

bubbles_palette_2 = {1: '#008080',  # Greyser
                     2: '#70a494',
                     3: '#b4c8a8',
                     4: '#f6edbd',
                     5: '#edbb8a',
                     6: '#de8a5a',
                     7: '#ca562c',
                     }

customers_palette = {1: '#173042',
                     2: '#cfdfda',
                     3: '#236477',
                     4: '#7cad3e',
                     }

font_family = 'Lato-Regular'  # 'Lato-Thin'


# font_family = 'Lato-Thin'



# Options:
# 'Current Month vs Previous Month'
# 'Current Month vs Same Month, Previous Year'
# 'Year-to-Date: Current Year vs Previous Year'

def prev(current_year, current_month, performance_scope=None):
    """
    Gets previous month & date based on current year and month and performance scope.

    Parameters
    ----------
    current_year : int
        Current year filter
    current_month : int
        Current month filter
    performance_scope : str, optional
        Performance scope filter (default None).

    Returns
    -------
    prev_year
        Previous year parameter
    prev_month
        Previous month parameter
    """
    if performance_scope == 'Current Month vs Previous Month' or not performance_scope:
        prev_month = current_month - 1 if current_month != 1 else 12
        prev_year = current_year if current_month != 1 else current_year - 1  # change current_year only if month is January
    elif performance_scope in ('Current Month vs Same Month, Previous Year', 'Year-to-Date: Current Year vs Previous Year'):
        prev_month = current_month
        prev_year = current_year - 1
    return prev_year, prev_month


def filter_performance_scope(df,
                             current_year,
                             current_month,
                             performance_scope,
                             datefield='Accident Occurrence Date'):
    """
    Filters data based on the Performance scope filter.

    Parameters
    ----------
    df : dataframe
        Data
    current_year : int
        Current year filter
    current_month : int
        Current month filter
    performance_scope : str
        Performance scope filter
    datefield : datetime, optional
        Date field in the data (default 'Accident Occurrence Date')

    Returns
    -------
    df_current
        Data filtered based on performance scope, current year and month
    df_prev
        Data filtered based on performance scope, previous year and month
    """
    ref_year, ref_month = prev(current_year, current_month, performance_scope)

    if performance_scope in ('Current Month vs Previous Month', 'Current Month vs Same Month, Previous Year'):
        df_current = df[(df[datefield].dt.year == current_year) & (df[datefield].dt.month == current_month)]
        df_prev = df[(df[datefield].dt.year == ref_year) & (df[datefield].dt.month == ref_month)]

    elif performance_scope == 'Year-to-Date: Current Year vs Previous Year':
        df_current = df[(df[datefield].dt.year == current_year) & (df[datefield].dt.month <= current_month)]
        df_prev = df[(df[datefield].dt.year == ref_year) & (df[datefield].dt.month <= ref_month)]

    return df_current, df_prev

# OPTIONS

# previous year / quarter / month / week / day (yesterday)
# this     year / quarter / month / week / day (today)
# next     year / quarter / month / week / day (tomorrow)
# last N   years / quarters / months / weeks / days
# next N   years / quarters / months / weeks / days
# year / quarter / month / week / day to date

# date_filter = 'previous year'
# date_filter = 'previous quarter'
# date_filter = 'previous month'
# date_filter = 'previous week'
# date_filter = 'yesterday'  # date_filter = 'previous day'

# date_filter = 'this year'
# date_filter = 'this quarter'
# date_filter = 'this month'
# date_filter = 'this week'
# date_filter = 'today'  # date_filter = 'this day'

# date_filter = 'next year'
# date_filter = 'next quarter'
# date_filter = 'next month'
# date_filter = 'next week'
# date_filter = 'tomorrow'  # date_filter = 'next day'

# date_filter = 'last 5 years'
# date_filter = 'last 5 quarters'
# date_filter = 'last 5 months'
# date_filter = 'last 5 weeks'
# date_filter = 'last 5 days'

# date_filter = 'next 3 years'
# date_filter = 'next 3 quarters'
# date_filter = 'next 3 months'
# date_filter = 'next 3 weeks'
# date_filter = 'next 3 days'

# date_filter = 'year to date'
# date_filter = 'quarter to date'
# date_filter = 'month to date'
# date_filter = 'week to date'
# date_filter = 'day to date'

def filter_on_date(df, date_filter, datefield='Accident Occurrence Date'):
    """
    Filters data based on the Date parameter.

    Parameters
    ----------
    df : dataframe
        Data
    date_filter : str
        Date filter
    datefield : datetime, optional
        Date field in the data (default 'Accident Occurrence Date')

    Returns
    -------
    df_filtered
        Data filtered based on date filter
    """

    date_filter = date_filter.lower()
    date_filter_list = date_filter.split()
    now = datetime.now()
    year, quarter, month, week, day = now.year, pd.Timestamp(now).quarter, now.month, pd.Timestamp(now).week, now.day

    if date_filter_list[0] in ('previous', 'yesterday'):
        if date_filter_list[-1] == 'year':
            df_filtered = df[df[datefield].dt.year == year - 1]
        elif date_filter_list[-1] == 'quarter':
            year = year if quarter != 1 else year - 1
            quarter = quarter - 1 if quarter != 1 else 4
            df_filtered = df[(df[datefield].dt.quarter == quarter) & (df[datefield].dt.year == year)]
        elif date_filter_list[-1] == 'month':
            year = year if month != 1 else year - 1
            month = month - 1 if month != 1 else 12
            df_filtered = df[(df[datefield].dt.month == month) & (df[datefield].dt.year == year)]
        elif date_filter_list[-1] == 'week':
            year = year if week != 1 else year - 1
            week = week - 1 if week != 1 else date(year, 12, 31).isocalendar()[1]
            df_filtered = df[(df[datefield].dt.week == week) & (df[datefield].dt.year == year)]
        elif date_filter_list[0] == 'yesterday':
            if month == 1 and day == 1:
                year, month, day = year - 1, 12, 31
            elif month != 1 and day == 1:
                year, month, day = year, month - 1, calendar.monthrange(year, month - 1)[1]
            else:
                year, month, day = year, month, day - 1
            df_filtered = df[df[datefield].dt.date == date(year, month, day)]

    elif date_filter_list[0] in ('this', 'today'):
        if date_filter_list[-1] == 'year':
            df_filtered = df[df[datefield].dt.year == year]
        elif date_filter_list[-1] == 'quarter':
            df_filtered = df[(df[datefield].dt.quarter == quarter) & (df[datefield].dt.year == year)]
        elif date_filter_list[-1] == 'month':
            df_filtered = df[(df[datefield].dt.month == month) & (df[datefield].dt.year == year)]
        elif date_filter_list[-1] == 'week':
            df_filtered = df[(df[datefield].dt.week == week) & (df[datefield].dt.year == year)]
        elif date_filter_list[0] == 'today':
            df_filtered = df[df[datefield].dt.date == date(year, month, day)]

    elif (date_filter_list[0] == 'next' and len(date_filter_list) == 2) or date_filter_list[0] == 'tomorrow':
        if date_filter_list[-1] == 'year':
            df_filtered = df[df[datefield].dt.year == year + 1]
        elif date_filter_list[-1] == 'quarter':
            year = year if quarter != 4 else year + 1
            quarter = quarter + 1 if quarter != 4 else 1
            df_filtered = df[(df[datefield].dt.quarter == quarter) & (df[datefield].dt.year == year)]
        elif date_filter_list[-1] == 'month':
            year = year if month != 12 else year + 1
            month = month + 1 if month != 12 else 1
            df_filtered = df[(df[datefield].dt.month == month) & (df[datefield].dt.year == year)]
        elif date_filter_list[-1] == 'week':
            year = year if week != date(year, 12, 31).isocalendar()[1] else year + 1
            week = week + 1 if week != date(year, 12, 31).isocalendar()[1] else 1
            df_filtered = df[(df[datefield].dt.week == week) & (df[datefield].dt.year == year)]
        elif date_filter_list[0] == 'tomorrow':
            if month == 12 and day == 31:
                year, month, day = year + 1, 1, 1
            elif month != 12 and day == calendar.monthrange(year, month)[1]:
                year, month, day = year, month + 1, 1
            else:
                year, month, day = year, month, day + 1
            df_filtered = df[df[datefield].dt.date == date(year, month, day)]

    elif date_filter_list[0] == 'last' and len(date_filter_list) == 3:
        N = int(date_filter_list[1]) - 1
        if date_filter_list[-1] == 'years':
            df_filtered = df[(df[datefield].dt.year >= year - N) & (df[datefield].dt.year <= year)]

        elif date_filter_list[-1] == 'quarters':
            new_date = (now - pd.DateOffset(months=3 * N)).date().replace(day=1)
            df_filtered = df[(df[datefield].dt.date >= new_date) & (
                        (df[datefield].dt.year <= year) & (df[datefield].dt.quarter <= quarter))]

        elif date_filter_list[-1] == 'months':
            new_date = (now - pd.DateOffset(months=N)).date().replace(day=1)
            df_filtered = df[(df[datefield].dt.date >= new_date) & (
                        (df[datefield].dt.year <= year) & (df[datefield].dt.month <= month))]
        elif date_filter_list[-1] == 'weeks':
            new_date = (now - timedelta(days=7 * (N))).date()
            d = "{}-{}-1".format(new_date.year, pd.Timestamp(new_date).week)
            new_date = pd.to_datetime(datetime.strptime(d, "%Y-%W-%w").strftime('%Y-%m-%d'))
            df_filtered = df[(df[datefield].dt.date >= new_date) & (
                        (df[datefield].dt.year <= year) & (df[datefield].dt.week <= week))]
        elif date_filter_list[-1] == 'days':
            new_date = (now - timedelta(days=N)).date()
            df_filtered = df[(df[datefield].dt.date >= new_date) & (df[datefield].dt.date <= date(year, month, day))]

    elif date_filter_list[0] == 'next' and len(date_filter_list) == 3:
        N = int(date_filter_list[1]) - 1
        if date_filter_list[-1] == 'years':
            df_filtered = df[(df[datefield].dt.year >= year) & (df[datefield].dt.year <= year + N)]
        elif date_filter_list[-1] == 'quarters':
            new_date = (now + pd.DateOffset(months=3 * (N + 1) - 1)).date()
            new_date = new_date.replace(day=calendar.monthrange(new_date.year, new_date.month)[1])
            df_filtered = df[(df[datefield].dt.date <= new_date) & (
                        (df[datefield].dt.year >= year) & (df[datefield].dt.quarter >= quarter))]
        elif date_filter_list[-1] == 'months':
            new_date = (now + pd.DateOffset(months=N)).date()
            new_date = new_date.replace(day=calendar.monthrange(new_date.year, new_date.month)[1])
            df_filtered = df[(df[datefield].dt.date <= new_date) & (
                        (df[datefield].dt.year >= year) & (df[datefield].dt.month >= month))]
        elif date_filter_list[-1] == 'weeks':
            new_date = (now + timedelta(days=7 * (N))).date()
            d = "{}-{}-1".format(new_date.year, pd.Timestamp(new_date).week)
            new_date = pd.to_datetime(datetime.strptime(d, "%Y-%W-%w").strftime('%Y-%m-%d'))
            new_date = new_date.replace(day=new_date.day + 6)
            df_filtered = df[(df[datefield].dt.date <= new_date) & (
                        (df[datefield].dt.year >= year) & (df[datefield].dt.week >= week))]
        elif date_filter_list[-1] == 'days':
            new_date = (now + timedelta(days=N)).date()
            df_filtered = df[(df[datefield].dt.date <= new_date) & (df[datefield].dt.date >= date(year, month, day))]

    elif date_filter_list[-1] == 'date' and len(date_filter_list) == 3:
        if date_filter_list[0] == 'year':
            df_filtered = df[(df[datefield].dt.year == year) & (df[datefield].dt.date <= date(year, month, day))]
        elif date_filter_list[0] == 'quarter':
            df_filtered = df[(df[datefield].dt.quarter == quarter) & (df[datefield].dt.year == year) & (
                        df[datefield].dt.date <= date(year, month, day))]
        elif date_filter_list[0] == 'month':
            df_filtered = df[(df[datefield].dt.month == month) & (df[datefield].dt.year == year) & (
                        df[datefield].dt.date <= date(year, month, day))]
        elif date_filter_list[0] == 'week':
            df_filtered = df[(df[datefield].dt.week == week) & (df[datefield].dt.year == year) & (
                        df[datefield].dt.date <= date(year, month, day))]
        elif date_filter_list[0] == 'day':
            df_filtered = df[(df[datefield].dt.date == date(year, month, day)) & (
                        df[datefield] <= datetime(year, month, day, now.hour, now.minute, now.second))]

    return df_filtered


def filter_data(df,
                client_type=None,
                accident_nature=None,
                accident_status=None,
                appeal_status=None,
                ):
    """Returns filtered df by columns: Client Type, Accident Nature, Accident Status, Appeal Status"""
    df_filtered = df.copy(deep=True)

    if client_type:
        df_filtered = df_filtered[df_filtered['Client Type'].isin(client_type)]
    if accident_nature:
        df_filtered = df_filtered[df_filtered['Accident Nature'].isin(accident_nature)]
    if accident_status:
        df_filtered = df_filtered[df_filtered['Accident Status'].isin(accident_status)]
    if appeal_status:
        df_filtered = df_filtered[df_filtered['Appeal Status'].isin(appeal_status)]

    return df_filtered


def value_format(value):
    """
    returns float value in converted necessary format which was chosen in config and rounded by 2
    Possible formats:
    '.' : 103301.321 -> 103,301.321
    ' ' : 103301.321 -> 103 301.321
    ',' : 103301.321 -> 103.301,321
    'X' : 103301.321 -> 103X301.321
    """
    with open('config.json', 'r') as f:
        number_format = json.load(f)['number_format']
    value = round(value, 2)
    value_str = '{:,}'.format(value)
    if number_format == '.':
        value_str = value_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    else:
        value_str = value_str.replace(',', number_format)
    return value_str


def get_palette(type):
    """
    returns palette which was chosen in config

    type:
    'list': returns palette in list format
    'dict': returns palette in dict format
    """
    def palette_typed(palette, type):
        if type == 'dict':
            palette = {index + 1: palette[index] for index in range(len(palette))}
            return palette
        elif type == 'list':
            return palette

    with open('config.json', 'r') as f:
        palette = json.load(f)["color_palette"]["palette"]
    if palette == "red_palette":
        return palette_typed(red_palette, type)
    elif palette == "blue_palette":
        return palette_typed(blue_palette, type)
    elif palette == "diverging_palette":
        return palette_typed(diverging_palette, type)
    elif palette == "orange_palette":
        return palette_typed(orange_palette, type)
    else:
        sys.exit('You did not specify the correct palette')


def get_currency_sign():
    """returns currency sign which was chosen in config"""
    with open('config.json', 'r', encoding='utf8') as f:
        currency_sign = json.load(f)['currency_sign']
    return currency_sign


def set_favicon(path):
    """
    copy file 'path' to /assets which allows you to set favicon

    path: url or path to file
    """
    import os
    import requests
    import shutil

    if os.path.exists(path):
        shutil.copyfile(path, 'assets/favicon.ico')
    else:
        try:
            p = requests.get(path)
            out = open("assets/favicon.ico", "wb")
            out.write(p.content)
            out.close()
        except:
            print('Incorrect path for favicon')

def kpis_prep(df, kpi):
    """
    Preparing column and aggregation function for computing kpi

    Parameters
    ----------
    df : dataframe
        Data
    kpi : str
        KPI to be computed

    Returns
    -------
    column_to_agg
        column to be use in computing
    agg
        aggregation function
    """
    def number_y(df):
        c = 0
        for el in df:
            if el == 'Y':
                c += 1
        return c

    def ppt_y(df):
        return number_y(df) / df.shape[0] * 100

    def work_acc(df):
        c = 0
        for el in df:
            if el > 0:
                c += 1
        return c

    def ppt_work(df):
        return work_acc(df) / df.shape[0] * 100

    def age(df):
        now = datetime.now().year
        l = []
        for el in df:
            l.append(now - el.year)

        return pd.Series(l).mean()

    if kpi == 'Nb of Accidents':
        column_to_agg = 'Accident #'
        agg = 'count'
    elif kpi == 'Nb of Work Accidents':
        column_to_agg = 'Work Accident Flag'
        agg = number_y
    elif kpi == 'Work Accidents %':
        column_to_agg = 'Work Accident Flag'
        agg = ppt_y
    elif kpi == 'Nb of Serious Accidents':
        column_to_agg = 'Serious Accident Flag'
        agg = number_y
    elif kpi == 'Serious Accidents %':
        column_to_agg = 'Serious Accident Flag'
        agg = ppt_y
    elif kpi == 'Nb of Accidents with Work Interruption':
        column_to_agg = 'Work Interruption (days)'
        agg = work_acc
    elif kpi == 'Accidents with Work Interruption %':
        column_to_agg = 'Work Interruption (days)'
        agg = ppt_work
    elif kpi == 'Avg Work Interruption':
        column_to_agg = 'Work Interruption (days)'
        agg = 'mean'
    elif kpi == 'Total Work Interruption':
        column_to_agg = 'Work Interruption (days)'
        agg = 'sum'
    elif kpi == 'Nb of Victims':
        column_to_agg = 'Contract #'
        agg = 'count'
    elif kpi == 'Victim Age':
        column_to_agg = 'Victim Birth Date'
        agg = age
    elif kpi == 'Nb of Deceases':
        column_to_agg = 'Victim Deceased Flag'
        agg = number_y

    return column_to_agg, agg

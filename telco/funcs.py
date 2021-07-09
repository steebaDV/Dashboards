from clickhouse_driver import Client
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import calendar
import json
import sys

# ALL USEFUL FUNCTIONS AND MODULES FOR DATA PROCESSING ARE STORED HERE

import seaborn as sns

# diverging_palette = {index+1: color for index, color in enumerate(sns.color_palette("RdBu", 7).as_hex())}
diverging_palette = sns.color_palette("RdBu", 7).as_hex()

red_palette = sns.color_palette("OrRd", 7).as_hex()

orange_palette = ['#ecda9a',
                  '#efc47e',
                  '#f3ad6a',
                  '#f7945d',
                  '#f97b57',
                  '#f66356',
                  '#ee4d5a'
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

font_family = 'Lato-Regular'


# font_family = 'Lato-Thin'

# fill missing days with 0s
def augment_days(month_int, year, df):
    from calendar import monthrange
    _, max_days = monthrange(year, month_int)
    updated_dates = pd.date_range(f'{month_int}-1-{year}', f'{month_int}-{max_days}-{year}')  # full month range
    df_augmented = df.set_index('DateTime').reindex(updated_dates).fillna(0.0).rename_axis('DateTime').reset_index()

    return df_augmented


def prev(current_year, current_month):
    prev_month = current_month - 1
    if prev_month == 0:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_year = current_year
    return prev_year, calendar.month_abbr[prev_month], current_year, calendar.month_abbr[current_month]


def filter_data(df, call_direction, dropped_reason, network, phonetype):
    df_filtered = df.copy(deep=True)
    if call_direction != '*ALL*':
        df_filtered = df_filtered[df_filtered['Call Direction'] == call_direction]
    if dropped_reason != '*ALL*':
        df_filtered = df_filtered[df_filtered['Dropped Reason'] == dropped_reason]
    if network != '*ALL*':
        df_filtered = df_filtered[df_filtered['Network'] == network]
    if phonetype != '*ALL*':
        df_filtered = df_filtered[df_filtered['Phone Type'] == phonetype]
    return df_filtered


def augment_days_3_m(start_date, end_date, df):
    df.drop_duplicates(subset=["Date", "Product"], keep='first',
                       inplace=True)  # prevents ValueError: cannot reindex from a duplicate axis

    updated_dates = pd.date_range(start_date, end_date)  # full month range
    df_augmented = df.set_index('Date').reindex(updated_dates).fillna(-1).rename_axis('Date').reset_index()
    #
    return df_augmented


def gen_random_number(number):
    import random
    from operator import add, sub, mul
    pct_lst = [i / 100 for i in range(1, 51)]

    operations = (add, sub)  # + /-
    random_operation = random.choice(operations)

    whole_num, part_num = number, number * random.choice(pct_lst)

    random_number = random_operation(whole_num, part_num)
    return abs(int(random_number))  # always positive integer


def set_favicon(path):
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


# def get_dict_number_format():
#     with open('config.json', 'r') as f:
#         number_format = json.load(f)['number_format']
#     dict_number_format = dict()
#     for column in ['Total Calls', 'Dropped Calls', 'Nb of Cell Towers', 'Total Handovers', 'Calls per Cell Tower']:
#         dict_number_format[column] = {
#             'prefix': '',
#             'value_format': number_format["value_int"],
#             'suffix': ''
#         }
#     for column in ['Avg Handovers']:
#         dict_number_format[column] = {
#             'prefix': '',
#             'value_format': number_format["value_float"],
#             'suffix': ''
#         }
#     for column in ['Avg Conversation Time', 'Avg Setup Time']:
#         dict_number_format[column] = {
#             'prefix': '',
#             'value_format': number_format["value_float"],
#             'suffix': ' s' if column in 'Avg Setup Time' else ' min'
#         }
#     for column in ['Dropped Calls %']:
#         dict_number_format[column] = {
#             'prefix': '',
#             'value_format': number_format["value_float"],
#             'suffix': '%'
#         }
#     return dict_number_format


def value_format(value):
    with open('config.json', 'r') as f:
        number_format = json.load(f)['number_format']
    value = round(value, 2)
    value_str = '{:,}'.format(value)
    if number_format == '.':
        value_str = value_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    else:
        value_str = value_str.replace(',', number_format)
    return value_str


def get_palette():
    with open('config.json', 'r') as f:
        palette = json.load(f)["color_palette"]["palette"]
    if palette == "orange_palette":
        return orange_palette
    elif palette == "red_palette":
        return red_palette
    elif palette == "blue_palette":
        return blue_palette
    elif palette == "diverging_palette":
        return diverging_palette
    else:
        sys.exit('You did not specify the correct palette')

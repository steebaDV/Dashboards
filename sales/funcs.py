from clickhouse_driver import Client
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import calendar
import json
import sys


# ALL USEFUL FUNCTIONS AND MODULES FOR DATA PROCESSING ARE STORED HERE
import seaborn as sns

diverging_palette = {index + 1: color for index, color in enumerate(sns.color_palette("RdBu", 7).as_hex())}

red_palette = {index + 1: color for index, color in enumerate(sns.color_palette("OrRd", 7).as_hex())}

orange_palette = {1: '#ecda9a',
                  2: '#efc47e',
                  3: '#f3ad6a',
                  4: '#f7945d',
                  5: '#f97b57',
                  6: '#f66356',
                  7: '#ee4d5a',
                  }

blue_palette = {1: '#d2fbd4',
                2: '#a5dbc2',
                3: '#7bbcb0',
                4: '#559c9e',
                5: '#3a7c89',
                6: '#235d72',
                7: '#123f5a',
                }

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

# fill missing days with 0s
def augment_days(month_int, year, df):
    from calendar import monthrange
    _, max_days = monthrange(year, month_int)
    updated_dates = pd.date_range(f'{month_int}-1-{year}', f'{month_int}-{max_days}-{year}')  # full month range
    df_augmented = df.set_index('DateTime').reindex(updated_dates).fillna(0.0).rename_axis('DateTime').reset_index()

    return df_augmented


def dataframe_difference(df1: pd.DataFrame, df2: pd.DataFrame, which=None):
    """Find rows which are different between two DataFrames."""
    comparison_df = df1.merge(
        df2,
        indicator=True,
        how='outer'
    )
    if which is None:
        diff_df = comparison_df[comparison_df['_merge'] != 'both']
    else:
        diff_df = comparison_df[comparison_df['_merge'] == which]

    return diff_df


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


def get_currency_sign():
    with open('config.json', 'r', encoding='utf8') as f:
        currency_sign = json.load(f)['currency_sign']
    return currency_sign


# def get_dict_number_format(currency_sign):
#     with open('config.json', 'r') as f:
#         number_format = json.load(f)['number_format']
#     dict_number_format = dict()
#
#     for column in ['Total Sales', 'Sales per Customer', 'Total Sales Margin']:
#         dict_number_format[column] = {
#             'prefix': f'{currency_sign}',
#             'value_format': number_format["value_float"],
#             'suffix': ''
#         }
#     for column in ['Average Selling Price']:
#         dict_number_format[column] = {
#             'prefix': f'{currency_sign}',
#             'value_format': number_format["value_int"],
#             'suffix': ' d'
#         }
#     for column in ['Total Sold Quantity']:
#         dict_number_format[column] = {
#             'prefix': '',
#             'value_format': number_format["value_float"],
#             'suffix': ''
#         }
#     for column in ['Sales Margin %']:
#         dict_number_format[column] = {
#             'prefix': '',
#             'value_format': number_format["value_int"],
#             'suffix': '%'
#         }
#     for column in ['Active Customers', 'New Customers']:
#         dict_number_format[column] = {
#             'prefix': '',
#             'value_format': number_format["value_int"],
#             'suffix': ''
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

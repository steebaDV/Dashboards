import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import pycountry
import plotly.express as px
import numpy as np
from funcs import font_family


def get_map(df, country=None, customer=None):
    # FILTER BY COUNTRY
    if country is not None:
        df = df[(df['Country'] == country)]

    if customer is not None:
        df = df[(df['Customer'] == customer)]

    print(df)
    df_map = df.groupby('Country').agg({'Total Sales': 'sum', 'Sales Amount Target': 'sum'}).reset_index()
    iso_code_list = []
    for country in df_map['Country']:
        iso_code_list.append(pycountry.countries.search_fuzzy(country)[0].alpha_3)
    df_map['ISO'] = iso_code_list
    with urlopen('https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json') as response:
        counties = json.load(response)
    color_list = []
    for total, target in zip(df_map['Total Sales'], df_map['Sales Amount Target']):
        percent = total / target if target != 0 else np.nan
        if 0 <= percent < 0.6:
            color_list.append(0.2)
        elif 0.6 <= percent < 1:
            color_list.append(0.4)
        elif 1 <= percent < 1.1:
            color_list.append(0.7)
        else:
            color_list.append(1.1)
    df_map['color'] = color_list

    fig = px.choropleth_mapbox(df_map, geojson=counties, color="color",
                               locations="ISO", featureidkey="id",
                               mapbox_style="carto-positron", zoom=1,
                               color_continuous_scale=[[0, 'rgb(173, 94, 75)'],
                                                       [0.4, 'rgb(234, 133, 76)'],
                                                       [0.6, 'rgb(151, 194, 222)'],
                                                       [1, 'rgb(84, 120, 157)']],
                               range_color=[0, 1.2])

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(
        title_text='Total Sales Per Country',
        mapbox_center={"lat": 30, "lon": 20}
    )
    fig.update_layout(coloraxis_showscale=False,
                      autosize=True,
    )

    # SET FONT
    fig.update_layout(autosize=True,
                      font={
                          'family': font_family,
                          # 'color': 'black',
                          # 'size': 12
                      },
    )

    return fig









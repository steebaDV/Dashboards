import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from urllib.request import urlopen
import json
import pycountry
import plotly.express as px
from funcs import font_family, get_currency_sign, get_palette, value_format
from datetime import datetime

currency_sign = get_currency_sign()
palette = get_palette()

def get_state_map(df,
                  kpi,
                  palette=palette,
                  dates=None,
                  state=None,
                  store=None,
                  brand=None,
                  product=None):
    palette = [palette[index] for index in range(1, len(palette))]
    # CURRENCY KPIs
    dollar_kpis = ['Total Sales',
                   'Sales per Store',
                   'Average Inventory Amount',
                   'Total On-Hand Amount',
                   'Average Selling Price',
                   'Average On-hand Price',
                   ]

    def bad_year(x):
        if x.year < datetime.today().year:
            return True
        else:
            return False

    df = df[df['Date'].apply(bad_year)]

    # FILTERS
    # TO-DO: more options for dates

    if store:
        df = df[df['Store'] == store]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]
    if state:
        df = df[df['City'] == state]

    if dates:
        # last n months
        if dates.split()[0] == 'last' and dates.split()[2] == 'months':
            n = int(dates.split()[1])
            start = df['Date'].max() - pd.DateOffset(months=n)
            df = df[df['Date'] >= start]
        # last n years
        if dates.split()[0] == 'last' and dates.split()[2] == 'years':
            n = int(dates.split()[1])
            df = df[df['Current Year'] > (df['Current Year'].max() - n)]


    if kpi == 'Sales per Store':
        kpi1, kpi2 = 'Store', 'Total Sales'
        agg1, agg2 = 'count', 'sum'
    elif kpi == 'Average Inventory Amount':
        kpi1, kpi2 = 'Date', 'Total On-Hand Amount'
        agg1, agg2 = 'count', 'sum'
    elif kpi == 'Average On-hand Price':
        kpi1, kpi2 = 'Total On-Hand Units', 'Total On-Hand Amount'
        agg1, agg2 = 'sum', 'sum'

    if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
        df_map = df.groupby(['City']).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
        df_map.columns = ['City', kpi1, kpi2]
        df_map[kpi] = (df_map[kpi2] / df_map[kpi1]).round()
    else:
        df_map = df.groupby(['City']).agg( { kpi: ['sum'] } ).reset_index()
        df_map.columns = ['City', kpi]
    df_map = df_map.fillna(0.0)
    df_map = df_map.sort_values(by=['City'], ascending=True)
    #df.drop(f'{dimension1} optional', axis=1, inplace=True)

    #can_province = {
    #    'Alberta': 'Alberta',
    #    'British Columbia': 'British Columbia',
    #    'Manitoba': 'Manitoba',
    #    'Brunswick': 'New Brunswick',
    #    'Newfoundland': 'Newfoundland and Labrador',
    #    'Northwest Territories': 'Northwest Territories',
    #    'Nova Scotia': 'Nova Scotia',
    #    'Nunavut': 'Nunavut',
    #    'Ontario': 'Ontario',
    #    'Prince Edward Island': 'Prince Edward Island',
    #    'Quebec': 'Quebec',
    #    'Saskatchewan': 'Saskatchewan',
    #    'Yukon': 'Yukon',
    #}
    #df_map['City'] = df_map['City'].replace(can_province)

    #with urlopen(
    #        'https://gist.githubusercontent.com/john-clarke/8cd86105089e70c013a6e28e8bd663e8/raw/e56f20869fdd518df89e266ef821a54efd9141a9/canada_provinces.geojson') as response:
    #    gj = json.load(response)

    # COLORING
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette) + 1), palette):
        palette2[i] = c
    df_map[f'quantiles_{kpi}'] = pd.cut(df_map[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    df_map[f'quantiles_{kpi}'] = df_map[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()

    import geocoder

    cities_lng = []
    cities_lat = []
    for loc in df_map['City']:
        g = geocoder.osm(loc)
        cities_lng.append(g.json['lng'])
        cities_lat.append(g.json['lat'])

    fig = px.scatter_geo(
                    df_map,
                    lon = cities_lng,
                    lat = cities_lat,
                    #locations=cities_loc,
                    color=kpi,
                    size=kpi,
                    #text=kpi,
                    hover_name='City',
                    hover_data=[kpi],
                    projection="natural earth"
                    )

    # MAP
    #fig = px.choropleth(
    #    #df_map,
    #    #locations='City',
    #    locations=cities_loc,
    #    text=df_map['City']
    #    #featureidkey='properties.name',
    #    scope='world',
    #    #locationmode='geojson-id',
    #    color=kpi,
    #    color_continuous_scale=df_map[f'quantiles_{kpi}'],
    #    hover_data=df_map[['City', kpi]],
    #)

    # UPDATE TITLE FONT
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=12, )

    # UPDATE LAYOUT
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(mapbox_center={"lat": 30, "lon": 20})
    fig.update_layout(coloraxis_showscale=False, autosize=True)

    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',
        plot_bgcolor='rgb(255,255,255)',
        showlegend=False,
        autosize=True,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=25,
                    # pad=0  # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
    )

    # SET FONT
    fig.update_layout(autosize=True,
                      font={
                          'family': font_family,
                          'color': 'black',
                          'size': 12
                      },
                      )

    return fig


def total_sales_per_state(df,
                          kpi,
                          palette=palette,
                          max_bars=None,
                          dates=None,
                          state=None,
                          store=None,
                          brand=None,
                          product=None):
    palette = [palette[index] for index in range(1, len(palette))]
    # CURRENCY KPIs
    dollar_kpis = ['Total Sales',
                   'Sales per Store',
                   'Average Inventory Amount',
                   'Total On-Hand Amount',
                   'Average Selling Price',
                   'Average On-hand Price',
                   ]

    # FILTERS
    # TO-DO: more options for dates
    #print(df.columns)

    if store:
        df = df[df['Store'] == store]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]
    if state:
        df = df[df['City'] == state]

    if dates:
        # last n months
        if dates.split()[0] == 'last' and dates.split()[2] == 'months':
            n = int(dates.split()[1])
            start = df['Date'].max() - pd.DateOffset(months=n)
            df = df[df['Date'] >= start]
        # last n years
        if dates.split()[0] == 'last' and dates.split()[2] == 'years':
            n = int(dates.split()[1])
            df = df[df['Current Year'] > (df['Current Year'].max() - n)]

    # DATA
    # State, Country
    # for further calculation
    if kpi == 'Sales per Store':
        kpi1, kpi2 = 'Store', 'Total Sales'
        agg1, agg2 = 'count', 'sum'
    elif kpi == 'Average Inventory Amount':
        kpi1, kpi2 = 'Date', 'Total On-Hand Amount'
        agg1, agg2 = 'count', 'sum'
    elif kpi == 'Average On-hand Price':
        kpi1, kpi2 = 'Total On-Hand Units', 'Total On-Hand Amount'
        agg1, agg2 = 'sum', 'sum'

    if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
        df = df.groupby(['City', 'Country']).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
        df.columns = ['City', 'Country', kpi1, kpi2]
        df[kpi] = (df[kpi2] / df[kpi1]).round()
    else:
        df = df.groupby(['City', 'Country']).agg( { kpi: ['sum'] } ).reset_index()
        df.columns = ['City', 'Country', kpi]
    df = df.fillna(0.0)
    df = df.sort_values(by=['City', 'Country'], ascending=True)
    #df.drop(f'{dimension1} optional', axis=1, inplace=True)
    
    df = df.reset_index(drop=True)
    df = df.replace([np.inf, -np.inf], np.nan)
    df_state_country = df.groupby(['City', 'Country']).agg(
        {kpi: ['sum']}).reset_index()
    calc = 'Percent of All'
    df_state_country[calc] = df_state_country[kpi] / df_state_country[kpi].sum() * 100
    df_state_country.columns = ['City', 'Country', kpi, calc]

    # COLORING
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette) + 1), palette):
        palette2[i] = c
    df_state_country[f'quantiles_{kpi}'] = pd.cut(df_state_country[kpi], bins=len(palette),
                                                  labels=[key for key in palette2.keys()])
    df_state_country[f'quantiles_{kpi}'] = df_state_country[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()

    if max_bars:
        df_state_country = df_state_country.sort_values(by=kpi, ascending=False).head(max_bars)
    else:
        df_state_country = df_state_country.sort_values(by=kpi, ascending=False)
    y_names = [i + ' | ' + j + ' ' for i, j in zip(df_state_country['City'], df_state_country['Country'])]

    # PLOTTING
    fig = go.Figure()

    # HORIZONTAL BAR CHART: KPI by State, Country
    fig.add_trace(
        go.Bar(
            x=df_state_country[kpi],
            # y = df_state_country[['Country', 'City']],
            y=y_names,
            name='',
            # text = [(f' $ {x:,.0f}') if kpi in dollar_kpis else (f' {x:,.0f}') for x in df_state_country[kpi]],
            text=[(f' {currency_sign} {x:,.0f}   <i>{y:,.2f}%<i>') if kpi in dollar_kpis else (f' {x:,.0f}   <i>{y:,.2f}%<i>') for
                  x, y in zip(df_state_country[kpi], df_state_country[calc])],
            textfont_color=df_state_country[f'quantiles_{kpi}'],
            textposition='outside',
            marker_color=df_state_country[f'quantiles_{kpi}'],
            marker_line={
                'color': df_state_country[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='h',
            hovertemplate='Location: %{y}<br>' + f'{kpi}:' + '%{text}',
            # hoverinfo='none',
        ),
    )

    # Update X axis
    x_max = df_state_country[kpi].max() + (df_state_country[kpi].max() * 0.2)
    fig.update_xaxes(
        zeroline=False,
        showline=False,
        showgrid=False,
        showticklabels=False,
        range=[0, x_max],
    )

    # Update Y axis
    fig.update_yaxes(
        categoryorder='total ascending',
        showgrid=False,
        showline=False,
        showticklabels=True,
    )

    # UPDATE TITLE FONT
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=12, )

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',
        plot_bgcolor='rgb(255,255,255)',
        showlegend=False,
        autosize=True,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=25,
                    # pad=0  # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
    )

    # SET FONT
    fig.update_layout(autosize=True,
                      font={
                          'family': font_family,
                          'color': 'black',
                          'size': 12
                      },
                      )

    return fig


def total_sales_per_country(df,
                            kpi,
                            palette=palette,
                            dates=None,
                            state=None,
                            store=None,
                            brand=None,
                            product=None):
    palette = [palette[index] for index in range(1, len(palette))]
    # CURRENCY KPIs
    dollar_kpis = ['Total Sales',
                   'Sales per Store',
                   'Average Inventory Amount',
                   'Total On-Hand Amount',
                   'Average Selling Price',
                   'Average On-hand Price',
                   ]

    # FILTERS
    # TO-DO: more options for dates
    if store:
        df = df[df['Store'] == store]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]
    if state:
        df = df[df['City'] == state]
        
    if dates:
        # last n months
        if dates.split()[0] == 'last' and dates.split()[2] == 'months':
            n = int(dates.split()[1])
            start = df['Date'].max() - pd.DateOffset(months=n)
            df = df[df['Date'] >= start]
        # last n years
        if dates.split()[0] == 'last' and dates.split()[2] == 'years':
            n = int(dates.split()[1])
            df = df[df['Current Year'] > (df['Current Year'].max() - n)]

    # DATA
    # State, Country
    # for further calculation
    if kpi == 'Sales per Store':
        kpi1, kpi2 = 'Store', 'Total Sales'
        agg1, agg2 = 'count', 'sum'
    elif kpi == 'Average Inventory Amount':
        kpi1, kpi2 = 'Date', 'Total On-Hand Amount'
        agg1, agg2 = 'count', 'sum'
    elif kpi == 'Average On-hand Price':
        kpi1, kpi2 = 'Total On-Hand Units', 'Total On-Hand Amount'
        agg1, agg2 = 'sum', 'sum'

    if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
        df = df.groupby(['City', 'Country']).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
        df.columns = ['City', 'Country', kpi1, kpi2]
        df[kpi] = (df[kpi2] / df[kpi1]).round()
    else:
        df = df.groupby(['City', 'Country']).agg( { kpi: ['sum'] } ).reset_index()
        df.columns = ['City', 'Country', kpi]
    df = df.fillna(0.0)
    df = df.sort_values(by=['City', 'Country'], ascending=True)
    #df.drop(f'{dimension1} optional', axis=1, inplace=True)
    
    df = df.reset_index(drop=True)
    df = df.replace([np.inf, -np.inf], np.nan)

    # Country
    df_country = df.groupby(['Country']).agg(
        {kpi: ['sum']}).reset_index()
    df_country.columns = ['Country', kpi]
    calc = 'Percent of All'
    df_country[calc] = df_country[kpi] / df_country[kpi].sum() * 100
    df_country.columns = ['Country', kpi, calc]

    # COLORING
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette) + 1), palette):
        palette2[i] = c
    df_country[f'quantiles_{kpi}'] = pd.cut(df_country[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    df_country[f'quantiles_{kpi}'] = df_country[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()

    df_country = df_country.sort_values(by=kpi, ascending=False)
    y_names = [i + ' ' for i in df_country['Country']]

    # PLOTTING
    fig = go.Figure()

    # HORIZONTAL BAR CHART: KPI by Country
    fig.add_trace(
        go.Bar(
            x=df_country[kpi],
            y=y_names,
            name='',
            # text = [(f' $ {x:,.0f}') if kpi in dollar_kpis else (f' {x:,.0f}') for x in df_country[kpi]],
            text=[(f' {currency_sign} {value_format(x)}   <i>{value_format(y)}%<i>') if kpi in dollar_kpis else (f' {x:,.0f}   <i>{y:,.2f}%<i>') for
                  x, y in zip(df_country[kpi], df_country[calc])],
            textfont_color=df_country[f'quantiles_{kpi}'],
            textposition='outside',
            marker_color=df_country[f'quantiles_{kpi}'],
            marker_line={
                'color': df_country[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='h',
            hovertemplate='Country: %{y}<br>' + f'{kpi}:' + '%{text}',
            # hoverinfo='none',
        ),
    )

    # Update X axis
    x_max = df_country[kpi].max() + (df_country[kpi].max() * 0.2)
    fig.update_xaxes(
        zeroline=False,
        showline=False,
        showgrid=False,
        showticklabels=False,
        range=[0, x_max],
    )

    # Update Y axis
    fig.update_yaxes(
        categoryorder='total ascending',
        showgrid=False,
        showline=False,
        showticklabels=True,
    )

    # UPDATE TITLE FONT
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=12, )

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',
        plot_bgcolor='rgb(255,255,255)',
        showlegend=False,
        autosize=True,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=25,
                    # pad=0  # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
    )

    # SET FONT
    fig.update_layout(autosize=True,
                      font={
                          'family': font_family,
                          'color': 'black',
                          'size': 12
                      },
                      )

    return fig

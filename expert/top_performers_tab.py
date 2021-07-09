import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, augment_days, filter_data, prev, get_currency_sign, value_format, get_palette

palette = get_palette()
currency_sign = get_currency_sign()



def get_bar_chart_and_line(df,
                           current_year,
                           current_month,
                           chart_type,
                           customer=None,
                           country=None,
                           product_group=None,
                           palette=palette):
    palette = [palette[index] for index in range(1, len(palette) + 1)]
    # GENERATE MONTHS SEQUENCE for: Current Month vs Same Month, Previous Year
    years = [current_year]
    months = [current_month]
    for i in range(11):
        month = months[0] - 1
        year = years[0]
        if month == 0:
            month = 12
            year -= 1
        years.insert(0, year)
        months.insert(0, month)
    for i in range(len(months)):
        if len(str(months[i])) == 1:
            months[i] = '0' + str(months[i])
        else:
            months[i] = str(months[i])
    if months[-1] == '12':
        months[-1] = 0
        years[-1] = years[-1] + 1


    # DATA
    df_filtered = filter_data(df, customer, country, product_group)
    if chart_type == 'Active Customers #':  # in ['Active Customers #', 'New Customers #']:

        # Active Customers #
        df_groupby = df_filtered[
            (df_filtered['DateTime'] >= f'{years[0]}-{months[0]}-01') &
            (df_filtered['DateTime'] < f'{years[-1]}-{int(months[-1]) + 1}-01')
            ]  # .groupby( pd.Grouper(key='DateTime', freq='M') ).agg( {chart_type: ['sum']} ).reset_index()
        df_groupby_prev = df_filtered[
            (df_filtered['DateTime'] >= f'{years[0] - 1}-{months[0]}-01') &
            (df_filtered['DateTime'] < f'{years[-1] - 1}-{int(months[-1]) + 1}-01')
            ]  # .groupby( pd.Grouper(key='DateTime', freq='M') ).agg( {chart_type: ['sum']} ).reset_index()

        df_groupby[chart_type] = df_groupby[['Customer', 'Country']].agg(' '.join, axis=1)
        df_groupby = df_groupby.groupby(pd.Grouper(key='DateTime', freq='M'))[
            chart_type].nunique()  # unique customers by month !!!
        df_groupby = df_groupby.to_frame().reset_index()

        df_groupby_prev[chart_type] = df_groupby_prev[['Customer', 'Country']].agg(' '.join, axis=1)
        df_groupby_prev = df_groupby_prev.groupby(pd.Grouper(key='DateTime', freq='M'))[
            chart_type].nunique()  # unique customers by month !!!
        df_groupby_prev = df_groupby_prev.to_frame().reset_index()

    else:
        if chart_type[-1] == '%':
            df_groupby = df_filtered[
                (df_filtered['DateTime'] >= f'{years[0]}-{months[0]}-01') &
                (df_filtered['DateTime'] < f'{years[-1]}-{int(months[-1]) + 1}-01')
                ].groupby(pd.Grouper(key='DateTime', freq='M')).agg({chart_type: ['mean']}).reset_index()
            df_groupby_prev = df_filtered[
                (df_filtered['DateTime'] >= f'{years[0] - 1}-{months[0]}-01') &
                (df_filtered['DateTime'] < f'{years[-1] - 1}-{int(months[-1]) + 1}-01')
                ].groupby(pd.Grouper(key='DateTime', freq='M')).agg({chart_type: ['mean']}).reset_index()
        else:
            df_groupby = df_filtered[
                (df_filtered['DateTime'] >= f'{years[0]}-{months[0]}-01') &
                (df_filtered['DateTime'] < f'{years[-1]}-{int(months[-1]) + 1}-01')
                ].groupby(pd.Grouper(key='DateTime', freq='M')).agg({chart_type: ['sum']}).reset_index()
            df_groupby_prev = df_filtered[
                (df_filtered['DateTime'] >= f'{years[0] - 1}-{months[0]}-01') &
                (df_filtered['DateTime'] < f'{years[-1] - 1}-{int(months[-1]) + 1}-01')
                ].groupby(pd.Grouper(key='DateTime', freq='M')).agg({chart_type: ['sum']}).reset_index()

    df_groupby['Month'] = df_groupby['DateTime'].dt.month
    df_groupby_prev['Month'] = df_groupby_prev['DateTime'].dt.month

    df_groupby['DateTime'] = df_groupby['DateTime'].apply(
        lambda x: f'{calendar.month_abbr[x.month]} {str(x.year)}')
    df_groupby.columns = ['DateTime', chart_type, 'Month']

    df_groupby_prev['DateTime'] = df_groupby_prev['DateTime'].apply(
        lambda x: f'{calendar.month_abbr[x.month]} {str(x.year)}')
    df_groupby_prev.columns = ['DateTime', f'{chart_type} prev', 'Month']

    df_groupby = pd.merge(df_groupby, df_groupby_prev, how='inner', on='Month')
    df_groupby.columns = ['DateTime', f'{chart_type}', 'Month', 'DateTime prev', f'{chart_type} prev']

    # COLORING
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette) + 1), palette):
        palette2[i] = c
    df_groupby[f'quantiles_{chart_type}'] = pd.cut(df_groupby[chart_type], bins=len(palette),
                                                   labels=[key for key in palette2.keys()])
    df_groupby[f'quantiles_{chart_type}'] = df_groupby[f'quantiles_{chart_type}'].map(lambda x: palette2[x])
    palette.reverse()

    df_x = df_groupby['DateTime'].values
    df_y = df_groupby[chart_type].values.T
    df_y_prev = df_groupby[f'{chart_type} prev'].values.T

    # ADDING TEXT
    bar_text = []
    for i in range(len(months)):
        value_text = f'{value_format(df_y[i])}'
        if chart_type in ['Total Sales', 'Total Sales Margin']:
            value_text = currency_sign + value_text
        elif chart_type == 'Sales Margin %':
            value_text += '%'
        bar_text.append(f'{value_text}')

    # PLOTTING
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_x,
            y=df_y,
            name='Current period',
            cliponaxis=False,
            text=bar_text,
            textposition='outside',
            textfont_color=df_groupby[f'quantiles_{chart_type}'],
            marker_color=df_groupby[f'quantiles_{chart_type}'],
            marker_line={
                'color': df_groupby[f'quantiles_{chart_type}'],
                'width': 1,
            },
            # orientation='v',
            hoverinfo='none',
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_x,
            y=df_y_prev,
            name='Previous period',
            mode='lines',
            line_color='grey',
            cliponaxis=False,
            # text = df_groupby['DateTime prev'],
            text=[(f'Month: {y}<br>{chart_type}: {currency_sign} {value_format(x)}') if chart_type in ['Total Sales',
                                                                                'Total Sales Margin'] else (
                f'Month: {y}<br>{chart_type}: {value_format(x)}') for x, y in zip(df_y_prev, df_groupby['DateTime prev'])],
            # hoverinfo='none',
            hovertemplate='%{text}',
        )
    )

    fig.update_yaxes(showticklabels=False, )
    fig.update_layout(
        font_color='Grey',
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        autosize=True,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=25,
                    # pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family
        # width=800,
        # height=500,
    )

    return fig
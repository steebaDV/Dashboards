import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, augment_days, orange_palette, get_currency_sign, get_palette, value_format

currency_sign = get_currency_sign()
palette = get_palette()


def pareto_analysis(df,
                    column_to_group_by,
                    kpi,
                    palette=palette,
                    dates=None,
                    state=None,
                    store=None,
                    brand=None,
                    product=None):
    palette = [palette[index] for index in range(1, len(palette))]
    # CURRENCY KPI_S
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
        df = df.groupby([column_to_group_by]).agg({kpi1: [agg1], kpi2: [agg2]}).reset_index()
        df.columns = [column_to_group_by, kpi1, kpi2]
        df[kpi] = (df[kpi2] / df[kpi1]).round()
    else:
        df = df.groupby([column_to_group_by]).agg({kpi: ['sum']}).reset_index()
        df.columns = [column_to_group_by, kpi]
    df = df.fillna(0.0)
    df = df.sort_values(by=[column_to_group_by], ascending=True)
    # df.drop(f'{dimension1} optional', axis=1, inplace=True)

    df = df.reset_index(drop=True)
    df = df.replace([np.inf, -np.inf], np.nan)

    total_df = df.groupby([column_to_group_by]).agg(
        {kpi: ['sum']}).reset_index()
    total_df.columns = [column_to_group_by, kpi]
    total_df = total_df.sort_values(by=kpi, ascending=False)
    cumsum = 'Cumulative kpi'
    total_df[cumsum] = total_df[kpi].cumsum()
    calc = 'Cumulative Percent'
    total_df[calc] = total_df[cumsum] / total_df[kpi].sum() * 100
    total_df.columns = [column_to_group_by, kpi, cumsum, calc]

    # COLORING
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette) + 1), palette):
        palette2[i] = c
    total_df[f'quantiles_{kpi}'] = pd.cut(total_df[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    total_df[f'quantiles_{kpi}'] = total_df[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()

    # PLOTTING
    fig = go.Figure()

    # Line Chart for cumulative percents
    fig.add_trace(
        go.Scatter(
            x=total_df[column_to_group_by],
            y=total_df[calc],
            name='',
            mode='lines',
            line_shape='spline',
            line_color='#F0F0F0',
            fill='tozeroy',
            fillcolor='#F0F0F0',
            hoverinfo='none',
            opacity=0.3,
        ),
    )

    # Vertical Bar Chart for kpi + dimension
    fig.add_trace(
        go.Bar(
            x=total_df[column_to_group_by],
            y=total_df[kpi],
            text=[(f' {currency_sign} {value_format(x)}') if kpi in dollar_kpis else (f' {value_format(x)}') for x in total_df[kpi]],
            textfont_color=total_df[f'quantiles_{kpi}'],
            textposition='outside',
            marker_color=total_df[f'quantiles_{kpi}'],
            marker_line={
                'color': total_df[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='v',
            hoverinfo='none',
            yaxis='y2',
        ),
    )

    # Text point for Line Chart
    fig.add_trace(
        go.Scatter(
            x=total_df[column_to_group_by],
            y=total_df[calc],
            name='',
            mode='text',
            text=[(f'{value_format(x)}%') for x in total_df[calc]],
            textposition='top center',
            hoverinfo='none',
            yaxis='y3',
        ),
    )

    # Create axis objects
    fig.update_layout(
        yaxis2=dict(
            overlaying='y',
        ),
        yaxis3=dict(
            overlaying='y',
        ),
    )

    # Update Y axis
    fig.update_yaxes(
        showticklabels=False,
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

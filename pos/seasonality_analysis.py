import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from plotly.subplots import make_subplots
import plotly.figure_factory as ff  # NEW
from funcs import font_family, augment_days, orange_palette, get_currency_sign, get_palette, value_format
from datetime import datetime

currency_sign = get_currency_sign()
palette = get_palette()


def seasonality_analysis(df,
                         dimension,  # looks like 'dimension1 x dimension2'
                         kpi,
                         palette=palette,
                         dates=None,
                         state=None,
                         store=None,
                         brand=None,
                         product=None):
    palette = [palette[index] for index in range(1, len(palette))]
    # CURRENCY KPIs
    currency_kpis = ['Total Sales',
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
    if store:
        df = df[df['Store'] == store]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]
    if state:
        df = df[df['City'] == state]
    dimension1, dimension2 = dimension.split(' x ')

    # DATA

    if dimension1 == 'Year':
        df[dimension1] = df['Date'].dt.year
    elif dimension1 == 'Month':
        df[dimension1] = df['Date'].dt.month_name()
        df[f'{dimension1} optional'] = df['Date'].dt.month
    elif dimension1 == 'Week':
        df[dimension1] = 'w' + df['Date'].dt.isocalendar().week.astype('str')
        df[f'{dimension1} optional'] = df['Date'].dt.isocalendar().week
    elif dimension1 == 'Day of Week':
        df[dimension1] = df['Date'].dt.day_name()
        df[f'{dimension1} optional'] = df['Date'].dt.dayofweek

    if dimension2 == 'Quarter':
        df[dimension2] = 'Q' + df['Date'].dt.quarter.astype('str')
    elif dimension2 == 'Month':
        df[dimension2] = df['Date'].dt.month_name()
        df[f'{dimension2} optional'] = df['Date'].dt.month
    elif dimension2 == 'Week':
        df[dimension2] = 'w' + df['Date'].dt.isocalendar().week.astype('str')
        df[f'{dimension2} optional'] = df['Date'].dt.isocalendar().week
    elif dimension2 == 'Day of Year':
        df[dimension2] = df['Date'].dt.dayofyear
    elif dimension2 == 'Day of Month':
        df[dimension2] = df['Date'].dt.day
    elif dimension2 == 'Day of Week':
        df[dimension2] = df['Date'].dt.day_name()
        df[f'{dimension2} optional'] = df['Date'].dt.dayofweek
    elif dimension2 == 'Hour':
        df[dimension2] = df['Date'].dt.hour

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

    # DATA - RIGHT BAR CHART - dimension1
    if dimension1 in ['Month', 'Week', 'Day of Week']:
        if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
            df1 = df.groupby([dimension1, f'{dimension1} optional']).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
            df1.columns = [dimension1, f'{dimension1} optional', kpi1, kpi2]
            df1[kpi] = (df1[kpi2] / df1[kpi1]).round()
        else:
            df1 = df.groupby([dimension1, f'{dimension1} optional']).agg( { kpi: ['sum'] } ).reset_index()
            df1.columns = [dimension1, f'{dimension1} optional', kpi]
        df1 = df1.fillna(0.0)
        df1 = df1.sort_values(by=f'{dimension1} optional', ascending=True)
        df1.drop(f'{dimension1} optional', axis=1, inplace=True)
    else:
        if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
            df1 = df.groupby(dimension1).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
            df1.columns = [dimension1, kpi1, kpi2]
            df1[kpi] = (df1[kpi2] / df1[kpi1]).round()
        else:
            df1 = df.groupby(dimension1).agg( { kpi: ['sum'] } ).reset_index()
            df1.columns = [dimension1, kpi]
        df1 = df1.fillna(0.0)
        df1 = df1.sort_values(by=dimension1, ascending=True)
    df1 = df1.reset_index(drop=True)
    df1 = df1.replace([np.inf, -np.inf], np.nan)

    # DATA - TOP BAR CHART - dimension2
    if dimension2 in ['Month', 'Week', 'Day of Week']:
        if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
            df2 = df.groupby([dimension2, f'{dimension2} optional']).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
            df2.columns = [dimension2, f'{dimension2} optional', kpi1, kpi2]
            df2[kpi] = (df2[kpi2] / df2[kpi1]).round()
        else:
            df2 = df.groupby([dimension2, f'{dimension2} optional']).agg( { kpi: ['sum'] } ).reset_index()
            df2.columns = [dimension2, f'{dimension2} optional', kpi]
        df2 = df2.fillna(0.0)
        df2 = df2.sort_values(by=f'{dimension2} optional', ascending=True)
        df2.drop(f'{dimension2} optional', axis=1, inplace=True)
    else:
        if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
            df2 = df.groupby(dimension2).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
            df2.columns = [dimension2, kpi1, kpi2]
            df2[kpi] = (df2[kpi2] / df2[kpi1]).round()
        else:
            df2 = df.groupby(dimension2).agg( { kpi: ['sum'] } ).reset_index()
            df2.columns = [dimension2, kpi]
        df2 = df2.fillna(0.0)
        df2 = df2.sort_values(by=dimension2, ascending=True)
    df2 = df2.reset_index(drop=True)
    df2 = df2.replace([np.inf, -np.inf], np.nan)

    # DATA - HEATMAP
    if dimension == 'Week x Day of Week':
        if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
            df3 = df.groupby([f'{dimension2} optional', f'{dimension1} optional']).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
            df3.columns = [f'{dimension2} optional', f'{dimension1} optional', kpi1, kpi2]
            df3[kpi] = (df3[kpi2] / df3[kpi1]).round()
        else:
            df3 = df.groupby([f'{dimension2} optional', f'{dimension1} optional']).agg( { kpi: ['sum'] } ).reset_index()
            df3.columns = [f'{dimension2} optional', f'{dimension1} optional', kpi]
        df3 = df3.fillna(0.0)
        df3 = df3.pivot(index=f'{dimension1} optional', columns=f'{dimension2} optional', values=kpi)
        df3.index = df1[dimension1].unique()
        df3.columns = df2[dimension2].unique()

    if dimension != 'Week x Day of Week' and dimension1 in ['Month', 'Week', 'Day of Week']:
        if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
            df3 = df.groupby([dimension2, f'{dimension1} optional']).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
            df3.columns = [dimension2, f'{dimension1} optional', kpi1, kpi2]
            df3[kpi] = (df3[kpi2] / df3[kpi1]).round()
        else:
            df3 = df.groupby([dimension2, f'{dimension1} optional']).agg( { kpi: ['sum'] } ).reset_index()
            df3.columns = [dimension2, f'{dimension1} optional', kpi]
        df3 = df3.fillna(0.0)
        df3 = df3.pivot(index=f'{dimension1} optional', columns=dimension2, values=kpi)
        df3.index = df1[dimension1].unique()

    if dimension != 'Week x Day of Week' and dimension2 in ['Month', 'Week', 'Day of Week']:
        if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
            df3 = df.groupby([f'{dimension2} optional', dimension1]).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
            df3.columns = [f'{dimension2} optional', dimension1, kpi1, kpi2]
            df3[kpi] = (df3[kpi2] / df3[kpi1]).round()
        else:
            df3 = df.groupby([f'{dimension2} optional', dimension1]).agg( { kpi: ['sum'] } ).reset_index()
            df3.columns = [f'{dimension2} optional', dimension1, kpi]
        df3 = df3.fillna(0.0)
        df3 = df3.pivot(index=dimension1, columns=f'{dimension2} optional', values=kpi)
        df3.columns = df2[dimension2].unique()

    if dimension1 not in ['Month', 'Week', 'Day of Week'] and dimension2 not in ['Month', 'Week', 'Day of Week']:
        if kpi in ['Sales per Store', 'Average Inventory Amount', 'Average On-hand Price']:
            df3 = df.groupby([dimension2, dimension1]).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
            df3.columns = [dimension2, dimension1, kpi1, kpi2]
            df3[kpi] = (df3[kpi2] / df3[kpi1]).round()
        else:
            df3 = df.groupby([dimension2, dimension1]).agg( { kpi: ['sum'] } ).reset_index()
            df3.columns = [dimension2, dimension1, kpi]
        df3 = df3.fillna(0.0)
        df3 = df3.pivot(index=dimension1, columns=dimension2, values=kpi)

    df3 = df3.replace([np.inf, -np.inf], np.nan)

    # COLORING
    # palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette)+1), palette):
        palette2[i] = c
    df1[f'quantiles_{kpi}'] = pd.cut(df1[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    df1[f'quantiles_{kpi}'] = df1[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    df2[f'quantiles_{kpi}'] = pd.cut(df2[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    df2[f'quantiles_{kpi}'] = df2[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    # palette.reverse()

    # PLOTTING
    fig = make_subplots(
        rows=2, cols=2, 
        column_widths=[0.7, 0.3], 
        row_heights=[0.3, 0.7],
        horizontal_spacing=0.01,
    )  # print_grid=True)

    # TOP Vertical Bar Chart for kpi + dimension2
    fig.add_trace(
        go.Bar(
            x = df2[dimension2],
            y = df2[kpi],
            name='',
            text = [(f' {currency_sign} {value_format(x)}') if kpi in currency_kpis else (f' {value_format(x)}') for x in df2[kpi]],
            textposition='outside',
            marker_color = df2[f'quantiles_{kpi}'],
            marker_line = {
                'color': df2[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='v',
            hovertemplate = f'{dimension2}:' + ' %{x}<br>' + f'{kpi}:' + '%{text}',
        ),
        row=1, col=1,
    )

    # RIGHT Horizontal Bar Chart for kpi + dimension1
    fig.add_trace(
        go.Bar(
            x = df1[kpi],
            y = df1[dimension1],
            name='',
            text = [(f' {currency_sign} {value_format(x)}') if kpi in currency_kpis else (f' {value_format(x)}') for x in df1[kpi]],
            textposition='outside',
            marker_color = df1[f'quantiles_{kpi}'],
            marker_line = {
                'color': df1[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='h',
            hovertemplate = f'{dimension1}:' + ' %{y}<br>' + f'{kpi}:' + '%{text}',
        ),
        row=2, col=2,
    )

    # HEATMAP
    hm = ff.create_annotated_heatmap(
            z=df3.values,
            x=list(df3.columns),
            y=list(df3.index),
            name='',
            annotation_text = [[(f' {currency_sign} {value_format(x)}') if kpi in currency_kpis else (f' {value_format(x)}') for x in row] for row in df3.values],
            # font_colors = ['black', 'black'],
            hovertemplate = f'{dimension1}:' + ' %{y}<br>' + f'{dimension2}:' + ' %{x}<br>' + f'{kpi}:' + ' %{z:,.0f}',
            hoverongaps=False,
            colorscale=list(palette2.values()),
            showscale=False,
    )
    fig.add_trace(
        hm.data[0],
        row=2, col=1,
    )

    # TO-DO: Add better annotations to heatmap
    # annot_bars = list(fig.layout.annotations)
    # annot_hm = list(hm.layout.annotations)
    # for k in range(len(annot_hm)):
    #     annot_hm[k]['xref'] = 'x3'
    #     annot_hm[k]['yref'] = 'y3'
    # # fig.update_layout(
    # #     annotations=annot_bars+annot_hm
    # # )
    # fig.layout.annotations += tuple(annot_hm)

    # Update X axis
    fig.update_xaxes(
        zeroline=False,
        showline=False,
        showgrid=False,
        showticklabels=False,
        dtick='M1',
        # tickformat='%b\n%Y',
        ticks='',
        tickangle=0,
        type='category',
        row=1, col=1,
    )

    fig.update_xaxes(
        zeroline=False,
        showline=False,
        showgrid=False,
        showticklabels=False,
        dtick='M1',
        # tickformat='%b\n%Y',
        ticks='',
        tickangle=0,
        range=[0, df1[kpi].max() + (df1[kpi].max() * 0.2)],
        row=2, col=2,
    )

    fig.update_xaxes(
        type='category',
        showticklabels=True,
        side='top',
        row=2, col=1,
    )

    # Update Y axis
    fig.update_yaxes(
        showticklabels=False,
        range=[0, df2[kpi].max() + (df2[kpi].max() * 0.2)],
        row=1, col=1,
    )

    fig.update_yaxes(
        showticklabels=False,
        type='category',
        row=2, col=2,
    )

    fig.update_yaxes(
        type='category',
        row=2, col=1,
    )

    # UPDATE TITLE FONT
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=12,)

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








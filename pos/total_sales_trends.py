import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, augment_days, get_palette, value_format, get_currency_sign, diverging_palette
from datetime import datetime

currency_sign = get_currency_sign()
palette = get_palette()


def total_sales_trends(df,
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

    if store:
        df = df[df['Store'] == store]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]
    if state:
        df = df[df['City'] == state]


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

    # DATA
    df['Date'] = df['Date'].astype('datetime64[M]')
    
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
        df = df.groupby(['Date']).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
        df.columns = ['Current Month', kpi1, kpi2]
        df[kpi] = (df[kpi2] / df[kpi1]).round()
    else:
        df = df.groupby(['Date']).agg( { kpi: ['sum'] } ).reset_index()
        df.columns = ['Current Month', kpi]
    df = df.fillna(0.0)
    df = df.sort_values(by=['Current Month'], ascending=True)
    #df.drop(f'{dimension1} optional', axis=1, inplace=True)
    
    df = df.reset_index(drop=True)
    df = df.replace([np.inf, -np.inf], np.nan)
    df_months = df.groupby(['Current Month']).agg(
        {kpi: ['sum']}).reset_index()
    calc = 'Percent of All'
    df_months[calc] = df_months[kpi] / df_months[kpi].sum() * 100
    df_months.columns = ['Current Month', kpi, calc]

    df_months = df_months.sort_values(by='Current Month', ascending=True)

    # COLORING
    colored_years = df_months['Current Month'].dt.year.unique().tolist()
    colored_years.reverse()
    palette2 = {}
    for c, y in zip(palette, colored_years):
        palette2[y] = c
    colored_years.reverse()

    # PLOTTING
    fig = go.Figure()

    #print(df_months.head(), df.shape)

    # Separate for each year
    for year in colored_years:
        fig.add_trace(
            go.Scatter(
                x = df_months[df_months['Current Month'].dt.year == year]['Current Month'],
                y = df_months[df_months['Current Month'].dt.year == year][kpi],
                name = '',
                mode = 'lines+text',
                # mode = 'lines',
                line_color = palette2[year],
                fill = 'tozeroy',
                fillcolor = palette2[year],
                # textfont_color = '#365da9',
                text = [(f'{currency_sign} {value_format(x)}') if kpi in dollar_kpis else (f'{value_format(x)}') for x in df_months[df_months['Current Month'].dt.year == year][kpi]],
                textposition='top left',
                # hovertemplate = '%{text}',
                hovertemplate = 'Month: %{x}<br>' + f'{kpi}:' + ' %{text}',
            ),
        )

    # Add grey rectangle for half of the years on the graph
    min_y = df_months[kpi].min()
    max_y = df_months[kpi].max()
    for year in colored_years:
        max_date = df_months.loc[df_months['Current Month'].dt.year == year].max()[0].strftime("%Y-%m-%d")
        min_date = df_months.loc[df_months['Current Month'].dt.year == year].min()[0].strftime("%Y-%m-%d")
        fig.add_vrect(
            x0 = min_date,
            x1 = max_date,
            y0 = min_y if min_y < 0 else 0,
            y1 = max_y + max_y * 0.1,
            fillcolor = ["#E8E8E8" if year % 2 == 0 else "#FFFFFF"][0],
            opacity=0.3,
            layer="below",
            line_width=0,
            annotation_text=year,
            annotation_font_color='black',
            annotation_position="top left",
        )

    # Update X axis
    fig.update_xaxes(
        showline=False,
        showgrid=False,
        showticklabels=True,
        dtick='M1',
        tickformat='%b',
        ticks='',
        tickangle=0,
        title_text=f'<b>{kpi}</b>',
        title_font_color='grey',
    )

    # Update Y axis
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
    )

    # UPDATE TITLE FONT
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=12,)

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        autosize=True,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=20,
                    # pad=100 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
    )

    # SET FONT
    fig.update_layout(autosize=True,
                      font={
                          'family': font_family,
                          'color': 'black',
                          'size': 10
                      },
    )

    return fig


def total_sales_by_brand(df,
                         column_to_group_by,
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
        df = df.groupby([column_to_group_by]).agg( { kpi1: [agg1], kpi2: [agg2] } ).reset_index()
        df.columns = [column_to_group_by, kpi1, kpi2]
        df[kpi] = (df[kpi2] / df[kpi1]).round()
    else:
        df = df.groupby([column_to_group_by]).agg( { kpi: ['sum'] } ).reset_index()
        df.columns = [column_to_group_by, kpi]
    df = df.fillna(0.0)
    df = df.sort_values(by=[column_to_group_by], ascending=True)
    #df.drop(f'{dimension1} optional', axis=1, inplace=True)
    
    df = df.reset_index(drop=True)
    df = df.replace([np.inf, -np.inf], np.nan)
    total_df = df.groupby([column_to_group_by]).agg(
        {kpi: ['sum']}).reset_index()
    calc = 'Percent of All'
    total_df[calc] = total_df[kpi] / total_df[kpi].sum() * 100
    total_df.columns = [column_to_group_by, kpi, calc]

    if not max_bars:
        total_df = total_df.sort_values(by=calc, ascending=False)
    else:
        total_df = total_df.sort_values(by=calc, ascending=False).head(max_bars)

    # COLORING
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette)+1), palette):
        palette2[i] = c
    total_df[f'quantiles_{kpi}'] = pd.cut(total_df[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    total_df[f'quantiles_{kpi}'] = total_df[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()

    # PLOTTING
    fig = go.Figure()

    # One Horizontal Bar Chart
    fig.add_trace(
        go.Bar(
            x = total_df[kpi],
            y = [name + ' ' for name in total_df[column_to_group_by]],
            text = [(f' {currency_sign} {value_format(x)}   <i>{value_format(y)}%<i>') if kpi in dollar_kpis else (f' {value_format(x)}   <i>{value_format(y)}%<i>') for x,y in zip(total_df[kpi], total_df[calc])],
            textfont_color = total_df[f'quantiles_{kpi}'],
            textposition='outside',
            marker_color = total_df[f'quantiles_{kpi}'],
            marker_line = {
                'color': total_df[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='h',
            hoverinfo='none',
        ),
    )

    # Update X axis
    x_max = total_df[kpi].max() + (total_df[kpi].max() * 0.2)
    fig.update_xaxes(
        zeroline=False,
        showline=False,
        showgrid=False,
        showticklabels=False,
        range=[0, 1.05*x_max],
        title_text=f"<b>{kpi}</b><br>by {column_to_group_by}",
        title_font={
            'color': 'grey',
            'size': 10,
        },
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






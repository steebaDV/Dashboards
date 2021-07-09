import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, augment_days, get_currency_sign, value_format

currency_sign = get_currency_sign()


def get_top_kpi_trends(month_int, year, df, kpi,
                              store=None,
                              state=None,
                              brand=None,
                              product=None
                      ):
    # params
    # month_int = 12
    # year = 2020
    # df = df
    # # kpi = 'Total Sales'
    # # kpi = 'Sales per Store'
    # # kpi = 'Average Inventory Amount'
    # # kpi = 'Total On-Hand Amount'

    # Month-to-Date - 1 Year Scope
    end_year = year
    start_year = year - 1  # prev year
    prev_month_int = month_int - 1

    if store:
        df = df[df['Store'] == store]
    if state:
        df = df[df['City'] == state]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]

    # 12M
    from calendar import monthrange

    _, max_days = monthrange(year, month_int)
    start_date, end_date = f'{start_year}-{month_int}-01', f'{end_year}-{month_int}-{max_days}'
    # print(start_date, end_date)
    df_12_m = df[df['Date'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates
    # len(df_12_m) # 650

    # YTD
    from calendar import monthrange

    _, max_days = monthrange(year, month_int)
    start_date, end_date = f'{year}-01-01', f'{year}-{month_int}-{max_days}'
    current_df_ytd = df[df['Date'].between(start_date, end_date, inclusive=True)].copy()

    start_date, end_date = f'{start_year}-01-01', f'{start_year}-{month_int}-{max_days}'
    prev_df_ytd = df[df['Date'].between(start_date, end_date, inclusive=True)].copy()

    if kpi == 'Total Sales':
        # upper part
        df_groupby = df_12_m.groupby(pd.Grouper(key='Date', freq='M')).agg({'Total Sales': ['sum']}).reset_index()
        df_groupby.columns = ['Date', 'Total Sales']

        current_month_kpi = df_groupby[df_groupby['Date'].dt.month == month_int]['Total Sales'].sum()
        prev_month_kpi = df_groupby[df_groupby['Date'].dt.month == prev_month_int]['Total Sales'].sum()
        prev_year_kpi = df_groupby[(df_groupby['Date'].dt.month == month_int) & (df_groupby['Date'].dt.year == start_year)][
            'Total Sales'].sum()

        month_diff, year_diff = 0, 0  # handling /0 error
        if (prev_month_kpi > 0) and (prev_year_kpi > 0):
            month_diff = round((current_month_kpi - prev_month_kpi) / prev_month_kpi * 100,
                               1)  # current month - prev month %
            year_diff = round((current_month_kpi - prev_year_kpi) / prev_year_kpi * 100,
                              1)  # current month - prev year month %

        # lower part
        # current ytd
        current_ytd_grouped = current_df_ytd.groupby(pd.Grouper(key='Date', freq='M')).agg(
            {'Total Sales': ['sum']}).reset_index()
        current_ytd_grouped.columns = ['Date', 'Total Sales']
        current_ytd_grouped['cumsum'] = current_ytd_grouped['Total Sales'].cumsum()
        # prev ytd
        prev_ytd_grouped = prev_df_ytd.groupby(pd.Grouper(key='Date', freq='M')).agg({'Total Sales': ['sum']}).reset_index()
        prev_ytd_grouped.columns = ['Date', 'Total Sales']
        prev_ytd_grouped['cumsum'] = prev_ytd_grouped['Total Sales'].cumsum()

        current_ytd_kpi = current_ytd_grouped['Total Sales'].sum()
        prev_ytd_kpi = prev_ytd_grouped['Total Sales'].sum()

        ytd_diff = 0
        if (prev_ytd_kpi > 0):
            ytd_diff = round((current_ytd_kpi - prev_ytd_kpi) / prev_ytd_kpi * 100, 1)
        # f'{prev_ytd_kpi:,}', f'{current_ytd_kpi:,}'

    elif kpi == 'Sales per Store':
        # upper part
        df_groupby = df_12_m.groupby(pd.Grouper(key='Date', freq='M')).agg(
            {'Store': ['count'], 'Total Sales': ['sum']}).reset_index()
        df_groupby.columns = ['Date', 'Store', 'Total Sales']
        df_groupby[kpi] = round(df_groupby['Total Sales'] / df_groupby['Store'])

        current_month_kpi = df_groupby[df_groupby['Date'].dt.month == month_int][kpi].sum()
        prev_month_kpi = df_groupby[df_groupby['Date'].dt.month == prev_month_int][kpi].sum()
        prev_year_kpi = df_groupby[(df_groupby['Date'].dt.month == month_int) & (df_groupby['Date'].dt.year == start_year)][
            kpi].sum()

        month_diff, year_diff = 0, 0  # handling /0 error
        if (prev_month_kpi > 0) and (prev_year_kpi > 0):
            month_diff = round((current_month_kpi - prev_month_kpi) / prev_month_kpi * 100,
                               1)  # current month - prev month %
            year_diff = round((current_month_kpi - prev_year_kpi) / prev_year_kpi * 100,
                              1)  # current month - prev year month %

        # lower part
        # current ytd
        current_ytd_grouped = current_df_ytd.groupby(pd.Grouper(key='Date', freq='M')).agg(
            {'Store': ['count'], 'Total Sales': ['sum']}).reset_index()
        current_ytd_grouped.columns = ['Date', 'Store', 'Total Sales']
        current_ytd_grouped[kpi] = round(current_ytd_grouped['Total Sales'] / current_ytd_grouped['Store'])

        current_ytd_grouped['cumsum'] = current_ytd_grouped[kpi].cumsum()
        # prev ytd
        prev_ytd_grouped = prev_df_ytd.groupby(pd.Grouper(key='Date', freq='M')).agg(
            {'Store': ['count'], 'Total Sales': ['sum']}).reset_index()
        prev_ytd_grouped.columns = ['Date', 'Store', 'Total Sales']
        prev_ytd_grouped[kpi] = round(prev_ytd_grouped['Total Sales'] / prev_ytd_grouped['Store'])

        prev_ytd_grouped['cumsum'] = prev_ytd_grouped[kpi].cumsum()

        current_ytd_kpi = current_ytd_grouped[kpi].sum()
        prev_ytd_kpi = prev_ytd_grouped[kpi].sum()

        ytd_diff = 0
        if (prev_ytd_kpi > 0):
            ytd_diff = round((current_ytd_kpi - prev_ytd_kpi) / prev_ytd_kpi * 100, 1)
        # f'{prev_ytd_kpi:,}', f'{current_ytd_kpi:,}'

    elif kpi == 'Average Inventory Amount':
        '''Average Inventory Amount = Total On-Hand Amount over the period/Number of Dates'''
        df_groupby = df_12_m.groupby(pd.Grouper(key='Date', freq='M')).agg(
            {'Total On-Hand Amount': ['sum']}).reset_index()
        df_groupby.columns = ['Date', 'Total On-Hand Amount']
        df_groupby[kpi] = (df_groupby['Total On-Hand Amount'] / df_groupby['Date'].dt.day).round()  # Month Total/ Max Days

        current_month_kpi = df_groupby[df_groupby['Date'].dt.month == month_int][kpi].sum()
        prev_month_kpi = df_groupby[df_groupby['Date'].dt.month == prev_month_int][kpi].sum()
        prev_year_kpi = df_groupby[(df_groupby['Date'].dt.month == month_int) & (df_groupby['Date'].dt.year == start_year)][
            kpi].sum()

        month_diff, year_diff = 0, 0  # handling /0 error
        if (prev_month_kpi > 0) and (prev_year_kpi > 0):
            month_diff = round((current_month_kpi - prev_month_kpi) / prev_month_kpi * 100,
                               1)  # current month - prev month %
            year_diff = round((current_month_kpi - prev_year_kpi) / prev_year_kpi * 100,
                              1)  # current month - prev year month %

        # lower part
        # current ytd
        current_ytd_grouped = current_df_ytd.groupby(pd.Grouper(key='Date', freq='M')).agg({'Total On-Hand Amount': ['sum']}).reset_index()
        current_ytd_grouped.columns = ['Date', 'Total On-Hand Amount']
        current_ytd_grouped[kpi] = (current_ytd_grouped['Total On-Hand Amount'] / current_ytd_grouped['Date'].dt.day).round()  # Month Total/ Max Days
        current_ytd_grouped['cumsum'] = current_ytd_grouped[kpi].cumsum()
        # prev ytd
        prev_ytd_grouped = prev_df_ytd.groupby(pd.Grouper(key='Date', freq='M')).agg({'Total On-Hand Amount': ['sum']}).reset_index()
        prev_ytd_grouped.columns = ['Date', 'Total On-Hand Amount']
        prev_ytd_grouped[kpi] = (prev_ytd_grouped['Total On-Hand Amount'] / prev_ytd_grouped['Date'].dt.day).round()  # Month Total/ Max Days
        prev_ytd_grouped['cumsum'] = prev_ytd_grouped[kpi].cumsum()

        current_ytd_kpi = current_ytd_grouped[kpi].sum()
        prev_ytd_kpi = prev_ytd_grouped[kpi].sum()

        ytd_diff = 0
        if (prev_ytd_kpi > 0):
            ytd_diff = round((current_ytd_kpi - prev_ytd_kpi) / prev_ytd_kpi * 100, 1)
        # f'{prev_ytd_kpi:,}', f'{current_ytd_kpi:,}'

    elif kpi == 'Total On-Hand Amount':
        df_groupby = df_12_m.groupby(pd.Grouper(key='Date', freq='M')).agg({kpi: ['sum']}).reset_index()
        df_groupby.columns = ['Date', kpi]

        current_month_kpi = df_groupby[df_groupby['Date'].dt.month == month_int][kpi].sum()
        prev_month_kpi = df_groupby[df_groupby['Date'].dt.month == prev_month_int][kpi].sum()
        prev_year_kpi = df_groupby[(df_groupby['Date'].dt.month == month_int) & (df_groupby['Date'].dt.year == start_year)][
            kpi].sum()

        month_diff, year_diff = 0, 0  # handling /0 error
        if (prev_month_kpi > 0) and (prev_year_kpi > 0):
            month_diff = round((current_month_kpi - prev_month_kpi) / prev_month_kpi * 100,
                               1)  # current month - prev month %
            year_diff = round((current_month_kpi - prev_year_kpi) / prev_year_kpi * 100,
                              1)  # current month - prev year month %

        # lower part
        # current ytd
        current_ytd_grouped = current_df_ytd.groupby(pd.Grouper(key='Date', freq='M')).agg({kpi: ['sum']}).reset_index()
        current_ytd_grouped.columns = ['Date', kpi]
        current_ytd_grouped['cumsum'] = current_ytd_grouped[kpi].cumsum()
        # prev ytd
        prev_ytd_grouped = prev_df_ytd.groupby(pd.Grouper(key='Date', freq='M')).agg({kpi: ['sum']}).reset_index()
        prev_ytd_grouped.columns = ['Date', kpi]
        prev_ytd_grouped['cumsum'] = prev_ytd_grouped[kpi].cumsum()

        current_ytd_kpi = current_ytd_grouped[kpi].sum()
        prev_ytd_kpi = prev_ytd_grouped[kpi].sum()

        ytd_diff = 0
        if (prev_ytd_kpi > 0):
            ytd_diff = round((current_ytd_kpi - prev_ytd_kpi) / prev_ytd_kpi * 100, 1)
        # f'{prev_ytd_kpi:,}', f'{current_ytd_kpi:,}'

    print(kpi)
    # PLOTTING
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=2, cols=1, start_cell="top-left",
                        # subplot_titles=("TOTAL SALES", "SALES MARGIN %", "TOTAL SALES MARGIN",),
                        # column_titles=[f"<b>{chart}</b>" for chart in bar_charts],
                        shared_xaxes=False,  # ! step-like bars
                        shared_yaxes=False,
                        vertical_spacing=0.25,
                        horizontal_spacing=0.03,  # space between the columns
                        )

    # 2 ROWS
    fig.add_trace(
        go.Scatter(x=df_groupby['Date'],  # +-1/2 day difference
                   y=df_groupby[kpi],
                   mode='lines',
                   fill='tozeroy',
                   hovertemplate='<extra></extra>',
                   line_color='darkgray',  # #E8E8E8
                   ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(x=current_ytd_grouped['Date'],
                   y=current_ytd_grouped['cumsum'],
                   mode='lines',
                   fill='tozeroy',
                   hovertemplate='<extra></extra>',
                   line_color='darkgray',  # #E8E8E8
                   ),
        row=2,
        col=1,
    )

    # UPDATE AXES FOR EACH ROW
    # ROW 1
    fig.update_xaxes(
        showline=False,
        showgrid=False,
        showticklabels=True,
        dtick="M1",
        tickformat="%b-%y",
        tickfont=dict(size=9,  # customize tick size
                      # color='default',
                      ),
        ticks='',  # |
        tickangle=45,
        row=1, col=1,
    )

    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
        row=1, col=1,
    )

    # ROW 2
    fig.update_xaxes(
        showline=False,
        showgrid=False,
        showticklabels=True,
        dtick="M1",
        tickformat="%b",
        tickfont=dict(size=7,  # customize tick size
                      # color='default',
                      ),
        ticks='',  # |
        tickangle=0,
        row=2, col=1,
    )

    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
        row=2, col=1,
    )

    # UPPER
    # KPI
    fig.add_annotation(text=f"<b>{currency_sign} {value_format(current_month_kpi)}</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=18,
                           #  color="black"
                       ),
                       x=0.01, y=1, showarrow=False)
    # DIFF
    fig.add_annotation(text=f"<b>▲ {value_format(month_diff)}%</b>" if month_diff > 0 else f"<b>▼ {value_format(month_diff)}%</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=14,
                           color="royalblue"
                       ),
                       x=0.35, y=0.97, showarrow=False)

    fig.add_annotation(text=f"<b>▲ {value_format(year_diff)}%</b>" if year_diff > 0 else f"<b>▼ {value_format(year_diff)}%</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=14,
                           color="royalblue"
                       ),
                       x=0.7, y=0.97, showarrow=False)

    # LOWER
    # KPI
    fig.add_annotation(text=f"<b>{currency_sign} {value_format(current_ytd_kpi)}</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=18,
                           #  color="black"
                       ),
                       x=0.01, y=0.5, showarrow=False)
    # DIFF
    fig.add_annotation(text=f"<b>▲ {value_format(ytd_diff)}%</b>" if ytd_diff > 0 else f"<b>▼ {value_format(ytd_diff)}%</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=14,
                           color="royalblue"
                       ),
                       x=0.7, y=0.455, showarrow=False)

    fig.update_layout(
        paper_bgcolor='white',  #
        plot_bgcolor='white',  # white
        showlegend=False,
        autosize=True,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=20,
                    ),
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







import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, filter_data, get_currency_sign, value_format, get_palette

from plotly.subplots import make_subplots

currency_sign = get_currency_sign()
palette = get_palette()


palette = [palette[index] for index in range(1, len(palette) + 1)]


# TOP PERFORMERS TAB
def get_horizontal_bar_chart(df,
                             current_year,
                             current_month,
                             chart,
                             top,
                             by,
                             customer=None,
                             country=None,
                             product_group=None,
                             palette=palette):
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
    df_filtered.rename(columns={'DateTime': 'DateTime dt'}, inplace=True)
    if top == 'DateTime':
        df_filtered['DateTime'] = df_filtered['DateTime dt'].apply(
            lambda x: f'{calendar.month_abbr[x.month]} {str(x.year)}')
    df_groupby = df_filtered[
        (df_filtered['DateTime dt'] >= f'{years[0]}-{months[0]}-01') &
        (df_filtered['DateTime dt'] < f'{years[-1]}-{int(months[-1]) + 1}-01')
        ]

    # Active Customers #
    active_customers = df_groupby.copy(deep=True)
    active_customers['Active Customers #'] = active_customers[['Customer', 'Country']].agg(' '.join, axis=1)
    active_customers = active_customers.groupby(top)['Active Customers #'].nunique()  # unique customers by month !!!
    active_customers = active_customers.to_frame().reset_index()

    df_groupby = df_groupby.groupby(top).agg(
        {'Total Sales': ['sum'], 'Sales Margin %': ['mean'], 'Total Sales Margin': ['sum']}).reset_index()
    df_groupby.columns = [top, 'Total Sales', 'Sales Margin %', 'Total Sales Margin']
    df_groupby = pd.merge(df_groupby, active_customers, how='inner', on=top)
    df_sorted = df_groupby.sort_values(by=by, ascending=True)

    # PLOTTING
    if chart == 'right':

        fig = make_subplots(
            rows=1, cols=4, start_cell="top-left",
            shared_xaxes=False,
            shared_yaxes=True,  # True?
            specs=[[{'type': 'bar'} for column in range(4)]],  # 1 list for 1 row
            # vertical_spacing=2,
            horizontal_spacing=0.025,  # space between the columns
        )

        for index, chart_type in enumerate(
                ['Total Sales', 'Active Customers #', 'Sales Margin %', 'Total Sales Margin']):
            # for index, chart_type in enumerate(['Total Sales', 'Sales Margin %', 'Total Sales Margin']):
            # Prefix
            if chart_type in ['Total Sales', 'Total Sales Margin']:
                prefix = currency_sign
            else:
                prefix = ''
            # Suffix
            if chart_type == 'Sales Margin %':
                suffix = '%'
            else:
                suffix = ''

            # COLORING
            palette.reverse()
            palette2 = {}
            for i, c in zip(range(1, len(palette) + 1), palette):
                palette2[i] = c
            df_sorted[f'quantiles_{chart_type}'] = pd.cut(df_sorted[chart_type], bins=len(palette),
                                                          labels=[key for key in palette2.keys()])
            df_sorted[f'quantiles_{chart_type}'] = df_sorted[f'quantiles_{chart_type}'].map(lambda x: palette2[x])
            palette.reverse()

            fig.add_trace(
                go.Bar(
                    x=df_sorted[chart_type],
                    y=df_sorted[top],
                    text=[f' {prefix}{value_format(x)}{suffix}' for x in df_sorted[chart_type]],
                    cliponaxis=False,
                    textposition='outside',
                    # marker = {'color': [palette[q] for q in quantile]},
                    marker_color=df_sorted[f'quantiles_{chart_type}'],
                    orientation='h',
                    hoverinfo='none',
                ),
                row=1, col=index + 1,

            ),
            fig.update_xaxes(row=1, col=index + 1,
                             range=[0, 1.35 * df_sorted[chart_type].max()])  # sets the range of xaxis

        fig.update_yaxes(showticklabels=False)
        fig.update_xaxes(showticklabels=False)
        fig.update_layout(
            paper_bgcolor='rgb(255,255,255)',  # white
            plot_bgcolor='rgb(255,255,255)',  # white
            showlegend=False,
            autosize=True,
            # width=1230,
            # height=225,
            margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                        r=0,
                        b=0,
                        t=0,
                        # pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                        ),
            font_family=font_family
            # width=800,
            # height=500,
        )

    else:
        fig = go.Figure(
            go.Bar(
                x=[0] * len(np.unique(df_sorted[top])),
                y=df_sorted[top],
                orientation='h',
                hoverinfo='none',
            )
        )

        fig.update_xaxes(
            showticklabels=False,
            range=[0, 0],  # sets the range of xaxis
            constrain="domain",  # meanwhile compresses the xaxis by decreasing its 'domain'
        )
        fig.update_layout(
            paper_bgcolor='rgb(255,255,255)',  # white
            plot_bgcolor='rgb(255,255,255)',  # white
            showlegend=False,
            autosize=True,
            margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                        r=0,
                        b=0,
                        t=0,
                        # pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                        ),
            font_family=font_family
        )

    return fig


# COCKPIT TAB + PRODUCT PERFORMANCE TAB
from funcs import blue_palette, orange_palette, grey_palette


def get_bar_charts_h(month_int, year, df,
                     column_to_group_by,
                     max_bars, bar_charts,
                     palette=palette,
                     column_widths=None,
                     country=None,
                     customer=None,
                     product_group=None,
                     scope=None,
                     ):
    # month_int = 7
    # year = 2011
    # df = df
    # # column_to_group_by = 'Business Line'
    # column_to_group_by = 'Customer'
    # country = None
    # customer = None
    # palette = orange_palette
    # column_widths = None
    # max_bars = 7
    # # bar_charts = ['Total Sales', 'Sales Margin %']
    # bar_charts = ['Total Sales', 'Sales Margin %', 'Total Sales Margin']
    month_name = calendar.month_name[month_int]
    previous_year = year - 1
    # ADD LINES
    '''Total Sales = SUM Total Sales'''
    # NOW
    df_month_now = df[(df['DateTime'].dt.month == month_int) & (df['DateTime'].dt.year == year)].copy()
    if country is not None:
        df_month_now = df_month_now[df_month_now['Country'] == country]

    if product_group is not None:
        df_month_now = df_month_now[df_month_now['Business Line'] == product_group]

    if customer is not None:
        df_month_now = df_month_now[df_month_now['Customer'] == customer]

    total_df_now = df_month_now.groupby([column_to_group_by]).agg(
        {'Total Sales': ['sum'], 'Total Sales Margin': ['sum']}).reset_index()
    total_df_now.columns = [column_to_group_by, 'Total Sales', 'Total Sales Margin']

    '''Sales Margin %  = (SUM Total Sales Margin/ SUM Total Sales)*100'''
    total_df_now['Sales Margin %'] = (total_df_now['Total Sales Margin'] / total_df_now[
        'Total Sales']) * 100 * 100

    total_df_now = total_df_now.sort_values(by='Total Sales', ascending=False).head(max_bars)

    # CALCULATE GREY LINES  - AVG FOR THE PAST 12 MONTH
    from calendar import monthrange
    _, max_days = monthrange(year, month_int - 1)  # not including the current month
    start_date, end_date = f'{previous_year}-{month_int}-01', f'{year}-{month_int - 1}-{max_days}'
    print(start_date, end_date)  # 2010-7-01 2011-6-30
    df_12_m = df[
        df['DateTime'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates

    total_df_12_m = df_12_m.groupby([column_to_group_by]).agg(
        {'Total Sales': ['sum'], 'Total Sales Margin': ['sum']}).reset_index()
    total_df_12_m.columns = [column_to_group_by, 'Total Sales', 'Total Sales Margin']
    total_df_12_m['Sales Margin %'] = (total_df_12_m['Total Sales Margin'] / total_df_12_m['Total Sales']) * 100 * 100
    total_df_12_m['Total Sales'] = total_df_12_m['Total Sales'] / 12
    total_df_12_m['Total Sales Margin'] = total_df_12_m['Total Sales Margin'] / 12

    # JOIN ON THE COMMON COLUMN
    total_df_now = total_df_now.merge(total_df_12_m, on=column_to_group_by, how='left')  # total_df_now =
    total_df_now.columns = [column_to_group_by, 'Total Sales', 'Total Sales Margin', 'Sales Margin %',
                            'Total Sales_avg', 'Total Sales Margin_avg', 'Sales Margin %_avg']

    # COLORING
    # TOTAL SALES
    # print('WE ARE HERE!')
    # print(palette)

    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette) + 1), palette):
        palette2[i] = c
    total_df_now['quantiles_Total Sales'] = pd.cut(total_df_now['Total Sales'], bins=len(palette),
                                                   labels=[key for key in palette2.keys()])
    total_df_now['quantiles_Total Sales'] = total_df_now['quantiles_Total Sales'].map(lambda x: palette2[x])
    palette.reverse()

    # SALES MARGIN %
    total_df_now['quantiles_Sales Margin %'] = pd.cut(total_df_now['Sales Margin %'], bins=len(grey_palette),
                                                      labels=[key for key in grey_palette.keys()])
    total_df_now['quantiles_Sales Margin %'] = total_df_now['quantiles_Sales Margin %'].map(lambda x: grey_palette[x])

    # TOTAL SALES MARGIN
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette) + 1), palette):
        palette2[i] = c
    total_df_now['quantiles_Total Sales Margin'] = pd.cut(total_df_now['Total Sales Margin'], bins=len(palette),
                                                          labels=[key for key in palette2.keys()])
    total_df_now['quantiles_Total Sales Margin'] = total_df_now['quantiles_Total Sales Margin'].map(
        lambda x: palette2[x])
    palette.reverse()

    # BINNING AND MAPPING BY COLOR
    # # TOTAL SALES
    # total_df_now['quantiles_Total Sales'] = pd.cut(total_df_now['Total Sales'], bins=len(palette),
    #                                                labels=[key for key in palette.keys()])
    # total_df_now['quantiles_Total Sales'] = total_df_now['quantiles_Total Sales'].map(lambda x: palette[x])
    #
    # # SALES MARGIN %
    # total_df_now['quantiles_Sales Margin %'] = pd.cut(total_df_now['Sales Margin %'], bins=len(grey_palette),
    #                                                   labels=[key for key in grey_palette.keys()])
    # total_df_now['quantiles_Sales Margin %'] = total_df_now['quantiles_Sales Margin %'].map(lambda x: grey_palette[x])
    #
    # # TOTAL SALES MARGIN
    # total_df_now['quantiles_Total Sales Margin'] = pd.cut(total_df_now['Total Sales Margin'], bins=len(palette),
    #                                                       labels=[key for key in palette.keys()])
    # total_df_now['quantiles_Total Sales Margin'] = total_df_now['quantiles_Total Sales Margin'].map(
    #     lambda x: palette[x])

    # PLOTTING
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=len(bar_charts), start_cell="top-left",
                        # subplot_titles=("TOTAL SALES", "SALES MARGIN %", "TOTAL SALES MARGIN",),
                        column_titles=[f"<b>{chart.upper()}</b>" for chart in bar_charts],
                        # title_font=dict(size=15),
                        column_widths=column_widths,
                        shared_xaxes=False,
                        shared_yaxes=True,  # True?
                        specs=[[{'type': 'bar'} for column in range(len(bar_charts))]],  # 1 list for 1 row
                        # vertical_spacing=2,
                        horizontal_spacing=0.03,  # space between the columns
                        )

    # print('BAR CHARTS:')
    y_names = [name + ' ' for name in total_df_now[column_to_group_by]]
    y_names.reverse()  # update_yaxes - ticktext
    # print(y_names)

    # 1st for loop
    num = 0
    for chart in bar_charts:  # Total Sales, Sales Margin %
        num += 1
        print(f'chart: {chart}, num: {num}')
        # ADDING BARS
        fig.add_trace(
            go.Bar(
                x=total_df_now[chart],
                # y=[name + ' ' for name in total_df_now[column_to_group_by]],
                # y=y_names,
                text=[(f' {value_format(x)}%' if chart == 'Sales Margin %' else f' {currency_sign} {value_format(x)}')
                      for x in total_df_now[chart]],
                # outside value formatting
                textposition='outside',
                # marker_color=products_2010['quantiles'], #bar color
                marker={'color': total_df_now[f'quantiles_{chart}'],
                        'line':
                            {'color': total_df_now[f'quantiles_{chart}'],
                             'width': 1
                             },
                        },
                # hoverinfo='none', # todo - update info
                orientation='h',
                hoverinfo='none',
            ),
            row=1, col=bar_charts.index(chart) + 1,
        )

        # SET GREY LINES
        line_colors = {'Total Sales': '#778899', 'Sales Margin %': '#F89C74', 'Total Sales Margin': '#778899'}
        y_line = [y for y in range(len(total_df_now))]
        y_line.reverse()
        # chart = 'Total Sales Margin'
        print(f'y_line: {y_line}')

        x_line = []
        if chart == 'Total Sales':
            x_line = total_df_now[f'{chart}_avg'].tolist()
            x_line.reverse()
        elif chart == 'Sales Margin %':
            x_line = total_df_now[f'{chart}_avg'].tolist()
            # x_target = [x - x * .1 if int(x) % 2 == 0 else x + x * .2 for x in total_df_now['Sales Margin %']];
            x_line.reverse()
        elif chart == 'Total Sales Margin':
            x_line = total_df_now[f'{chart}_avg'].tolist()
            # x_target = [x - x * .1 if int(x) % 2 == 0 else x + x * .2 for x in total_df_now['Total Sales Margin']];
            x_line.reverse()

        for x, y in zip(x_line, y_line):
            y_start = y - 0.5
            y_end = y + 0.5

            fig.add_shape(type="line",
                          x0=x, y0=y_start,  # start
                          x1=x, y1=y_end,  # end
                          line=dict(color=line_colors[chart], width=1.5),
                          row=1, col=bar_charts.index(chart) + 1,
                          )

        # UPDATE AXES FOR EACH CHART
        coef = {'Total Sales': 0.21, 'Sales Margin %': 0.25, 'Total Sales Margin': 0.2}
        x_max = total_df_now[chart].max() + (total_df_now[chart].max() * coef[chart])
        # print(f'chart: {coef[chart]}')
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            range=[0, x_max],  # [from value, to value]
            title_text=f"<b>{chart}</b><br>Current Period",
            title_font={'color': 'grey',
                        'size': 10,
                        },
            row=1, col=bar_charts.index(chart) + 1,

        )

        fig.update_yaxes(
            categoryorder='total ascending' if chart == 'Total Sales' else None,
            autorange='reversed',
            # autorange='reversed' if chart != 'Total Sales' else None,
            showgrid=False,
            showline=False,
            showticklabels=True if chart == 'Total Sales' else False,

            tickmode='array',
            tickvals=y_line,
            ticktext=y_names,
            row=1, col=bar_charts.index(chart) + 1,
        )

    # 2nd for loop
    # Update Title Font
    for i in fig['layout']['annotations']:
        # print(i)
        i['font'] = dict(size=12,
                         # color='red',
                         )

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=25,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
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


# def get_bar_charts_h(month_int, year, df,
#                      column_to_group_by,
#                      max_bars, bar_charts,
#                      palette=blue_palette,
#                      column_widths=None,
#                      country=None,
#                      customer=None):
#     # month_int = 7
#     # year = 2011
#     # df = df
#     # # column_to_group_by = 'Business Line'
#     # column_to_group_by = 'Customer'
#     # country = None
#     # customer = None
#     # palette = orange_palette
#     # column_widths = None
#     # max_bars = 7
#     # # bar_charts = ['Total Sales', 'Sales Margin %']
#     # bar_charts = ['Total Sales', 'Sales Margin %', 'Total Sales Margin']
#
#     month_name = calendar.month_name[month_int]
#     previous_year = year - 1
#     # ADD LINES
#     '''Total Sales = SUM Total Sales'''
#     # NOW
#     df_month_now = df[(df['DateTime'].dt.month == month_int) & (df['DateTime'].dt.year == year)].copy()
#     if country is not None:
#         df_month_now = df_month_now[df_month_now['Country'] == country]
#
#     if customer is not None:
#         df_month_now = df_month_now[df_month_now['Customer'] == customer]
#
#     total_df_now = df_month_now.groupby([column_to_group_by]).agg(
#         {'Total Sales': ['sum'], 'Total Sales Margin': ['sum']}).reset_index()
#     total_df_now.columns = [column_to_group_by, 'Total Sales', 'Total Sales Margin']
#
#     '''Sales Margin %  = (SUM Total Sales Margin/ SUM Total Sales)*100'''
#     total_df_now['Sales Margin %'] = (total_df_now['Total Sales Margin'] / total_df_now[
#         'Total Sales']) * 100 * 100
#
#     total_df_now = total_df_now.sort_values(by='Total Sales', ascending=False).head(max_bars)
#
#     # CALCULATE GREY LINES  - AVG FOR THE PAST 12 MONTH
#     from calendar import monthrange
#     _, max_days = monthrange(year, month_int - 1)  # not including the current month
#     start_date, end_date = f'{previous_year}-{month_int}-01', f'{year}-{month_int - 1}-{max_days}'
#     print(start_date, end_date)  # 2010-7-01 2011-6-30
#     df_12_m = df[df['DateTime'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates
#
#     total_df_12_m = df_12_m.groupby([column_to_group_by]).agg(
#         {'Total Sales': ['sum'], 'Total Sales Margin': ['sum']}).reset_index()
#     total_df_12_m.columns = [column_to_group_by, 'Total Sales', 'Total Sales Margin']
#     total_df_12_m['Sales Margin %'] = (total_df_12_m['Total Sales Margin'] / total_df_12_m['Total Sales']) * 100 * 100
#     total_df_12_m['Total Sales'] = total_df_12_m['Total Sales'] / 12
#     total_df_12_m['Total Sales Margin'] = total_df_12_m['Total Sales Margin'] / 12
#
#     # JOIN ON THE COMMON COLUMN
#     total_df_now = total_df_now.merge(total_df_12_m, on=column_to_group_by, how='left')  # total_df_now =
#     total_df_now.columns = [column_to_group_by, 'Total Sales', 'Total Sales Margin', 'Sales Margin %',
#                             'Total Sales_avg', 'Total Sales Margin_avg', 'Sales Margin %_avg']
#
#     # BINNING AND MAPPING BY COLOR
#     # TOTAL SALES
#     total_df_now['quantiles_Total Sales'] = pd.cut(total_df_now['Total Sales'], bins=len(palette),
#                                                    labels=[key for key in palette.keys()])
#     total_df_now['quantiles_Total Sales'] = total_df_now['quantiles_Total Sales'].map(lambda x: palette[x])
#
#     # SALES MARGIN %
#     total_df_now['quantiles_Sales Margin %'] = pd.cut(total_df_now['Sales Margin %'], bins=len(grey_palette),
#                                                       labels=[key for key in grey_palette.keys()])
#     total_df_now['quantiles_Sales Margin %'] = total_df_now['quantiles_Sales Margin %'].map(lambda x: grey_palette[x])
#
#     # TOTAL SALES MARGIN
#     total_df_now['quantiles_Total Sales Margin'] = pd.cut(total_df_now['Total Sales Margin'], bins=len(palette),
#                                                           labels=[key for key in palette.keys()])
#     total_df_now['quantiles_Total Sales Margin'] = total_df_now['quantiles_Total Sales Margin'].map(
#         lambda x: palette[x])
#
#     # PLOTTING
#     from plotly.subplots import make_subplots
#
#     fig = make_subplots(rows=1, cols=len(bar_charts), start_cell="top-left",
#                         # subplot_titles=("TOTAL SALES", "SALES MARGIN %", "TOTAL SALES MARGIN",),
#                         column_titles=[f"<b>{chart.upper()}</b>" for chart in bar_charts],
#                         # title_font=dict(size=15),
#                         column_widths=column_widths,
#                         shared_xaxes=False,
#                         shared_yaxes=True,  # True?
#                         specs=[[{'type': 'bar'} for column in range(len(bar_charts))]],  # 1 list for 1 row
#                         # vertical_spacing=2,
#                         horizontal_spacing=0.03,  # space between the columns
#                         )
#
#     # print('BAR CHARTS:')
#     y_names = [name + ' ' for name in total_df_now[column_to_group_by]];
#     y_names.reverse()  # update_yaxes - ticktext
#     # print(y_names)
#
#     # 1st for loop
#     num = 0
#     for chart in bar_charts:  # Total Sales, Sales Margin %
#         num += 1
#         print(f'chart: {chart}, num: {num}')
#         # ADDING BARS
#         fig.add_trace(
#             go.Bar(
#                 x=total_df_now[chart],
#                 # y=[name + ' ' for name in total_df_now[column_to_group_by]],
#                 # y=y_names,
#                 text=[(f' {x:,.1f}%' if chart == 'Sales Margin %' else f' $ {x:,.0f}') for x in total_df_now[chart]],
#                 # outside value formatting
#                 textposition='outside',
#                 # marker_color=products_2010['quantiles'], #bar color
#                 marker={'color': total_df_now[f'quantiles_{chart}'],
#                         'line':
#                             {'color': total_df_now[f'quantiles_{chart}'],
#                              'width': 1
#                              },
#                         },
#                 # hoverinfo='none', # todo - update info
#                 orientation='h',
#                 hoverinfo='none',
#             ),
#             row=1, col=bar_charts.index(chart) + 1,
#         )
#
#         # SET GREY LINES
#         line_colors = {'Total Sales': '#778899', 'Sales Margin %': '#F89C74', 'Total Sales Margin': '#778899'}
#         y_line = [y for y in range(len(total_df_now))]
#         y_line.reverse()
#         # chart = 'Total Sales Margin'
#         print(f'y_line: {y_line}')
#
#         x_line = []
#         if chart == 'Total Sales':
#             x_line = total_df_now[f'{chart}_avg'].tolist()
#             x_line.reverse()
#         elif chart == 'Sales Margin %':
#             x_line = total_df_now[f'{chart}_avg'].tolist()
#             # x_target = [x - x * .1 if int(x) % 2 == 0 else x + x * .2 for x in total_df_now['Sales Margin %']];
#             x_line.reverse()
#         elif chart == 'Total Sales Margin':
#             x_line = total_df_now[f'{chart}_avg'].tolist()
#             # x_target = [x - x * .1 if int(x) % 2 == 0 else x + x * .2 for x in total_df_now['Total Sales Margin']];
#             x_line.reverse()
#
#         for x, y in zip(x_line, y_line):
#             y_start = y - 0.5
#             y_end = y + 0.5
#
#             fig.add_shape(type="line",
#                           x0=x, y0=y_start,  # start
#                           x1=x, y1=y_end,  # end
#                           line=dict(color=line_colors[chart], width=1.5),
#                           row=1, col=bar_charts.index(chart) + 1,
#                           )
#
#         # UPDATE AXES FOR EACH CHART
#         coef = {'Total Sales': 0.21, 'Sales Margin %': 0.25, 'Total Sales Margin': 0.2}
#         x_max = total_df_now[chart].max() + (total_df_now[chart].max() * coef[chart])
#         # print(f'chart: {coef[chart]}')
#         fig.update_xaxes(
#             zeroline=False,
#             showline=False,
#             showgrid=False,
#             showticklabels=False,
#             range=[0, x_max],  # [from value, to value]
#             title_text=f"<b>{chart}</b><br>Current Period",
#             title_font={'color': 'grey',
#                         'size': 10,
#                         },
#             row=1, col=bar_charts.index(chart) + 1,
#
#         )
#
#         fig.update_yaxes(
#             categoryorder='total ascending' if chart == 'Total Sales' else None,
#             autorange='reversed',
#             # autorange='reversed' if chart != 'Total Sales' else None,
#             showgrid=False,
#             showline=False,
#             showticklabels=True if chart == 'Total Sales' else False,
#
#             tickmode='array',
#             tickvals=y_line,
#             ticktext=y_names,
#             row=1, col=bar_charts.index(chart) + 1,
#         )
#
#     # 2nd for loop
#     # Update Title Font
#     for i in fig['layout']['annotations']:
#         # print(i)
#         i['font'] = dict(size=12,
#                          # color='red',
#                          )
#
#     # UPDATE LAYOUT
#     fig.update_layout(
#         paper_bgcolor='rgb(255,255,255)',  # white
#         plot_bgcolor='rgb(255,255,255)',  # white
#         showlegend=False,
#         margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
#                     r=0,
#                     b=0,
#                     t=25,
#                     #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
#                     ),
#     )
#     # SET FONT
#     fig.update_layout(autosize=True,
#                       font={
#                           'family': font_family,
#                           # 'color': 'black',
#                           # 'size': 12
#                       },
#     )
#
#     return fig


def total_sales_per_country(df,
                            kpi,
                            palette=palette,
                            dates=None,
                            state=None,
                            store=None,
                            product=None):
    # CURRENCY KPIs
    dollar_kpis = ['Total Sales',
                   'Sales per Customer',
                   'Average Inventory Amount',
                   'Total On-hand Amount',
                   'Average Selling Price',
                   'Average On-hand Price',
                   ]

    # FILTERS
    # TO-DO: more options for dates
    #print(df.columns)
    if store:
         df = df[df['Customer'] == store]
    if product:
         df = df[df['Business Line'] == product]
    if state:
         df = df[df['Country'] == state]

    if dates:
    # last n months
        if dates.split()[0] == 'last' and dates.split()[2] == 'months':
            n = int(dates.split()[1])
            start = df['DateTime'].max() - pd.DateOffset(months=n)
            df = df[df['DateTime'] >= start]
        # last n years
        if dates.split()[0] == 'last' and dates.split()[2] == 'years':
            n = int(dates.split()[1])
            df = df[df['Current Year'] > (df['Current Year'].max() - n)]
    # DATA
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
            text=[(f' {currency_sign} {value_format(x)}   <i>{value_format(y)}%<i>') if kpi in dollar_kpis else (
                f' {value_format(x)}   <i>{value_format(y)}%<i>') for x, y in zip(df_country[kpi], df_country[calc])],
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

import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, augment_days, get_palette, grey_palette, value_format, get_currency_sign

currency_sign = get_currency_sign()
palette = get_palette()

def get_performace_by_brand_h(month_int, year, df,
                              column_to_group_by,
                              max_bars, bar_charts,
                              store=None,
                              brand=None,
                              product=None,
                              state=None,
                              palette_1=palette,
                              palette_2=grey_palette,
                              palette_3=palette,
                              column_widths=None,
                              ):
    # params
    # month_int = 12
    # year = 2020
    # df = df

    if store:
        df = df[df['Store'] == store]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]
    if state:
        df = df[df['City'] == state]

    column_to_group_by = 'Brand'
    max_bars = 10
    bar_charts = ['Total Sales', 'Sales per Store', 'Average Inventory Amount', 'Total On-Hand Amount',
                  'Inventory Turns', 'Days Sales of Inventory', 'Nb of Stores', 'Nb of New Stores',
                  'Nb of Products', 'Average Selling Price']
    column_widths = None

    month_name = calendar.month_name[month_int]
    previous_year = year - 1

    from calendar import monthrange
    _, max_days_now = monthrange(year, month_int)

    # NOW
    df_month_now = df[(df['Date'].dt.month == month_int) & (df['Date'].dt.year == year)].copy()
    '''Nb of Stores = store_state'''
    df_month_now['store_state'] = df_month_now[['Store', 'City']].agg(' '.join, axis=1)
    '''Total Sales = SUM Total Sales'''
    '''Total On-Hand Amount = SUM Total On-Hand Amount'''
    '''Average Selling Price = Average Selling Price OR Total Sales / Total Sales Units'''
    total_df_now = df_month_now.groupby([column_to_group_by]).agg({'Total Sales': ['sum'],
                                                                   'store_state': ['nunique'],
                                                                   # 'Average Inventory Amount': ['sum'],
                                                                   'Total On-Hand Amount': ['sum'],
                                                                   'Average Selling Price': ['sum'],
                                                                   'Product': ['nunique'],

                                                                   }).reset_index()
    total_df_now.columns = [column_to_group_by, 'Total Sales', 'Nb of Stores',
                            # 'Average Inventory Amount',
                            'Total On-Hand Amount', 'Average Selling Price', 'Nb of Products']

    '''Sales per Store = Total Sales/ Stores'''  # 'Store': ['count'] - count unique stores for selected period
    total_df_now['Sales per Store'] = (total_df_now['Total Sales'] / total_df_now['Nb of Stores']).round(1)

    '''Inventory Turns = (Total Sales  * 365) / Total On-Hand Amount over the period'''
    total_df_now['Total Sales x365'] = total_df_now['Total Sales'] * 365
    total_df_now['Inventory Turns'] = (total_df_now['Total Sales x365'] / total_df_now['Total On-Hand Amount']).round(2)

    '''Days Sales of Inventory' = Total On-Hand Amount over the period / Total Sales'''
    total_df_now['Days Sales of Inventory'] = (
            total_df_now['Total On-Hand Amount'] / total_df_now['Total Sales']).round(1)

    '''Average Inventory Amount = Total On-Hand Amount /Number of Dates)'''
    total_df_now['Average Inventory Amount'] = total_df_now['Total On-Hand Amount'] / max_days_now

    '''Nb of New Stores - YTD'''
    from calendar import monthrange

    _, max_days_current = monthrange(year, month_int)
    start_month = 1  # Jan
    start_date, end_date = f'{year}-{start_month}-01', f'{year}-{month_int}-{max_days_current}'
    df_ytd = df[df['Date'].between(start_date, end_date, inclusive=True)].copy()  # Jan -> Selected Month
    df_ytd['store_state'] = df_ytd[['Store', 'City']].agg(' '.join, axis=1)
    df_min_date = df_ytd.groupby(['Store', 'City']).Date.min().reset_index()
    new_stores_groupby = df_min_date.groupby(pd.Grouper(key='Date', freq='1M'))['Store'].nunique().reset_index()

    if month_int not in new_stores_groupby['Date'].dt.month:
        # append a missing row
        one_row = pd.DataFrame([[end_date, 0]], columns=new_stores_groupby.columns)
        one_row['Date'] = pd.to_datetime(one_row['Date'], infer_datetime_format=True)
        new_stores_groupby = new_stores_groupby.append(one_row, ignore_index=True)

    new_stores_now = int(new_stores_groupby.iloc[-1]['Store'])  # 0, 1, 10
    new_stores_lst = [new_stores_now for i in range(len(total_df_now))]
    total_df_now['Nb of New Stores'] = new_stores_lst
    # Check
    # df_month_now[df_month_now['Brand']=='Brand_1']
    total_df_now = total_df_now.sort_values(by='Total Sales', ascending=False).head(max_bars)

    # CALCULATE GREY LINES  - AVG FOR THE PAST 12 MONTH
    from calendar import monthrange

    _, max_days = monthrange(year, month_int - 1)
    start_date, end_date = f'{previous_year}-{month_int}-01', f'{year}-{month_int - 1}-{max_days}'
    print(start_date, end_date)  # 2019-12-01 2020-11-30 # not including the selected month
    df_12_m = df[df['Date'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates
    df_12_m['store_state'] = df_12_m[['Store', 'City']].agg(' '.join, axis=1)

    total_df_12_m = df_12_m.groupby([column_to_group_by]).agg({'Total Sales': ['sum'],
                                                               'store_state': ['nunique'],
                                                               # 'Average Inventory Amount': ['sum'],
                                                               'Total On-Hand Amount': ['sum'],
                                                               'Average Selling Price': ['sum'],
                                                               }).reset_index()
    total_df_12_m.columns = [column_to_group_by, 'Total Sales', 'Store',
                             #  'Average Inventory Amount',
                             'Total On-Hand Amount', 'Average Selling Price']
    '''Sales per Store = Total Sales/ Stores'''  # 'Store': ['count'] - count unique stores for selected period
    total_df_12_m['Sales per Store'] = (total_df_12_m['Total Sales'] / total_df_12_m['Store']).round(1)
    '''Inventory Turns = (Total Sales  * 365) / Total On-Hand Amount over the period'''
    total_df_12_m['Total Sales x365'] = total_df_12_m['Total Sales'] * 365
    total_df_12_m['Inventory Turns'] = (
            total_df_12_m['Total Sales x365'] / total_df_12_m['Total On-Hand Amount']).round(2)
    '''Days Sales of Inventory' = Total On-Hand Amount over the period / Total Sales'''
    total_df_12_m['Days Sales of Inventory'] = (
            total_df_12_m['Total On-Hand Amount'] / total_df_12_m['Total Sales']).round(
        1)
    total_df_12_m.drop(['Store', 'Total Sales x365'], axis=1, inplace=True)

    '''Average Inventory Amount = Total On-Hand Amount /Number of Dates)'''
    total_df_12_m['Average Inventory Amount'] = total_df_12_m['Total On-Hand Amount'] / 365
    # check
    # df_12_m[df_12_m['Brand'] == 'Brand_0']

    # CALCULATE AVG
    for column in total_df_12_m.columns:
        if column not in ['Brand', 'Average Inventory Amount']:
            # Total Sales, Sales per Store, 'Average Inventory Amount', 'Total On-Hand Amount', Inventory Turns, Days Sales of Inventory', Average Selling Price
            total_df_12_m[column] = (total_df_12_m[column] / 12).round(1)

    # JOIN ON THE COMMON COLUMN AND RENAME
    total_df_now = total_df_now.merge(total_df_12_m, on=column_to_group_by, how='left')  # total_df_now =
    for column in total_df_now.columns:
        if '_x' in column:
            total_df_now.rename({column: column[:-2]}, axis='columns', inplace=True)
        if '_y' in column:
            total_df_now.rename({column: column[:-2] + '_avg'}, axis='columns', inplace=True)

    # BINNING AND MAPPING BY COLOR
    # SET COLOR BY CHART
    color_palettes = {'Total Sales': palette_1, 'Sales per Store': palette_1,  # orange
                      'Average Inventory Amount': palette_2, 'Total On-Hand Amount': palette_2,  # grey
                      'Inventory Turns': palette_3, 'Days Sales of Inventory': palette_3,  # blue
                      'Nb of Stores': palette_2, 'Nb of New Stores': palette_2,  # grey
                      'Nb of Products': palette_2, 'Average Selling Price': palette_3}  # grey, blue

    # 1st loop
    for chart in bar_charts:
        palette = color_palettes[chart]
        total_df_now[f'quantiles_{chart}'] = pd.cut(total_df_now[chart], bins=len(palette),
                                                    labels=[key for key in palette.keys()])
        total_df_now[f'quantiles_{chart}'] = total_df_now[f'quantiles_{chart}'].map(lambda x: palette[x])

    # total_df_now['quantiles_Total Sales'] = pd.cut(total_df_now['Total Sales'], bins=len(palette_1),  # orange
    #                                                 labels=[key for key in palette_1.keys()])
    # total_df_now['quantiles_Total Sales'] = total_df_now['quantiles_Total Sales'].map(lambda x: palette_1[x])

    # PLOTTING
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=len(bar_charts), start_cell="top-left",
                        # todl - add column titles
                        # subplot_titles=("SALES", "INVENTORY", "STORES", "PRODUCTS",),
                        # column_titles=("SALES", "INVENTORY", "STORES", "PRODUCTS"),
                        # title_font=dict(size=15),
                        column_widths=column_widths,
                        shared_xaxes=False,
                        shared_yaxes=True,  # True?
                        specs=[[{'type': 'bar'} for column in range(len(bar_charts))]],  # 1 list for 1 row
                        # vertical_spacing=2,
                        horizontal_spacing=0.01,  # space between the columns
                        )

    # print('BAR CHARTS:')
    y_names = [name + '    ' for name in total_df_now[column_to_group_by]]  # Brand Names
    y_line = [y for y in range(len(total_df_now))]  # list of integres - 1, 2, 3, 4, 5

    # 2nd loop
    for chart in bar_charts:
        # ADDING BARS
        bar_text = [(f' {currency_sign} {value_format(x)}') for x in total_df_now[chart]]
        if chart == 'Inventory Turns':
            bar_text = [(f' 🔄 {value_format(x)}') for x in total_df_now[chart]]
        elif chart == 'Days Sales of Inventory':
            bar_text = [(f' 🕜 {value_format(x)} d') for x in total_df_now[chart]]
        elif chart in ['Nb of Stores', 'Nb of New Stores']:
            bar_text = [(f'   🏠 {value_format(x)}') for x in total_df_now[chart]]
        elif chart == 'Nb of Products':
            bar_text = [(f'      {value_format(x)}') for x in total_df_now[chart]]

        fig.add_trace(
            go.Bar(
                x=total_df_now[chart],
                # y=[name + ' ' for name in total_df_now[column_to_group_by]],
                # y=y_names,
                # text=[(f' {x:,.1f}%' if chart == 'Sales Margin %' else f' $ {x:,.0f}') for x in total_df_now[chart]],
                text=bar_text,
                # outside value formatting
                textposition='auto',
                # marker_color=products_2010['quantiles'], #bar color
                marker={'color': total_df_now[f'quantiles_{chart}'],
                        'line':
                            {'color': total_df_now[f'quantiles_{chart}'],
                             'width': 1,
                             },
                        },
                orientation='h',
                hoverinfo='none',
            ),
            row=1, col=bar_charts.index(chart) + 1,
        )

        # SET GREY LINES
        if chart not in ['Nb of Stores', 'Nb of New Stores',
                         'Nb of Products']:  # set grey lines for all bar chart except for these
            grey_line = '#778899'
            orange_line = '#F89C74'

            line_colors = {'Total Sales': grey_line, 'Sales per Store': grey_line,
                           'Average Inventory Amount': orange_line, 'Total On-Hand Amount': orange_line,
                           'Inventory Turns': grey_line, 'Days Sales of Inventory': grey_line,
                           'Average Selling Price': grey_line}

            # line_colors = {'Total Sales': '#778899', 'Sales Margin %': , 'Total Sales Margin': '#778899'}
            y_line = [y for y in range(len(total_df_now))]  # list of integres - 1, 2, 3, 4, 5
            x_line = total_df_now[f'{chart}_avg']
            # print(y_line, x_line)

            for x, y in zip(x_line, y_line):
                y_start = y - 0.5
                y_end = y + 0.5

                fig.add_shape(type="line",
                              x0=x, y0=y_start,  # start
                              x1=x, y1=y_end,  # end
                              line=dict(color=line_colors[chart], width=1.5),
                              row=1, col=bar_charts.index(chart) + 1,
                              )
        # check
        # total_df_now[['Brand', 'Average Selling Price', 'Average Selling Price_avg']]

        # UPDATE AXES FOR EACH CHART
        coef = {'Total Sales': 0.1, 'Sales per Store': 0.1, 'Average Inventory Amount': 0.1,
                'Total On-Hand Amount': 0.1,
                'Inventory Turns': 0.1, 'Days Sales of Inventory': 0.1, 'Nb of Stores': 0.1, 'Nb of New Stores': 0.1,
                'Nb of Products': 0.1,
                'Average Selling Price': 0.1}
        x_max = total_df_now[chart].max() + (total_df_now[chart].max() * coef[chart])
        # print(f'chart: {coef[chart]}')
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            range=[0, x_max],  # [from value, to value]
            title_text=f"<b>{chart}</b>",
            title_font={'color': 'grey',
                        'size': 11,
                        },
            row=1, col=bar_charts.index(chart) + 1,
        )

        fig.update_yaxes(
            categoryorder='total ascending',
            autorange='reversed',
            showgrid=False,
            showline=False,
            showticklabels=True if chart == 'Total Sales' else False,

            tickmode='array',
            tickvals=y_line,
            ticktext=y_names,
            row=1, col=bar_charts.index(chart) + 1,
        )


    # 3d loop -> Update Title Font
    for i in fig['layout']['annotations']:
        # print(i)
        i['font'] = dict(size=12,
                         # color='red',
                         )

    # UPDATE LAYOUT
    fig.update_layout(
        # FIGURE MAIN TITLE
        title=dict(text='SALES ' + 180*' ' + ' INVENTORY '
                        + 170*' '+' STORES '
                        + 85*' ' + ' PRODUCTS ',
                   font=dict(size=14,
                             color='grey',
                             ),
                   # alignment
                   x=0.12, y=1,
                   xref="container", yref="container",
                   # xanchor='center', yanchor='top'
                   ),
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        autosize=True,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=25,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
    )
    # GLOBAL FONT SETINGS
    fig.update_layout(autosize=True,
                      font={
                          'family': font_family,
                          # 'color': 'green',
                          # 'size': 12
                      },
                      )

    return fig








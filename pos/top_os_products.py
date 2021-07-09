import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, augment_days, orange_palette, augment_days_3_m, value_format, \
    get_currency_sign, diverging_palette

currency_sign = get_currency_sign()


def get_top_os_products(month_int, year, df,
                        column_to_group_by,  # Product
                        state=None,
                        store=None,
                        brand=None,
                        product=None,
                        max_bars=10):
    # params
    # month_int = 12
    # year = 2020
    # df = df
    # max_bars = 10
    # column_to_group_by = 'Product'
    if store:
        df = df[df['Store'] == store]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]
    if state:
        df = df[df['State'] == state]

    df_month_now = df[(df['Date'].dt.month == month_int) & (df['Date'].dt.year == year)].copy()

    # FIND OUT-OF-STOCK - number of stores
    os_products = df_month_now[df_month_now['Total On-Hand Units'] == 0]
    grouped_by_os = os_products.groupby([column_to_group_by]).agg({'Store': ['count'], 'Total Sales': [
        'sum']}).reset_index()  # the number of stores where the product is out-of-stock
    grouped_by_os.columns = ['Product', 'Out-of-Stock Stores', 'Sales Losses']  # SALES LOSSES

    # FIND IN-STOCK PRODUCTS - number of stores
    is_products = df_month_now[df_month_now['Total On-Hand Units'] > 0]
    grouped_by_is = is_products.groupby([column_to_group_by]).agg({'Store': ['count'],
                                                                   #  'Total Sales': ['sum']
                                                                   }).reset_index()
    grouped_by_is.columns = ['Product', 'In-Stock Stores',
                             #  'IS Total Sales'
                             ]

    totals_sales_by_product = df_month_now.groupby([column_to_group_by]).agg(
        {'Total Sales': ['sum']}).reset_index()
    totals_sales_by_product.columns = ['Product', 'Total Sales']

    # MERGE DFs on common values
    merged_os = pd.merge(grouped_by_os, grouped_by_is, how='inner', on=['Product'])

    merged_os = pd.merge(merged_os, totals_sales_by_product, how='inner', on=['Product'])
    merged_os = merged_os.sort_values(by='Sales Losses', ascending=False).reset_index(drop=True).head(max_bars)

    # SET RANGE - 3M
    end_year = year
    end_month = month_int
    if end_month > 2:  # ! including the current month !
        start_month = month_int - 2
        start_year = year
    else:  # start_month falls on PREVIOUS YEAR
        month_dict = {0: 12, -1: 11}
        start_month = month_int - 2
        start_month = month_dict[start_month]
        start_year = year - 1

    from calendar import monthrange
    _, max_days = monthrange(year, end_month)
    start_date, end_date = f'{start_year}-{start_month}-01', f'{end_year}-{end_month}-{max_days}'
    # print(start_date, end_date)  # 2020-3-01 2020-5-31
    df_3_m = df[df['Date'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates

    date_str = calendar.month_abbr[end_month] + '-' + str(end_year)
    bar_charts = ['OUT-OF-STOCKS ' + date_str, 'TOTAL SALES', 'ESTIMATED SALES LOSSES', 'SALES & OUT-OF-STOCKS']
    grouped_df = merged_os

    # PLOTTING
    # PREP THE PLOT LAYOUT
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=len(grouped_df), cols=4, start_cell="top-left",
                        # subplot_titles=("TOTAL SALES", "SALES MARGIN %", "TOTAL SALES MARGIN",),
                        column_titles=[f"<b>{chart}</b>" for chart in bar_charts],
                        shared_xaxes=True,  # ! step-like bars
                        shared_yaxes=False,
                        # vertical_spacing=2,
                        horizontal_spacing=0.03,  # space between the columns
                        )

    color = 'crimson'

    for i in range(len(grouped_df)):  # fetch row by index
        # CALCULATE
        row = grouped_df.iloc[i]
        # print(row)

        product = row[column_to_group_by]
        os_stores = row['Out-of-Stock Stores']
        is_stores = row['In-Stock Stores']
        total_sales = row['Total Sales']
        sales_losses = row['Sales Losses']

        # OUT OF STOCK & # IN-STOCK
        fig.add_trace(
            go.Bar(
                x=[os_stores],  # 1 val
                y=[f'{product} ' + 20 * ' '],  # same as is
                text=f' {value_format(os_stores)}',
                # outside value formatting
                textposition='outside',
                marker={'color': color,
                        'line':
                            {'color': color,
                             'width': 1
                             },
                        },
                orientation='h',
                hoverinfo='none',
                hovertemplate='Out-of-Stock Stores',
            ),
            row=i + 1,
            col=1,
        )

        fig.add_trace(
            go.Bar(
                x=[is_stores],  # 1 val
                y=[f'{product} ' + 20 * ' '],  # same as os
                text=f' {value_format(is_stores)}',
                # outside value formatting
                textposition='outside',
                marker={'color': 'grey',
                        'line':
                            {'color': 'grey',
                             'width': 1
                             },
                        },
                orientation='h',
                hoverinfo='none',
                hovertemplate='In-stock Stores',
            ),
            row=i + 1,
            col=1,
        )

        # TOTAL SALES
        fig.add_trace(
            go.Bar(
                x=[total_sales],  # 1 val
                # y=[f' $ {total_sales} ' + 20*' '],  # 1 val
                text=f'{currency_sign}{value_format(total_sales)}',
                # outside value formatting
                textposition='outside',
                marker={'color': 'royalblue',
                        'line':
                            {'color': 'royalblue',
                             'width': 1
                             },
                        },
                orientation='h',
                hoverinfo='none',
            ),
            row=i + 1,
            col=2,
        )

        # ESTIMATED SALES LOSSES
        fig.add_trace(
            go.Bar(
                x=[sales_losses],  # 1 val
                # y=[f' $ {sales_losses} ' + 20*' '],  # 1 val
                text=f' {currency_sign}{value_format(sales_losses)}',
                # outside value formatting
                textposition='outside',
                marker={'color': 'crimson',
                        'line':
                            {'color': 'crimson',
                             'width': 1
                             },
                        },
                orientation='h',
                hoverinfo='none',
            ),
            row=i + 1,
            col=3,
        )

        # SALES & OUT-OF-STOCKS
        # 1 PRODUCT AT A TIME
        # print(product)
        df_product = df_3_m[df_3_m['Product'] == product].copy()
        augmented_df = augment_days_3_m(start_date, end_date, df_product)

        fig.add_trace(
            go.Scatter(x=augmented_df['Date'],
                       y=[y if y != -1 else 0 for y in augmented_df['Total Sales']],  # actual value else 0
                       mode='lines',
                       fill='tozeroy',
                       hovertemplate='<extra></extra>',
                       line_color='darkgray',
                       ),
            row=i + 1,
            col=4,
        )

        bar_height = df_product['Total Sales'].mean()  # fixed for each out-of-stock product bar
        fig.add_trace(
            go.Bar(
                x=augmented_df['Date'],
                y=[bar_height if y == 0 else 0 for y in augmented_df['Total On-Hand Units']],
                # 1 if out-of-stock else 0
                text=['1' if y == 0 else ' ' for y in augmented_df['Total On-Hand Units']],
                textfont=dict(color="crimson"),
                textposition='outside',
                marker={'color': 'crimson',
                        'line':
                            {'color': 'crimson',
                             'width': 1
                             },
                        },
                hoverinfo='none',
            ),
            row=i + 1,
            col=4,
        )
        # break

    # UPDATE AXES FOR EACH CHART
    for i in range(len(grouped_df)):
        # OUT OF STOCK & # IN-STOCK
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            # only for the last bar
            title_text=f"<b>Nb of Out-of-Stocks vs Total Nb of inventory positions</b><br>{date_str}" if (
                    i == len(grouped_df) - 1) else None,
            title_font={'color': 'grey',
                        'size': 10,
                        },
            range=[0, 1.35*max(grouped_df['Out-of-Stock Stores'].max(), grouped_df['In-Stock Stores'].max())],
            row=i + 1, col=1,

        )

        fig.update_yaxes(
            showgrid=False,
            showline=False,
            showticklabels=True,
            # tickmode='array',
            # tickvals=y_line,
            # ticktext=y_names,
            row=i + 1, col=1,
        )

        # TOTAL SALES
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            title_text=f"<b>Total Sales</b><br>{date_str}" if (i == len(grouped_df) - 1) else None,
            # only for the last bar
            title_font={'color': 'grey',
                        'size': 10,
                        },
            range=[0, 1.35 * grouped_df['Total Sales'].max()],
            row=i + 1, col=2,

        )
        fig.update_yaxes(
            showgrid=False,
            showline=False,
            showticklabels=False,

            # tickmode='array',
            # tickvals=y_line,
            # ticktext=y_names,
            row=i + 1, col=2,
        )

        # ESTIMATED SALES LOSSES
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            title_text=f"<b>Estimated Sales Losses {currency_sign}</b><br>{date_str}" if (
                        i == len(grouped_df) - 1) else None,
            # only for the last bar
            title_font={'color': 'grey',
                        'size': 10,
                        },
            range=[0, 1.35 * grouped_df['Sales Losses'].max()],
            row=i + 1, col=3,

        )
        fig.update_yaxes(
            showgrid=False,
            showline=False,
            showticklabels=False,

            # tickmode='array',
            # tickvals=y_line,
            # ticktext=y_names,
            row=i + 1, col=3,
        )

        # SALES & OUT-OF-STOCKS
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            title_text=f"<b>Totals Sales & Nb of Out-of-Stocks</b><br>Last 3 months" if (
                    i == len(grouped_df) - 1) else None,
            # only for the last bar
            title_font={'color': 'grey',
                        'size': 10,
                        },
            row=i + 1, col=4,

        )
        fig.update_yaxes(
            showgrid=False,
            showline=False,
            showticklabels=False,

            # tickmode='array',
            # tickvals=y_line,
            # ticktext=y_names,
            row=i + 1, col=4,
        )
        # break

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        margin=dict(l=0,  #
                    r=0,
                    b=0,
                    t=25,
                    ),
        # barmode='stack', # overlay
        bargroupgap=0.1  # 1st col gap

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

# check
# df_product = df_3_m[df_3_m['Product']=='Product_35'].copy()

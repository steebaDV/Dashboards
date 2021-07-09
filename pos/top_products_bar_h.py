
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

currency_sign = get_currency_sign()
palette = get_palette()


def get_top_products_bar_h(month_int, year, df, column_to_group_by,
                           state=None,
                           store=None,
                           product=None,
                           brand=None,
                           palette=palette):
    # month_int = 12
    # year = 2020
    # df = df
    # column_to_group_by = 'Product'
    # state = None
    # store = None
    # palette = orange_palette

    if store:
        df = df[df['Store'] == store]
    if brand:
        df = df[df['Brand'] == brand]
    if product:
        df = df[df['Product'] == product]
    if state:
        df = df[df['City'] == state]

    month_name = calendar.month_name[month_int]
    previous_year = year - 1

    # NOW
    df_month_now = df[(df['Date'].dt.month == month_int) & (df['Date'].dt.year == year)].copy()
    if state is not None:
        df_month_now = df_month_now[df_month_now['City'] == state]

    if store is not None:
        df_month_now = df_month_now[df_month_now['Store'] == store]
    # len(df_month_now) # 36 for Dec 2020

    total_df_now = df_month_now.groupby([column_to_group_by]).agg({'Total Sales': ['sum']}).reset_index()
    total_df_now.columns = [column_to_group_by, 'Total Sales']
    total_df_now = total_df_now.sort_values(by='Total Sales', ascending=False).head(10)

    # CALCULATE GREY LINES  - AVG FOR THE PAST 12 MONTH
    from calendar import monthrange
    _, max_days = monthrange(year, month_int - 1)  # not including the current month
    start_date, end_date = f'{previous_year}-{month_int}-01', f'{year}-{month_int - 1}-{max_days}' # 12 months
    # print(start_date, end_date)
    df_12_m = df[df['Date'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates
    total_df_12_m = df_12_m.groupby([column_to_group_by]).agg({'Total Sales': ['sum']}).reset_index()
    total_df_12_m.columns = [column_to_group_by, 'Total Sales']
    total_df_12_m['Total Sales'] = total_df_12_m['Total Sales'] / 12

    # # JOIN ON THE COMMON COLUMN
    total_df_now = total_df_now.merge(total_df_12_m, on=column_to_group_by, how='left')  # total_df_now =
    total_df_now.columns = [column_to_group_by, 'Total Sales', 'Total Sales_avg']

    # BINNING AND MAPPING BY COLOR
    total_df_now['quantiles_Total Sales'] = pd.cut(total_df_now['Total Sales'], bins=len(palette),
                                                    labels=[key for key in palette.keys()])
    total_df_now['quantiles_Total Sales'] = total_df_now['quantiles_Total Sales'].map(lambda x: palette[x])

    # PLOTTING
    from plotly.subplots import make_subplots
    fig = go.Figure()

    y_names = [product + ' ' for product in total_df_now[column_to_group_by]];
    # y_names.reverse()  # update_yaxes - ticktext

    # TOP 10 PRODUCTS BY SALES
    fig.add_trace(
              go.Bar(
                  x=total_df_now['Total Sales'],
                  # y=[name + ' ' for name in total_df_now[column_to_group_by]],
                  # y=y_names,
                  text=[f' {currency_sign} {value_format(x)}' for x in total_df_now['Total Sales']],
                  # outside value formatting
                  textposition='auto',
                  marker={'color': total_df_now[f'quantiles_Total Sales'],
                          'line':
                              {'color': total_df_now[f'quantiles_Total Sales'],
                                'width': 1
                                },
                          },
                  orientation='h',
                  hoverinfo='none',
              )
          )

    line_color = '#778899'
    y_line = [y for y in range(len(total_df_now))]
    # y_line.reverse()
    # chart = 'Total Sales Margin'
    print(f'y_line: {y_line}')


    x_line = total_df_now[f'Total Sales_avg'].tolist()
    # x_line.reverse()

    for x, y in zip(x_line, y_line):
        y_start = y - 0.5
        y_end = y + 0.5

        fig.add_shape(type="line",
                      x0=x, y0=y_start,  # start
                      x1=x, y1=y_end,  # end
                      line=dict(color=line_color, width=1.5),
                      )

    # UPDATE AXES FOR EACH CHART
    x_max = total_df_now['Total Sales'].max() + (total_df_now['Total Sales'].max() * 0.21)

    fig.update_xaxes(
        zeroline=False,
        showline=False,
        showgrid=False,
        showticklabels=False,
        range=[0, x_max],  # [from value, to value]
        # title_text=f"<b>{chart}</b><br>Current Period",
        # title_font={'color': 'grey',
        #             'size': 10,
        #             },
        # row=1, col=bar_charts.index(chart) + 1,

    )

    fig.update_yaxes(
        categoryorder='total ascending', #if chart == 'Total Sales' else None,
        autorange='reversed',
        # autorange='reversed' if chart != 'Total Sales' else None,
        showgrid=False,
        showline=False,
        showticklabels=True, #True if chart == 'Total Sales' else False,

        tickmode='array',
        tickvals=y_line,
        ticktext=y_names,
    )


    for i in fig['layout']['annotations']:
        i['font'] = dict(size=12,
                          # color='red',
                          )

    # UPDATE LAYOUT
    fig.update_layout(
        title=dict(text='Top Products',
                       font=dict(size=13,
                                 color='grey',
                                 ),
                       # alignment
                       x=0, y=1,
                       ),
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=25,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        # width=800,
        # height=500,
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



# Check
# df_12_m[df_12_m['Product']=='Product_3']['Total Sales'].sum()
# df_month_now[df_month_now['Product']=='Product_3']['Total Sales'].sum()








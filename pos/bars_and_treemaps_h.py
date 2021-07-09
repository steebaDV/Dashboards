import pandas as pd
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
from plotly import graph_objects as go
import calendar
import numpy as np
from funcs import font_family, augment_days, get_palette, get_currency_sign, value_format

currency_sign = get_currency_sign()
palette = get_palette()


def get_bars_and_treemaps_h(month_int, year, df,
                            column_to_group_by,
                            bar_charts, trees_column,
                            state=None,
                            store=None,
                            brand=None,
                            product=None,
                            palette=palette, max_bars=8,
                            ):
    # params
    # month_int = 12
    # year = 2020
    # df = df
    # max_bars = 8
    # # Brand, Product
    # column_to_group_by = 'Brand'
    # trees_column = 'Product'
    # bar_charts = ['Total Sales', 'Total Sales by Product']
    # palette = orange_palette
    # # Store, Brand
    # column_to_group_by = 'Store'
    # trees_column = 'Brand'
    # bar_charts = ['Total Sales', 'Total Sales by Brand']
    # palette = blue_palette

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

    grouped_df = df_month_now.groupby([column_to_group_by]).agg({'Total Sales': ['sum']}).reset_index()
    grouped_df.columns = [column_to_group_by, 'Total Sales']
    grouped_df = grouped_df.sort_values(by='Total Sales', ascending=False).head(max_bars).reset_index(
        drop=True)  # sort and enumerate

    # BINNING AND COLOR
    grouped_df['color'] = pd.cut(grouped_df['Total Sales'], bins=len(palette),
                                 labels=[key for key in palette.keys()])
    grouped_df['color'] = grouped_df['color'].map(lambda x: palette[x])

    # PREP THE PLOT LAYOUT
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=len(grouped_df), cols=2, start_cell="top-left",
                        # subplot_titles=("TOTAL SALES", "SALES MARGIN %", "TOTAL SALES MARGIN",),
                        column_titles=[f"<b>{chart.upper()}</b>" for chart in bar_charts],
                        # title_font=dict(size=15),
                        column_widths=[0.35, 0.75],  # bars, treemaps
                        shared_xaxes=True,  # ! important - bars order
                        shared_yaxes=True,
                        specs=[[{'type': 'bar'}, {'type': 'domain'}] for i in range(len(grouped_df))],
                        # new list for each row
                        # vertical_spacing=2,
                        horizontal_spacing=0.03,  # space between the columns
                        )

    # Iterate DF and fetch one row at a time
    for i in range(len(grouped_df)):  # fetch row by index
        # CALCULATE
        row = grouped_df.iloc[i]
        item = row[column_to_group_by]
        total_sales = row['Total Sales']
        color = row['color']
        # print(item, total_sales)

        by_item = df_month_now[df_month_now[column_to_group_by] == item]  # Brand == 'Brand_18' or Store == 'Store 8'
        grouped_by_item = by_item.groupby([column_to_group_by, trees_column]).agg(
            {'Total Sales': ['sum']}).reset_index()  # Brand, Product or  Store, Brand
        grouped_by_item.columns = [column_to_group_by, trees_column, 'Total Sales']

        # PLOTTING
        fig.add_trace(
            go.Bar(
                x=[total_sales],  # 1 val
                y=[f'{item} ' + 20 * ' '],  # 1 val
                text=f'{currency_sign} {value_format(total_sales)}',
                # outside value formatting
                textposition='auto',
                marker={'color': color,
                        'line':
                            {'color': color,
                             'width': 1
                             },
                        },
                orientation='h',
                hoverinfo='none',
            ),
            row=i + 1,
            col=1,
        )

        fig.add_trace(go.Treemap(
            # ! labels, parents and values are equal sized arrays !
            labels=grouped_by_item[trees_column],  # Product, Brand
            parents=[item for i in range(len(grouped_by_item))],  # item  or  ' '
            values=grouped_by_item['Total Sales'],  # tree size
            textinfo = "label+percent root",
            # color
            # marker=dict(
            #   colors=['white' for i in range(len(grouped_by_item))],
            #   colorscale='thermal',
            #   cmid=average_score
            # ),
        ), row=i + 1, col=2)

    # UPDATE AXES FOR EACH CHART
    for i in range(len(grouped_df)):
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            title_text=f"<b>Total Sales</b><br>Current Period" if (i == len(grouped_df) - 1) else None,
            # only for the last bar
            title_font={'color': 'grey',
                        'size': 10,
                        },
            row=i + 1, col=1,

        )

        fig.update_yaxes(
            # categoryorder='total ascending' if chart == 'Total Sales' else None,
            # autorange='reversed',
            # autorange='reversed' if chart != 'Total Sales' else None,
            showgrid=False,
            showline=False,
            showticklabels=True,

            # tickmode='array',
            # tickvals=y_line,
            # ticktext=y_names,
            row=i + 1, col=1,
        )

    # ADD X TITLE FOR TREEMAPS - update_xaxes not supported
    fig.add_annotation(text=f"<b>Total Sales by {trees_column}</b><br>Current Period",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=10,
                           color="grey"
                       ),
                       x=0.7, y=-0.07, showarrow=False)

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        # color treemap - only for Store, Brand
        #treemapcolorway=["MediumTurquoise", "DarkTurquoise"] if (trees_column == 'Brand') else None,
        # extendtreemapcolors=True, # add > colors to the treemap
        showlegend=False,
        treemapcolorway=[palette[index] for index in range(1, len(palette) + 1)],
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

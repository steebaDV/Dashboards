from clickhouse_driver import Client
import pandas as pd
import plotly.graph_objects as go
import calendar
import json

from funcs import augment_days, blue_palette, grey_palette, font_family, get_currency_sign, get_palette, value_format

currency_sign = get_currency_sign()
palette = get_palette()

def get_bar_charts_h(month_int, year, df,
                     column_to_group_by,
                     max_bars, bar_charts,
                     palette=palette,
                     column_widths=None,
                     country=None,
                     customer=None):
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
    df_12_m = df[df['DateTime'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates

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

    # BINNING AND MAPPING BY COLOR
    # TOTAL SALES
    total_df_now['quantiles_Total Sales'] = pd.cut(total_df_now['Total Sales'], bins=len(palette),
                                                   labels=[key for key in palette.keys()])
    total_df_now['quantiles_Total Sales'] = total_df_now['quantiles_Total Sales'].map(lambda x: palette[x])

    # SALES MARGIN %
    total_df_now['quantiles_Sales Margin %'] = pd.cut(total_df_now['Sales Margin %'], bins=len(grey_palette),
                                                      labels=[key for key in grey_palette.keys()])
    total_df_now['quantiles_Sales Margin %'] = total_df_now['quantiles_Sales Margin %'].map(lambda x: grey_palette[x])

    # TOTAL SALES MARGIN
    total_df_now['quantiles_Total Sales Margin'] = pd.cut(total_df_now['Total Sales Margin'], bins=len(palette),
                                                          labels=[key for key in palette.keys()])
    total_df_now['quantiles_Total Sales Margin'] = total_df_now['quantiles_Total Sales Margin'].map(
        lambda x: palette[x])

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
    y_names = [name + ' ' for name in total_df_now[column_to_group_by]];
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
                text=[(f' {value_format(x)}%' if chart == 'Sales Margin %' else f' {currency_sign} {value_format(x)}') for x in total_df_now[chart]],
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
















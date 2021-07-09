import pandas as pd
import calendar
from clickhouse_driver import Client
from datetime import datetime
import warnings
warnings.filterwarnings(action='once')
from time import sleep
from plotly import graph_objects as go

client = Client(host='10.0.0.218',
                user='aisurgeclick',
                password='M9YfSU7P1R',
                port='9000',
                database='aisurgeclickdb')

tablename = 'sales_cockpit_matview_v2'

df = pd.DataFrame(client.execute(f'select * from {tablename}'))

try:
    df.columns = ['Current Year', 'Current Month', 'Current Date', 'DateTime', 'Customer', 'Country',
                  'Business Line', 'Total Sales', 'Sales Amount Target', '% of Target', 'Sales per Customer',
                  'Average Selling Price', 'Total Sold Quantity', 'Total Sales Margin', 'Sales Margin %',
                  'Total Sales Costs', 'Sales Costs %', 'Active Customers', 'New Customers', 'Distinct Items Sold'] #20
except Exception as e:
    print('THE FOLLOWING EXCEPTION WAS RAISED DURING THE LUNCH:')
    print(e)
    column_names = client.execute(f'SHOW CREATE superstore.sales_cockpit_matview_v2')
    string = column_names[0][0]
    lst = string.split('`')
    column_names = lst[1::2]
    # MAINTAIN THE ORDER
    column_names = list(dict.fromkeys(column_names))
    df.columns = column_names

print(df.columns)
print(f'DF len: {len(df)}')
print(df.head(10))


# YEARS
avbl_years = sorted(df['DateTime'].dt.year.unique().tolist())
print(avbl_years)



# CHECK DATA
blue_palette = {1: '#d2fbd4',
                2: '#a5dbc2',
                3: '#7bbcb0',
                4: '#559c9e',
                5: '#3a7c89',
                6: '#235d72',
                7: '#123f5a',
}

grey_palette = {1: '#f9f9f9',
                2: '#ececec',
                3: '#dfdfdf',
                4: '#d3d3d3',
                5: '#c6c6c6',
                6: '#b9b9b9',
                7: '#acacac',
}

orange_palette = {1: '#ecda9a',
                  2: '#efc47e',
                  3: '#f3ad6a',
                  4: '#f7945d',
                  5: '#f97b57',
                  # 6: '#f66356',
                  # 7: '#ee4d5a',
}


#INDICATORS
# def get_current_and_prev_data(current_year, current_month, df, chart_type, country, customer):
#     # FILTER BY DATE
#     # current_year = 2011
#     # current_int = 7
#     # current_month = calendar.month_abbr[current_int]
#     # country = None
#     # customer = None
#
#     prev_year = current_year - 1
#     # print(f'current_year: {current_year}, current_month: {current_month}, country: {country}, customer: {customer}')
#     df_current = df[(df['Current Year'] == current_year) & (df['Current Month'] == current_month)]
#     df_prev = df[(df['Current Year'] == prev_year) & (df['Current Month'] == current_month)]
#     # FILTER BY COUNTRY
#     if country is not None:
#         df_current = df_current[(df_current['Country'] == country)]
#         df_prev = df_prev[(df_prev['Country'] == country)]
#
#     if customer is not None:
#         df_current = df_current[(df_current['Customer'] == customer)]
#         df_prev = df_prev[(df_prev['Customer'] == customer)]
#
#     # print(df_current)
#     # prev_year = current_year - 1
#     # df_current = df[(df['Current Year'] == current_year) & (df['Current Month'] == current_month)]
#     # # df_current = df[(df['Current Year'] == current_year)]
#     # df_prev = df[(df['Current Year'] == prev_year) & (df['Current Month'] == current_month)]
#
#
#     total_sales_current = df_current['Total Sales'].sum()
#     total_sales_prev = df_prev['Total Sales'].sum()
#
#     if chart_type == 'Total Sales':
#         df_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg({'Total Sales': ['sum']}).reset_index()
#         df_groupby.columns = ['DateTime', 'Total Sales']
#
#         diff_percent = round((total_sales_current - total_sales_prev) / total_sales_prev * 100, 1)
#         return df_groupby, total_sales_current, total_sales_prev, diff_percent
#
#     elif chart_type == 'Sales per Customer':
#         df_current_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg({'Customer': ['count'], 'Total Sales': ['sum']}).reset_index()
#         # print(df_current_groupby)
#         df_current_groupby.columns = ['DateTime', 'Customer', 'Total Sales']
#         # df_current_grouped_by_customers = df_current.groupby(['Current Month', 'Customer', 'Country']).agg(
#         #     {'Total Sales': 'sum'}).reset_index()
#         # df_current_groupby = df_current.groupby('Current Month').agg({'Total Sales': 'sum'}).reset_index()
#         # df_prev_grouped_by_customers = df_prev.groupby(['Current Month', 'Customer', 'Country']).agg(
#         #     {'Total Sales': 'sum'}).reset_index()
#         df_prev_grouped_by_customers = df_prev.groupby(pd.Grouper(key='DateTime', freq='1D')).agg({'Customer': ['count'], 'Total Sales': ['sum']}).reset_index()
#         unique_customers_current = df_current.value_counts(['Customer', 'Country']).shape[0]
#         # unique_customers_current_2 = df_current.groupby(['Customer', 'Country']).ngroups
#         # print(f'unique_customers_current: {unique_customers_current}, unique_customers_current_2: {unique_customers_current_2}')
#         unique_customers_prev = df_prev.value_counts(['Customer', 'Country']).shape[0]
#         sales_per_customer_current = total_sales_current / unique_customers_current
#         sales_per_customer_prev = total_sales_prev / unique_customers_prev
#         diff_percent = round((sales_per_customer_current - sales_per_customer_prev) / sales_per_customer_prev * 100, 1)
#         return df_current_groupby, sales_per_customer_current, sales_per_customer_prev, diff_percent
#
#     elif chart_type == 'Total Sold Quantity':
#         total_sales_quantity_current = df_current['Total Sold Quantity'].sum()
#         total_sales_quantity_prev = df_prev['Total Sold Quantity'].sum()
#         df_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg({'Total Sold Quantity': ['sum']}).reset_index()
#         df_groupby.columns = ['DateTime', 'Total Sold Quantity']
#         # df_groupby = df_current.groupby('Current Month').agg({'Total Sold Quantity': 'sum'}).reset_index()
#         diff_percent = round((total_sales_quantity_current - total_sales_quantity_prev) / total_sales_quantity_prev * 100, 1)
#         return df_groupby, total_sales_quantity_current, total_sales_quantity_prev, diff_percent
#
#     elif chart_type == 'Average Selling Price':
#         df_groupby_date_current = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
#             {'Total Sales': ['sum'], 'Total Sold Quantity': ['sum']}).reset_index()
#         df_groupby_date_current.columns = ['DateTime', 'Total Sales', 'Total Sold Quantity']
#         df_groupby_date_prev = df_prev.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
#             {'Total Sales': ['sum'], 'Total Sold Quantity': ['sum']}).reset_index()
#         df_groupby_date_prev.columns = df_groupby_date_current.columns
#         # df_groupby_date_current = df_current.groupby('Current Month').agg(
#         #     {'Total Sales': 'sum', 'Total Sold Quantity': 'sum'}).reset_index()
#         # df_groupby_date_prev = df_prev.groupby('Current Month').agg(
#         #     {'Total Sales': 'sum', 'Total Sold Quantity': 'sum'}).reset_index()
#         df_groupby_date_current['Average Selling Price'] = df_groupby_date_current['Total Sales']/df_groupby_date_current['Total Sold Quantity']
#         df_groupby_date_current = df_groupby_date_current.fillna(0)
#         # print('df_groupby_date_current')
#         # print(df_groupby_date_current)
#
#         average_selling_price_current = round(
#             df_groupby_date_current['Total Sales'].sum() / df_groupby_date_current['Total Sold Quantity'].sum(), 1)
#         average_selling_price_prev = round(
#             df_groupby_date_prev['Total Sales'].sum() / df_groupby_date_prev['Total Sold Quantity'].sum(), 1)
#         diff_percent = round(
#             (average_selling_price_current - average_selling_price_prev) / average_selling_price_prev * 100, 1)
#         return df_groupby_date_current, average_selling_price_current, average_selling_price_prev, diff_percent
#
#     elif chart_type == 'Active Customers':
#         df_groupby_date_current = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
#             {'Customer': ['count']}).reset_index()
#         df_groupby_date_current.columns = ['DateTime', 'Customer']
#         df_groupby_date_prev = df_prev.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
#             {'Customer': ['count']}).reset_index()
#         df_groupby_date_prev.columns = df_groupby_date_current.columns
#
#         # df_groupby_date_current = df_current.groupby(['Current Month']).agg({'Customer': 'count'}).reset_index()
#         # df_groupby_date_prev = df_prev.groupby('Current Month').agg({'Customer': 'count'}).reset_index()
#         active_customers_current = df_current.groupby(['Current Month', 'Customer', 'Country']).ngroups
#         active_customers_prev = df_prev.groupby(['Current Month', 'Customer', 'Country']).ngroups
#
#         diff_percent = round((active_customers_current - active_customers_prev) / active_customers_prev * 100, 1) if active_customers_prev != 0 else np.nan
#         return df_groupby_date_current, active_customers_current, active_customers_prev, diff_percent
#
#     elif chart_type == 'Total Sales Margin':
#         df_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
#             {'Total Sales Margin': ['sum']}).reset_index()
#         df_groupby.columns = ['DateTime', 'Total Sales Margin']
#         # df_groupby = df_current.groupby('Current Month').agg({'Total Sales Margin': 'sum'}).reset_index()
#         total_sales_margin_current = df_current['Total Sales Margin'].sum()
#         total_sales_margin_prev = df_prev['Total Sales Margin'].sum()
#         df_groupedby_date_current = df_current.groupby('Current Date').agg({'Total Sales Margin': 'sum'}).reset_index()
#         diff_percent = round((total_sales_margin_current - total_sales_margin_prev) / total_sales_margin_prev * 100, 1)
#         return df_groupby, total_sales_margin_current, total_sales_margin_prev, diff_percent
#     #
#     elif chart_type == 'Sales Margin %':
#         sales_margin_percent_current = df_current['Total Sales Margin'].sum() / df_current['Total Sales'].sum() * 100
#         sales_margin_percent_prev = df_prev['Total Sales Margin'].sum() / df_prev['Total Sales'].sum() * 100
#         df_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
#             {'Total Sales Margin': ['sum'], 'Total Sales': ['sum']}).reset_index()
#         # df_groupby = df_current.groupby('Current Month').agg(
#         #     {'Total Sales Margin': 'sum', 'Total Sales': 'sum'}).reset_index()
#         df_groupby.columns = ['DateTime', 'Total Sales Margin', 'Total Sales']
#         df_groupby['Sales Margin %'] = df_groupby['Total Sales Margin'] / df_groupby['Total Sales'] * 100
#         diff_percent = round(
#             (sales_margin_percent_current - sales_margin_percent_prev) / sales_margin_percent_prev * 100, 1)
#         return df_groupby, sales_margin_percent_current, sales_margin_percent_prev, diff_percent
#     #
#     elif chart_type == 'New Customers':
#         new_customers_col = []
#
#         count_of_new_customers_prev = 0
#         count_of_new_customers_current = 0
#         for date, customer in zip(df_current['Current Date'], df_current['Customer']):
#             if customer not in list(df[df['Current Date'] < date]['Customer']):
#                 new_customers_col.append(1)
#                 count_of_new_customers_current += 1
#             else:
#                 new_customers_col.append(0)
#         for date, customer in zip(df_prev['Current Date'], df_prev['Customer']):
#             if customer not in list(df[df['Current Date'] < date]['Customer']):
#                 count_of_new_customers_prev += 1
#
#         df_current['New Customers'] = new_customers_col
#
#         count_of_new_customers_current = df_current['New Customers'].sum()
#         df_groupby_date = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
#             {'New Customers': ['sum']}).reset_index()
#         df_groupby_date.columns = ['DateTime', 'New Customers']
#         # df_groupby_date = df_current.groupby('Current Month').agg({'New Customers': 'sum'}).reset_index()
#         diff_percent = round(
#             (count_of_new_customers_current - count_of_new_customers_prev) / count_of_new_customers_current * 100, 1)
#
#         return df_groupby_date, count_of_new_customers_current, count_of_new_customers_prev, diff_percent
#
#
# def create_figure(df_x, df_y, value, reference, chart_type):
#     if chart_type in ['Total Sold Quantity', 'Active Customers', 'Sales Margin %', 'New Customers']:
#         prefix = ""
#     else:
#         prefix = "$"
#     if chart_type in ['Sales Margin %']:
#         valueformat_1 = "%"
#     else:
#         valueformat_1 = ",.0f"
#     if chart_type in ['New Customers', 'Active Customers']:
#         valueformat_2 = ""
#     else:
#         valueformat_2 = ".2s"
#     if chart_type in ['New Customers', 'Sales Margin %']:
#         fig = go.Figure(go.Bar(x=df_x,
#                                y=df_y,
#                                marker_color='#E8E8E8'))
#     else:
#         fig = go.Figure(go.Scatter(x=df_x,
#                                    y=df_y,
#                                    mode='lines',
#                                    fill='tozeroy',
#                                    # hovertemplate='<extra></extra>',
#                                    line_color='#E8E8E8'))
#     fig.add_trace(go.Indicator(mode="number+delta",
#                                value=value,
#                                title={"text": chart_type,
#                                       'font': {'size': 17,
#                                                },
#                                },
#                                number={'prefix': prefix,
#                                        'valueformat': valueformat_1,
#                                        'font': {'size': 17,
#                                                 },
#                                },
#                                delta={'position': 'left',
#                                       'reference': reference,
#                                       'valueformat': valueformat_2,
#                                       'font': {'size': 13,
#                                                },
#                                },
#                                domain={'y': [0, 0.7], 'x': [0.25, 0.75]}))
#     # SET FONT
#     fig.update_layout(autosize=True,
#                       font={
#                             # 'family': font_family,
#                             # 'color': 'black',
#                             # 'size': 12
#                       },
#     )
#     return fig
#
#
# def augment_days(month_int, year, df):
#     from calendar import monthrange
#     _, max_days = monthrange(year, month_int)
#     updated_dates = pd.date_range(f'{month_int}-1-{year}', f'{month_int}-{max_days}-{year}')  # full month range
#     df_augmented = df.set_index('DateTime').reindex(updated_dates).fillna(0.0).rename_axis('DateTime').reset_index()
#
#     return df_augmented
#
# def get_indicator_plot(current_year, current_month, df, chart_type, country=None, customer=None):
#     prev_year = current_year - 1
#     df_1, dim_1, dim_2, diff = get_current_and_prev_data(current_year, current_month, df, chart_type, country, customer)
#     month_int = list(calendar.month_abbr).index(current_month)  # month abr to int
#     # print(f'current_month indicator: {month_int}')
#     df_1 = augment_days(month_int, current_year, df_1)
#     # print('df_1')
#     # print(df_1)
#     df_x = df_1['DateTime']
#     # print('df_x')
#     # print(df_x)
#     # df_x = df_1['Current Month']
#     if chart_type in ['Total Sales']:
#         df_y = df_1['Total Sales']
#     elif chart_type in ['Sales per Customer']:
#         df_y = df_1['Total Sales']
#     elif chart_type in ['Active Customers']:
#         df_y = df_1['Customer']
#     elif chart_type in ['Sales Margin %']:
#         df_y = df_1['Sales Margin %']
#     elif chart_type in ['New Customers']:
#         df_y = df_1['New Customers']
#     elif chart_type in ['Average Selling Price']:
#         df_y = df_1['Average Selling Price']
#     elif chart_type in ['Total Sold Quantity']:
#         # df_1.columns = ['DateTime', 'Total Sold Quantity']
#         # print(df_1['Total Sold Quantity'].sum())
#         df_y = df_1['Total Sold Quantity']
#     elif chart_type in ['Total Sales Margin']:
#         df_y = df_1['Total Sales Margin']
#
#     # print(f'df_y: {df_y}')
#     fig = create_figure(df_x, df_y, dim_1, dim_2, chart_type)
#     fig.update_layout(xaxis={'showgrid': False,
#                              'showticklabels': False},
#                       yaxis={'showgrid': False,
#                              'showticklabels': False},
#                       plot_bgcolor='#FFFFFF',
#                       # width=800,
#                       # height=500,
#                       xaxis_title=f"<b>{'+' if diff > 0 else ''}{diff}%</b> vs {current_month}-{prev_year}", # YTD
#                       xaxis_title_font={'color': 'grey',
#                                         'size': 12,
#                       },
#                       margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
#                                   r=0,
#                                   b=0,
#                                   t=15,
#                                   #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
#                       ),
#                       autosize=True,
#     )
#
#
#     # fig.show()
#     return fig
#
#
#
# indicator_fig = get_indicator_plot(2010, 'Jul', df, 'Total Sales', country=None, customer=None)
# print(indicator_fig)


# BARS
def get_bar_charts_h(month_int, year, df,
                     column_to_group_by,
                     max_bars, bar_charts,
                     palette=blue_palette,
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
                text=[(f' {x:,.1f}%' if chart == 'Sales Margin %' else f' $ {x:,.0f}') for x in total_df_now[chart]],
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
                          # 'family': font_family,
                          # 'color': 'black',
                          # 'size': 12
                      },
    )

    return fig


# bar_chart = get_bar_charts_h(month_int=7, year=2010, df=df,
#                  column_to_group_by='Business Line',
#                  max_bars=7,
#                  bar_charts=['Total Sales', 'Sales Margin %'],
#                  country=None, customer=None)

print('top-products-bar-h-2 Input:')
month = 7
year = 2010

top_products_bar_h_2 = get_bar_charts_h(month_int=month, year=year, df=df,
                                        column_to_group_by='Business Line',
                                        max_bars=7, palette=orange_palette,
                                        bar_charts=['Total Sales', 'Sales Margin %'],
                                        country=None, customer=None)

print('CREATED BAR CHART:')
print(top_products_bar_h_2)










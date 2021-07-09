from clickhouse_driver import Client
import pandas as pd
import plotly.graph_objects as go
import calendar
import json
from funcs import augment_days, blue_palette, grey_palette, orange_palette, customers_palette, \
    font_family, get_currency_sign, value_format, get_palette

currency_sign = get_currency_sign()
palette = get_palette()


numbers_lst = list(range(1, len(palette)))


def get_active_and_new_customers(month_int, max_year, df, range=3, country=None, customer=None, product=None,
                                 palette=palette
                                 ):
    # range = 3
    # month_int = 7
    # max_year = 2010
    # df = df
    palette = [palette[index] for index in numbers_lst]
    min_year = max_year - range
    # SELECT RANGE
    from calendar import monthrange
    _, max_days = monthrange(max_year, month_int)  # not including the current month
    start_date, end_date = f'{min_year}-{month_int}-01', f'{max_year}-{month_int}-{max_days}'
    # print(start_date, end_date)  # 2008-7-01 2011-7-31 - # including

    df_range = df[
        df['DateTime'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates
    if country is not None:
        df_range = df_range[df_range['Country'] == country]
    if customer is not None:
        df_range = df_range[df_range['Customer'] == customer]
    if product is not None:
        df_range = df_range[df_range['Business Line'] == product]

    df_range['customer_country'] = df_range[['Customer', 'Country']].agg(' '.join,
                                                                         axis=1)  # del active_customers_gp['Country']
    active_customers_gp = df_range.groupby(pd.Grouper(key='DateTime', freq='M'))[
        'customer_country'].nunique()  # unique customers by month !!!
    # convert series to DF
    active_customers_gp = active_customers_gp.to_frame().reset_index()

    # new customers and first purchase date
    df_min_purchase = df_range.groupby(['Customer', 'Country']).DateTime.min().reset_index()
    new_customers_gp = df_min_purchase.groupby(pd.Grouper(key='DateTime', freq='M'))['Customer'].nunique().reset_index()

    # augment months for new_customers_gp
    customers_gp = pd.merge(new_customers_gp, active_customers_gp, how='right', on=['DateTime']).fillna(0.0)
    customers_gp.columns = ['DateTime', 'new_customers', 'active_customers']
    customers_gp = customers_gp.astype({'new_customers': 'int64'})

    palette.reverse()
    palette2 = {}
    for i, c in zip(numbers_lst, palette):
        palette2[i] = c
    customers_gp['colors'] = pd.cut(customers_gp['new_customers'], bins=len(palette),
                                    labels=[key for key in palette2.keys()])
    customers_gp['colors'] = customers_gp['colors'].map(lambda x: palette2[x])
    palette.reverse()

    # color bars by new_customers
    # customers_gp['colors'] = pd.cut(customers_gp['new_customers'], bins=4, labels=[1, 2, 3, 4])
    # customers_gp['colors'] = customers_gp['colors'].map(lambda x: customers_palette[x])

    # PLOTTING
    fig = go.Figure()
    # Active Customers Line
    fig.add_trace(go.Scatter(
        x=customers_gp["DateTime"],
        y=customers_gp["active_customers"],
        mode="lines",
        line=dict(color='grey', width=2),
        text=[date.strftime('%b') for date in customers_gp["DateTime"]],
        hovertemplate='Month: %{text}<br>'
                      'Active Customers: %{y}<extra></extra>',
        opacity=0.3,
    ))

    fig.add_trace(go.Bar(
        x=customers_gp["DateTime"],
        y=customers_gp["new_customers"],
        marker_color=customers_gp['colors'],
        text=[date.strftime('%b') for date in customers_gp["DateTime"]],
        hovertemplate='Month: %{text}<br>'
                      'New Customers: %{y}<extra></extra>',
    ))

    colored_years = customers_gp["DateTime"].dt.year.unique().tolist()[1::2]  # [2009, 2011]
    max_y = customers_gp["active_customers"].max()
    for year in colored_years:
        max_date = customers_gp.loc[customers_gp['DateTime'].dt.year == year].max()[0].strftime("%Y-%m-%d")
        fig.add_vrect(
            x0=f'{year}-01-01',  # start
            x1=f'{year}-12-31' if colored_years.index(year) != 1 else max_date,  # end
            y0=0,
            y1=max_y + max_y * 0.1,
            fillcolor="#E8E8E8", opacity=0.3,
            layer="below", line_width=0,
        ),

    fig.update_xaxes(
        showline=False,
        showgrid=False,
        showticklabels=True,
        dtick="M1",
        tickformat="%b",  # %b\n%Y",
        tickfont=dict(size=9,  # customize tick size
                      # color='default',
                      ),
        ticks='',  # |
        tickangle=0,
    )

    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
    )

    fig.update_layout(
        title=dict(text='Line=Active Customers #            Bar=New Customers #',
                   font=dict(size=12,
                             color='grey',
                             ),
                   # alignment
                   x=0.5, y=1,
                   # xanchor='center', yanchor='top'
                   ),
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
                          # 'color': 'black',
                          # 'size': 12
                      },
                      )

    return fig

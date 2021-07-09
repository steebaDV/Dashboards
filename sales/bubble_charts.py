from clickhouse_driver import Client
import pandas as pd
import plotly.graph_objects as go
import calendar
import json

from funcs import augment_days, blue_palette, grey_palette, orange_palette, \
    font_family, get_currency_sign, get_palette

currency_sign = get_currency_sign()
palette = get_palette()


def get_bubble_chart(month_int, year, df, column_to_group_by, palette=palette, country=None, customer=None):
    '''
    There is one bubble per product group.
    Each product is located on the chart:

    Horizontally by Total Sales
    Vertically by Sales Margin %
    The size of the bubble is based on the Total Sales, the color is based on the Sales Margin %.
    '''
    # month_int = 7
    # year = 2011
    # df = df
    # column_to_group_by = 'Business Line'
    # column_to_group_by = 'Customer'

    month_name = calendar.month_name[month_int]
    previous_year = year - 1
    # print(f'month_name: {month_name}, month_int: {month_int}, year: {year}')
    '''Total Sales = SUM Total Sales'''
    '''Sales Margin %  = (SUM Total Sales Margin/ SUM Total Sales)*100'''
    # NOW
    df_month_now = df[(df['DateTime'].dt.month == month_int) & (df['DateTime'].dt.year == year)].copy()
    if country is not None:
        df_month_now = df_month_now[df_month_now['Country'] == country]

    if customer is not None:
        df_month_now = df_month_now[df_month_now['Customer'] == customer]

    df_bubble = df_month_now.groupby([column_to_group_by]).agg(
        {'Total Sales Margin': ['sum'], 'Total Sales': ['sum']}).reset_index()
    df_bubble.columns = [column_to_group_by, 'Total Sales Margin', 'Total Sales']
    df_bubble['Sales Margin %'] = (df_bubble['Total Sales Margin'] / df_bubble['Total Sales']) * 100
    df_bubble = df_bubble.sort_values(by='Total Sales', ascending=False)
    # BINNING
    df_bubble['quantiles'] = pd.cut(df_bubble['Sales Margin %'], bins=len(palette),
                                    labels=[key for key in palette.keys()])

    df_bubble['quantiles'] = df_bubble['quantiles'].map(lambda x: palette[x])
    df_bubble['size'] = df_bubble['Total Sales'] / 500

    fig = go.Figure(
        go.Scatter(
            x=df_bubble['Total Sales'],
            y=df_bubble['Sales Margin %'],
            text=[x for x in df_bubble[column_to_group_by]],
            hovertemplate='%{text}<extra></extra>',
            textposition='bottom center',
            mode='markers+text',
            marker=dict(
                size=df_bubble['size'],  # Total Sale
                color=df_bubble['quantiles'],  # by Sales Margin %
                # colorscale='Viridis',
            ),

        )
    )

    # ['top left', 'top center', 'top right', 'middle left',
    # 'middle center', 'middle right', 'bottom left', 'bottom center', 'bottom right']

    fig.update_xaxes(
        # zeroline=True,
        # zerolinewidth=2,
        # zerolinecolor='Black',

        showline=False,
        showgrid=False,
        showticklabels=True,
        tickprefix=currency_sign,
        tickformat=",",  # d3 formatting  http://bl.ocks.org/ix4/934f36e16bcc7d57a8bc83fe7f4695c2
        title_text=f"<b>Total Sales</b>",
        title_font={'color': 'grey',
                    'size': 12,
                    },
    )

    fig.update_yaxes(
        # zeroline=True,
        # zerolinewidth=2,
        # zerolinecolor='Black',

        showgrid=False,
        showline=False,
        showticklabels=True,
        # rangemode='nonnegative',
        # 1 option
        tickformat='%',
        tickmode='linear',
        # tick0=0.0,
        # dtick=1,
        # range=[0, df_bubble['Sales Margin %'].max()],
        title_text=f"<b>Sales Margin %</b>",
        title_font={'color': 'grey',
                    'size': 12,
                    },

    )

    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        autosize=True,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=0,
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

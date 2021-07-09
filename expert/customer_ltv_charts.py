import pandas as pd
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from plotly import graph_objects as go
import numpy as np
from funcs import font_family, filter_data, get_currency_sign, value_format

currency_sign = get_currency_sign()


def get_table(df, ltv_on):
    customers_list = df['Customer'].unique()
    customers_dict = {
        customer: df[df['Customer'] == customer]['DateTime'].min() for customer in customers_list}
    df['at n years'] = df.apply(lambda x: int((x['DateTime'] - customers_dict[x['Customer']]).days / 365) + 1,
                                axis=1)
    df = df[df['at n years'] <= 5]
    df['First Sales Date'] = df.apply(lambda x: customers_dict[x['Customer']].year, axis=1)

    year_list = sorted(df['First Sales Date'].unique())

    total_ltv_per_year = df.groupby(pd.Grouper(key='at n years')).agg(
        {ltv_on: ['sum']}).cumsum().reset_index()
    total_ltv_per_year.columns = ['at n years', ltv_on]
    total_ltv_per_year = total_ltv_per_year[ltv_on].tolist() + [None] * (5 - len(total_ltv_per_year))

    total_cr_per_year = df[['at n years', 'Customer']].groupby(['at n years', 'Customer']).first().reset_index()
    total_cr_per_year = [len(total_cr_per_year[total_cr_per_year['at n years'] == year]['Customer'].unique()) for year
                         in range(1, 6)]
    total_cr_per_year = [(1 - total_cr_per_year[index] / total_cr_per_year[0]) * 100 for index in
                         range(1, len(total_cr_per_year))]
    total_cr_per_year = total_cr_per_year + [None] * (5 - len(total_cr_per_year))

    ltv_per_year = df.groupby(['First Sales Date', 'at n years']).agg(
        {ltv_on: ['sum']}).reset_index()
    ltv_per_year.columns = ['First Sales Date', 'at n years', ltv_on]
    LTV_list = []
    for year in year_list:
        LTV_list.append(ltv_per_year[ltv_per_year['First Sales Date'] == year][ltv_on].cumsum().tolist())
    LTV_list = list(map(lambda x: x + [None] * (5 - len(x)), LTV_list))

    cr_per_year = df[['First Sales Date', 'at n years', 'Customer']].groupby(
        ['First Sales Date', 'at n years', 'Customer']).first().reset_index()
    CR_list = []
    for year in year_list:
        cr = []
        for n in range(1, 6):
            cr.append(len(cr_per_year[(cr_per_year['First Sales Date'] == year) & (cr_per_year['at n years'] == n)][
                              'Customer'].unique()))
        cr = [(1 - cr[index] / cr[0]) * 100 for index in range(1, len(cr))] + [None] * (6 - len(cr))
        CR_list.append(cr)

    number_of_customers = [len(df['Customer'].unique())]
    for year in year_list:
        number_of_customers.append(len(df[df['First Sales Date'] == year]['Customer'].unique()))

    LTV_dict = dict()
    CR_dict = dict()
    for col in range(5):
        LTV_dict[f'LTV{col + 1}'] = [total_ltv_per_year[col]] + list(map(lambda x: x[col], LTV_list))
        if col != 4:
            CR_dict[f'CR{col + 1}'] = [total_cr_per_year[col]] + list(map(lambda x: x[col], CR_list))

    table = pd.DataFrame(
        {
            'First Sales Date': ['Total'] + list(map(str, sorted(np.unique(ltv_per_year['First Sales Date'])))),
            'Number of Customers': list(map(str, number_of_customers)),
            **LTV_dict, **CR_dict
        })
    return table


def get_slot(table, row, col):
    if col == 1:
        return html.Label(table['First Sales Date'][row], style={'font-family':font_family})
    elif col == 2:
        return html.Label(table['Number of Customers'][row], style={'font-family':font_family})
    elif col % 2:
        el = table[f'LTV{col // 2}'][row]
        fig = go.Figure(go.Bar(
            x=[el],
            text=[f'{currency_sign}{value_format(el)}'],
            textposition='outside',
            cliponaxis=False,
            orientation='h',
            hoverinfo='none',
            textangle=90
        ))
        fig.update_yaxes(showticklabels=False)
        fig.update_xaxes(showticklabels=False,
                         range=[0,
                                1.5 * table[[column for column in table.columns if column[:3] == 'LTV']].max().max()])
        fig.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False,
            autosize=True,
            # width=1230,
            # height=225,
            margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                        r=0,
                        b=0,
                        t=0,
                        #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                        ),
            font_family=font_family
            # width=800,
            # height=500,
        )
        return dcc.Graph(figure=fig, style={
            # 'border': '1px solid green',
            'height': '95%',
            'width': '95%'})

    elif col == 12:
        return None
    else:
        el = round(table[f'CR{col // 2 - 1}'][row],1)
        fig = go.Figure(data=[go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker_size=[0.5*el])
        ])
        fig.add_annotation(x=0, y=0,
                           text=f'{value_format(el)}%',
                           showarrow=False,
                           font=dict(color='black',
                                     # family="Courier New, monospace",
                                     size=15,  # size: 15..30
                                     ),
                           )
        fig.update_yaxes(showticklabels=False)
        fig.update_xaxes(showticklabels=False)
        fig.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False,
            autosize=True,
            # width=1230,
            # height=225,
            margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                        r=0,
                        b=0,
                        t=0,
                        #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                        ),
            font_family=font_family
            # width=800,
            # height=500,
        )
        return dcc.Graph(figure=fig, style={
            'height': '95%',
            'width': '95%'})


def get_ltv_table(df, customer, country, product_group, ltv_on):
    df_filtered = filter_data(df, customer, country, product_group)
    table = get_table(df_filtered, ltv_on)
    row1 = [
        dbc.Row(
            [
                dbc.Col(html.H6(f'at {col} year', style={'color': 'white',
                                                         'background': 'grey',
                                                         'font-family':font_family,
                                                         'text-align': 'center'}
                                ) if col != 0 else None) for col in range(6)
            ], style={'height': '1rem'}
        )
    ]
    row2 = [
        dbc.Row([
            dbc.Col(html.Label(
                column, style={'color': 'SteelBlue' if column == 'Lifetime Value' else None,
                               'font-family':font_family,
                              })
            ) for column in [
                'First Sales Date', 'Number of Customers', *(['Lifetime Value', 'Churn Rate'] * 5)
            ]
        ], style={'height': f'{95 / (len(table) + 1)}%'}
        )
    ]
    children = row1 + row2 + [dbc.Row(
        style={'height': f'{95 / (len(table) + 1)}%'}, children=[
            dbc.Col(
                get_slot(table, row, col)
            ) for col in range(1, 13)
        ]
    ) for row in range(len(table))
    ]
    return children


def get_customer_ltv_1(df, customer, country, product_group, ltv_on):
    df_filtered = filter_data(df, customer, country, product_group)
    table = get_table(df_filtered, ltv_on)

    year_list = table[1:]['First Sales Date'].unique()

    fig = go.Figure()
    for index in range(1, 6):
        y = [table[table['First Sales Date'] == str(year)][f'LTV{index}'].tolist()[0] for year in year_list]
        fig.add_trace(go.Scatter(
            x=year_list,
            y=y,
            text=[f'<br>CLTV year {index}</br>{currency_sign} {value_format(x)}' for x in y],
            mode='lines+text',
        ))
    fig.update_xaxes(
        tickmode='array',
        tickvals=year_list,
        range=[table['First Sales Date'][1:].astype(int).min() - 1, table['First Sales Date'][1:].astype(int).max() + 1]
    )
    fig.update_yaxes(
        showticklabels=False,
        range=[0, 1.35 * table[[f'LTV{index}' for index in range(1, 6)]].max().max()]
    )
    fig.update_traces(textposition='top center')
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        autosize=True,
        # width=1230,
        # height=225,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=0,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family
        # width=800,
        # height=500,
    )
    return fig


def get_customer_ltv_2(df, customer, country, product_group, ltv_on):
    df_filtered = filter_data(df, customer, country, product_group)
    table = get_table(df_filtered, ltv_on)

    y = table[:1][[f'LTV{index}' for index in range(1, 6)]].values[0].tolist()
    year_list = [int(table[1:2]['First Sales Date'].values[0]) + n for n in range(len(y))]
    fig = go.Figure(go.Scatter(
        x=year_list,
        y=y,
        text=[f'{currency_sign} {value_format(x)}' for x in y],
        mode='lines+text',
    ))
    fig.update_xaxes(
        tickmode='array',
        tickvals=[f'Year {index + 1}' for index, year in enumerate(year_list)],
        range=[year_list[0]-1, year_list[-1] + 1]
    )
    fig.update_yaxes(
        showticklabels=False,
        range=[0, 1.35 * max(y)]
    )
    fig.update_traces(textposition='top center')
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        autosize=True,
        # width=1230,
        # height=225,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=0,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family
        # width=800,
        # height=500,
    )
    return fig

def get_customer_ltv_3(df, customer, country, product_group, ltv_on):
    df_filtered = filter_data(df, customer, country, product_group)
    table = get_table(df_filtered, ltv_on)

    y = table[:1][[f'CR{index}' for index in range(1, 5)]].values[0]
    y = y[y != None]
    year_list = [f'Year{index}' for index in range(1, len(y)+1)]
    fig = go.Figure(go.Bar(
        x=year_list,
        y=y,
        text=[f'{value_format(x)}%' for x in y],
        textposition='outside',
    ))
    fig.update_yaxes(
        showticklabels=False,
        range=[0, 135]
    )
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        autosize=True,
        # width=1230,
        # height=225,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=0,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family
        # width=800,
        # height=500,
    )
    return fig

import pandas as pd
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from plotly import graph_objects as go
import json
import numpy as np
import datetime
from funcs import font_family, filter_data, get_currency_sign, value_format, get_palette
import seaborn as sns

currency_sign = get_currency_sign()
palette = sns.color_palette("coolwarm", 10).as_hex()

with open('params.json', 'r') as f:
    params = json.load(f)

class_set = [
    'Champions',
    'Loyal',
    'Potential Loyalist',
    'Promising',
    'New Customers',
    'Need Attention',
    'About to Sleep',
    'At Risk',
    'Hibernating',
    'Cannot Lose Them',
    'Lost'
]
gradation = ['Very High',
             'High',
             'Intermediate',
             'Low',
             'Very Low'
             ]


def get_list(table, column):
    def get_class_list(table):
        return sorted(list(set(class_set).intersection(set(table['Class']))), key=class_set.index)

    def get_monetary_list(table):
        return sorted(table['MonetaryRate'].unique())

    if column == 'Class':
        return get_class_list(table)
    elif column == 'Recency':
        class_list = get_class_list(table)
        recency_list = []
        for class_ in get_class_list(table):
            recency_list.append(sorted(table[table['Class'] == class_]['RecencyRate'].unique()))
        return recency_list
    elif column == 'Monetary':
        return get_monetary_list(table)
    elif column == 'Frequency':
        monetary_list = get_monetary_list(table)
        frequency_list = []
        for monetary in monetary_list:
            frequency_list.append(sorted(table[table['MonetaryRate'] == monetary]['FrequencyRate'].unique()))
        return frequency_list


def get_sublists(list):
    sublists = []
    for sublist in list:
        sublists += [*sublist]
    return sublists


def get_index(list_, sub_index):
    length = -1
    for index, sublist in enumerate(list_):
        if length + 1 == sub_index:
            return index, True
        elif length + len(sublist) >= sub_index:
            return index, False
        else:
            length += len(sublist)


def rate(data, column):
    a = np.quantile(data, [params[column.lower()][0][f"{i}"] for i in range(2, 6)])
    # b = np.quantile(data, [0.2, 0.4, 0.6, 0.8])
    ind = np.argsort(data)
    l = []

    for el in data:
        if el >= a[-1]:
            l.append(5)
        elif el <= a[0]:
            l.append(1)
        else:
            for i in range(3):
                if el < a[i + 1] and el >= a[i]:
                    l.append(i + 2)
    return l


def get_table(df):
    rfm_table = df.groupby(pd.Grouper(key='Customer')).agg(
        {'Total Sales': ['sum'], 'Total Sold Quantity': ['sum'],
         'DateTime': ['min']}).reset_index()
    rfm_table.columns = ['Customer', 'Monetary', 'Frequency', 'Recency']

    rfm_table['Recency'] = datetime.datetime.today() - rfm_table['Recency']
    rfm_table['Recency'] = pd.Series([x.days for x in rfm_table['Recency']])

    rfm_table['MonetaryRate'] = rate(rfm_table['Monetary'], 'Monetary')
    rfm_table['FrequencyRate'] = rate(rfm_table['Frequency'], 'Frequency')
    rfm_table['RecencyRate'] = rate(rfm_table['Recency'] * (-1), 'Recency')

    rfm_table['RFMScore'] = rfm_table.apply(lambda x: f"{x['RecencyRate']}{x['FrequencyRate']}{x['MonetaryRate']}",
                                            axis=1)

    rfm_align = pd.read_csv('RFM.csv').drop([0, 1, 2, 3, 4])
    iterables = [[i for i in range(5, 0, -1)], [i for i in range(5, 0, -1)]]
    rfm_align.index = pd.MultiIndex.from_product(iterables, names=['Recency', 'Frequency'])
    rfm_align.drop(columns=['There are 125 possible combinations of profile.', 'Unnamed: 1'], axis=1, inplace=True)
    rfm_align.columns = ['5', '4', '3', '2', '1']

    rfm_metrics = []
    for i in rfm_align.index:
        for j, el in enumerate(rfm_align.loc[i]):
            rfm_metrics.append([i[0], i[1], 5 - j, el])
            # print('R =', i[0],'F =', i[1], 'M =', 5-j, 'class =', el)

    rfm_metr = pd.DataFrame(rfm_metrics)
    rfm_metr.columns = ['Recency', 'Frequency', 'Monetary', 'Class']
    rfm_metr['RFMScore'] = rfm_metr.apply(lambda x: f"{x['Recency']}{x['Frequency']}{x['Monetary']}", axis=1)

    table = rfm_table.merge(rfm_metr[['Class', 'RFMScore']], on='RFMScore', how='left')
    return table


def get_customer_table(df, customer, country, product):
    def get_slot(table, row, col):
        monetary = monetary_list[get_index(frequency_list, col)[0]]
        class_ = class_list[get_index(recency_list, row)[0]]
        recency = get_sublists(recency_list)[row]
        frequency = get_sublists(frequency_list)[col]
        # str_sum = lambda x,y,z: f'{x}{y}{z}'
        data = table[
            (table['Class'] == class_) &
            (table['RFMScore'] == f'{recency}{frequency}{monetary}')
            ]
        if not data.empty:
            marker_size_list = np.array(list(map(class_set.index, data['Class'].values)))

            max_value = len(class_set) - 1
            min_value = 0
            range_value = max_value - min_value

            quantile = list(map(round, (len(palette) - 1) * (marker_size_list - min_value) / range_value))

            fig = go.Figure(data=[go.Scatter(
                x=np.array(list(range(len(data)))), y=[0] * len(data),
                mode='markers',
                textfont= {'family':font_family},
                marker=dict(color=[palette[q] for q in quantile],
                            size=3 * (marker_size_list + 1),
                            )
            )
            ])
            for index, customer in enumerate(data['Customer'].values):
                fig.add_annotation(y=0.6, x=index,
                                   text=customer,
                                   showarrow=False,
                                   font=dict(color='black',
                                             family=font_family,
                                             size=8,  # size: 15..30
                                             ),
                                   )
            fig.update_yaxes(showticklabels=False, range=[-0.5, 1])
            fig.update_xaxes(showticklabels=False, range=[-0.5, len(data) - 0.5])
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
            graph = dcc.Graph(figure=fig, style={
                'font_family':font_family,
                'height': '95%',
                'width': '95%'})

            return graph
        else:
            return ''

    df_filtered = filter_data(df, customer, country, product)

    table = get_table(df_filtered)

    class_list = get_list(table, 'Class')
    monetary_list = get_list(table, 'Monetary')
    frequency_list = get_list(table, 'Frequency')
    recency_list = get_list(table, 'Recency')

    width = len(get_sublists(frequency_list)) + 2
    height = len(get_sublists(recency_list)) + 2
    children = html.Table(style={'border': '1px solid black', 'height': '100%', 'font_family':font_family}, children=
    [
        html.Tbody(
            [
                html.Tr(style={'border': '1px solid black', 'height': f'{100 / height}%'}, children=
                [
                    html.Td(colSpan=2, rowSpan=2, style={'border': '1px solid black', 'width': f'{100 / width}%'})
                ] +
                [
                    html.Td(gradation[monetary_list[monetary_index] - 1] + ' Total Sales',
                            colSpan=len(frequency_list[monetary_index]),
                            style={'border': '1px solid black', 'width': f'{100 / width}%'}) for monetary_index in
                    range(len(monetary_list))
                ]
                        ),
                html.Tr(style={'border': '1px solid black', 'height': f'{100 / height}%'}, children=
                [
                    html.Td(gradation[frequency - 1] + ' Frequency',
                            style={'border': '1px solid black', 'width': f'{100 / width}%'}) for frequency in
                    get_sublists(frequency_list)
                ]
                        ),

            ] +
            [
                html.Tr(style={'border': '1px solid black', 'height': f'{100 / height}%'}, children=
                ([
                     html.Td(class_list[get_index(recency_list, row)[0]],
                             rowSpan=len(recency_list[get_index(recency_list, row)[0]]),
                             style={'border': '1px solid black', 'width': f'{100 / width}%'})
                 ] if get_index(recency_list, row)[1] else []) +
                [
                    html.Td(gradation[recency - 1] + ' Recency',
                            style={'border': '1px solid black', 'width': f'{100 / width}%'})
                ] +
                [
                    html.Td(style={'border': '1px solid black', 'width': f'{100 / width}%'}, children=
                    [
                        get_slot(table, row, col)
                    ]
                            ) for col, frequency in enumerate(get_sublists(frequency_list))
                ]
                        ) for row, recency in enumerate(get_sublists(recency_list))
            ],
        )
    ]
                          )
    return children

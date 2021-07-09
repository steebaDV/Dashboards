import dash_html_components as html

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

from datetime import datetime
import calendar
from funcs import font_family, value_format, filter_data, prev, filter_on_date, kpis_prep, get_palette

palette = get_palette('list')


def get_accidents_per_client_bar(
        df,
        palette=palette,
        dates=None,
        client_type=None,
        accident_nature=None,
        accident_status=None,
        appeal_status=None,
):
    """
    	Plot bar charts.

    	Parameters
    	----------
    	df : dataframe
    		Data
    	dates : str
    		PDate filter (default None)
    	client_type : str
    		Client Type filter (default None)
    	accident_nature : str
    		Accident Nature filter (default None)
    	accident_status : str
    		Accident Status filter (default None)
    	appeal_status : str
    		Appeal Status filter (default None)
    	palette: dict / list
    		Color palette (default palette)
    	datefield : datetime, optional
    		Date field in the data (default 'Accident Occurrence Date')

    	Returns
    	-------
    	fig
    		Created figure
    	"""

    if dates:
        df = filter_on_date(df, dates)

    df = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    fig = make_subplots(rows=1, cols=4, start_cell="top-left",
                        # subplot_titles=("Total Calls", "SALES MARGIN %", "Total Calls MARGIN",),
                        # column_titles=[f"<b>{chart.upper()}</b>" for chart in bar_charts],
                        # title_font=dict(size=15),
                        # column_widths=[0.26]*3 + [(1-0.26)/3],
                        shared_xaxes=False,
                        shared_yaxes=True,  # True?
                        specs=[[{'type': 'bar'} for column in range(4)]],  # 1 list for 1 row
                        # vertical_spacing=2,
                        horizontal_spacing=0.025,  # space between the columns
                        )

    charts = ['Total Work Interruption', 'Nb of Accidents', 'Avg Work Interruption', 'Nb of Victims']

    df_groupby = df.groupby('Client').agg(
        {
            'Work Interruption (days)': ['sum', 'mean'],
            'Accident #': 'count',
            'Contract #': 'count'
        }).reset_index()
    df_groupby.columns = ['Client'] + [charts[i] for i in [0, 2, 1, 3]]
    df_groupby = df_groupby[['Client', *charts]]

    df_groupby = df_groupby.sort_values(charts[0], ascending=True).reset_index()

    for index, chart in enumerate(charts):
        if index % 2 == 0:
            suffix = ' d'
            prefix = '🕑 '
        else:
            suffix = ''
            prefix = ''

        max_value = df_groupby[chart].max()
        min_value = df_groupby[chart].min()
        range_value = max_value - min_value

        quantile = list(map(round, (len(palette) - 1) * (df_groupby[chart].values - min_value) / range_value))
        fig.add_trace(
            go.Bar(
                x=df_groupby[chart],
                y=df_groupby['Client'],
                # y=[name + ' ' for name in total_df_now[column_to_group_by]],
                # y=y_names,
                text=[f'{prefix}{value_format(x)}{suffix}' for x in df_groupby[chart]],
                cliponaxis=False,
                # outside value formatting
                textposition='outside',
                marker={'color': [palette[q] for q in quantile]},
                # marker={'color': total_df_now[f'quantiles_{chart}'],
                #         'line':
                #             {'color': total_df_now[f'quantiles_{chart}'],
                #              'width': 1
                #              },
                #         },
                # hoverinfo='none', # todo - update info
                orientation='h',
                hoverinfo='none',

            ),
            row=1, col=index + 1,

        ),
        fig.update_xaxes(row=1, col=index + 1, range=[0, 2 * df_groupby[chart].max()])  # sets the range of xaxis
    fig.update_xaxes(showticklabels=False)
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        # autosize=True,
        # width=1230,
        # height=225,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=0,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family,
        height=25 * len(df_groupby),
        width=650,
        # height=500,
    )
    return fig


def get_accidents_per_client(
        df,
        palette=palette,
        dates=None,
        client_type=None,
        accident_nature=None,
        accident_status=None,
        appeal_status=None,
):
    """
    	Plot a scatter plot.

    	Parameters
    	----------
    	df : dataframe
    		Data
    	dates : str
    		PDate filter (default None)
    	client_type : str
    		Client Type filter (default None)
    	accident_nature : str
    		Accident Nature filter (default None)
    	accident_status : str
    		Accident Status filter (default None)
    	appeal_status : str
    		Appeal Status filter (default None)
    	palette: dict / list
    		Color palette (default palette)
    	datefield : datetime, optional
    		Date field in the data (default 'Accident Occurrence Date')

    	Returns
    	-------
    	fig
    		Created figure
    	"""

    if dates:
        df = filter_on_date(df, dates)

    df = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    charts = ['Total Work Interruption', 'Avg Work Interruption', 'Nb of Accidents']

    df_groupby = df.groupby('Client').agg(
        {
            'Work Interruption (days)': ['sum', 'mean', 'count'],
        }).reset_index()
    df_groupby.columns = ['Client', *charts]

    df_groupby = df_groupby.sort_values(charts[0], ascending=True).reset_index()
    df_groupby = df_groupby.iloc[:, 1:]

    max_value = df_groupby[charts[0]].max()
    min_value = df_groupby[charts[0]].min()
    range_value = max_value - min_value

    quantile = np.array(list(map(round, (len(palette) - 1) * (df_groupby[charts[0]].values - min_value) / range_value)))

    length = len(quantile[quantile >= max(quantile) - 2])
    print(df_groupby.iloc[:, :2])
    fig = go.Figure(
        data=[
            go.Scatter(
                x=df_groupby[charts[2]], y=df_groupby[charts[1]],
                mode='markers+text',
                textfont={'family': font_family},
                text=[''] * (len(df_groupby) - length) + df_groupby.loc[length + 1:, 'Client'].to_list(),
                marker=dict(color=[palette[q] for q in quantile],
                            size=[10 * (q + 2) for q in quantile],
                            ),
                hoverinfo='none',
                cliponaxis=False,
                textposition='bottom left',
            )
        ]
    )

    fig.update_yaxes(
        tickmode='array',
        tickvals=df_groupby[charts[1]],
        ticktext=[f'🕑 {value_format(x)} d' for x in df_groupby[charts[1]]],
        title=charts[1]
    )
    fig.update_xaxes(
        title=charts[2]
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
        font_family=font_family,
        # height=500,
    )
    return fig

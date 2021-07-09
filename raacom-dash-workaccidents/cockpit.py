import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
from funcs import font_family, get_currency_sign, value_format, filter_data, prev, filter_performance_scope, get_palette, kpis_prep
from top_performers_tab import get_current_and_prev_data

palette = get_palette('dict')
currency_sign = get_currency_sign()

def get_horizontal_bar_chart_2(df,
                             current_year,
                             current_month,
                             chart,
                             performance_scope,
                             top,
                             client_type=None,
                             accident_nature=None,
                             accident_status=None,
                             appeal_status=None,
                             palette=palette,
                             datefield='Accident Occurrence Date'):
    """
    Plot a horizontal bar chart.
    
    Parameters
    ----------
    df : dataframe
        Data
    current_year : int
        Current year filter
    current_month : int
        Current month filter
    chart : str
        KPI to calculate and use
    performance_scope : str
        Performance scope filter
    client_type : str
        Client Type filter
    accident_nature : str
        Accident Nature filter
    accident_status : str
        Accident Status filter
    appeal_status : str
        Appeal Status filter
    palette: dict / list
        Color palette
    datefield : datetime, optional
        Date field in the data (default 'Accident Occurrence Date')

    Returns
    -------
    fig
        Created figure
    """
    
    main_kpis = ['Nb of Accidents', 'Work Accidents %', 'Serious Accidents %',\
                 'Accidents with Work Interruption %', 'Avg Work Interruption', 'Total Work Interruption']

    # DATA
    prev_year, prev_month = prev(current_year, current_month, performance_scope)
    df_filtered = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    if performance_scope == 'Year-to-Date: Current Year vs Previous Year':
        ytd_marker = 'YTD'
    else:
        ytd_marker = ''
    
    df_current, df_prev = filter_performance_scope(df_filtered, current_year, current_month, performance_scope)
    df_current_init, _, _, _ = get_current_and_prev_data(
        df_current, current_year, current_month, main_kpis[0], performance_scope, n_months=None, group_on=top)
    df_prev_init, _, _, _ = get_current_and_prev_data(
        df_prev, current_year, current_month, main_kpis[0], performance_scope, n_months=None, group_on=top)

    for chart_type in main_kpis[1:]:
        df_gb_current, _, _, _ = get_current_and_prev_data(
            df_current, current_year, current_month, chart_type, performance_scope, n_months=None, group_on=top)
        df_gb_prev, _, _, _ = get_current_and_prev_data(
            df_prev, current_year, current_month, chart_type, performance_scope, n_months=None, group_on=top)

        df_current_init = pd.merge(df_current_init, df_gb_current, how='inner', on=top)
        df_prev_init = pd.merge(df_prev_init, df_gb_prev, how='inner', on=top)

    df_current_sorted = df_current_init.sort_values(by=top, ascending=True)
    df_prev_sorted = df_prev_init.sort_values(by=top, ascending=True)

    # PLOTTING
    if chart == 'right':

        fig = make_subplots(
            rows=1, cols=len(main_kpis), start_cell="top-left",
            shared_xaxes=False,
            shared_yaxes=True,
            specs=[[{'type': 'bar'} for column in range(len(main_kpis))]],  # 1 list for 1 row
            # vertical_spacing=2,
            horizontal_spacing=0.025,  # space between the columns
        )

        for index, chart_type in enumerate(main_kpis):
            if chart_type in main_kpis:
                prefix = ''
            else:
                prefix = currency_sign
            if chart_type[-1] == '%':
                suffix = '%'
            else:
                suffix = ''

            # COLORING
            df_current_sorted[f'quantiles_{chart_type}']=pd.cut(df_current_sorted[chart_type], bins=len(palette),
                                                                labels=[key for key in palette.keys()])
            df_current_sorted[f'quantiles_{chart_type}']=df_current_sorted[f'quantiles_{chart_type}'].map(lambda x: palette[x])

            fig.add_trace(
                go.Bar(
                    x=df_current_sorted[chart_type],
                    y=df_current_sorted[top],
                    name='',
                    text=[f' {prefix}{value_format(x)}{suffix} {ytd_marker}'
                          for x in df_current_sorted[chart_type]],
                    cliponaxis=False,
                    textposition='outside',
                    marker_color=df_current_sorted[f'quantiles_{chart_type}'],
                    orientation='h',
                    hovertemplate=f'<b>Month: </b>{calendar.month_abbr[current_month]} {current_year}<br><b>{top}:</b> '+'%{y}<br>'+f'<b>{chart_type}:</b>'+'%{text}'+f' <i>{calendar.month_abbr[prev_month]} {prev_year}</i>',
                ),
                row=1, col=index+1,
            ),

            # SET GREY LINES
            #line_colors = {'Total Sales': '#778899', 'Sales Margin %': '#F89C74', 'Total Sales Margin': '#778899'}
            y_line = [y for y in range(len(df_prev_sorted[top]))]
            y_line.reverse()

            x_line = []
            x_line = df_prev_sorted[chart_type].tolist()
            x_line.reverse()

            for x, y in zip(x_line, y_line):
                y_start = y - 0.5
                y_end = y + 0.5

                fig.add_shape(type="line",
                              x0=x, y0=y_start,  # start
                              x1=x, y1=y_end,  # end
                              #line=dict(color=line_colors[chart], width=1.5),
                              line=dict(color='grey',width=1.5),
                              row=1, col=index+1,
                              )

            fig.update_xaxes(row=1, col=index+1,
                             title=chart_type,
                             title_font={'color': 'grey', 'size': 10},
                             range=[0, 1.5 * df_current_sorted[chart_type].max()])  # sets the range of xaxis

        fig.update_yaxes(showticklabels=False)
        fig.update_xaxes(showticklabels=False)

    elif chart == 'left':
        fig = go.Figure(
            go.Bar(
                x=[0] * len(np.unique(df_current_sorted[top])),
                y=df_current_sorted[top],
                orientation='h',
                hoverinfo='none',
            )
        )

        fig.update_xaxes(
            showticklabels=False,
            range=[0, 0],        # sets the range of xaxis
            constrain='domain',  # meanwhile compresses the xaxis by decreasing its 'domain'
        )

    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        autosize=True,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=0,
                    # pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family,
    )

    return fig



def get_bar_chart_uni(df,
                   current_year,
                   current_month,
                   performance_scope,
                   chart,
                   client_type=None,
                   accident_nature=None,
                   accident_status=None,
                   appeal_status=None,
                   palette=palette,
                   datefield='Accident Occurrence Date'):
    """
    Plot a horizontal bar chart.
    
    Parameters
    ----------
    df : dataframe
        Data
    current_year : int
        Current year filter
    current_month : int
        Current month filter
    chart : str
        KPI to calculate and use
    performance_scope : str
        Performance scope filter
    client_type : str
        Client Type filter
    accident_nature : str
        Accident Nature filter
    accident_status : str
        Accident Status filter
    appeal_status : str
        Appeal Status filter
    palette: dict / list
        Color palette
    datefield : datetime, optional
        Date field in the data (default 'Accident Occurrence Date')

    Returns
    -------
    fig
        Created figure
    """
    
    #main_kpis = ['Nb of Accidents', 'Work Accidents %', 'Serious Accidents %',\
    #             'Accidents with Work Interruption %', 'Avg Work Interruption', 'Total Work Interruption']

    # DATA
    prev_year, prev_month = prev(current_year, current_month, performance_scope)
    df_filtered = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    if performance_scope == 'Year-to-Date: Current Year vs Previous Year':
        ytd_marker = 'YTD'
    else:
        ytd_marker = ''
    
    df_current, df_prev = filter_performance_scope(df_filtered, current_year, current_month, performance_scope)

    df_current_init, _, _, _ = get_current_and_prev_data(
        df_current, current_year, current_month, chart, performance_scope, n_months=None)
    df_prev_init, _, _, _ = get_current_and_prev_data(
        df_prev, current_year, current_month, chart, performance_scope, n_months=None)

    df_current_sorted = df_current_init.sort_values(by=chart, ascending=True)
    df_prev_sorted = df_prev_init.sort_values(by=chart, ascending=True)

    # PLOTTING
    if chart in main_kpis:
        prefix = ''
    else:
        prefix = currency_sign
    if chart[-1] == '%':
        suffix = '%'
    else:
        suffix = ''

    # COLORING
    df_current_sorted[f'quantiles_{chart}']=pd.cut(df_current_sorted[chart], bins=len(palette),
                                                        labels=[key for key in palette.keys()])
    df_current_sorted[f'quantiles_{chart}']=df_current_sorted[f'quantiles_{chart}'].map(lambda x: palette[x])

    fig = go.Figure(
        go.Bar(
            x=df_current_sorted[chart],
            y=df_current_sorted[datefield],
            name='',
            text=[f' {prefix}{value_format(x)}{suffix} {ytd_marker} <i>(vs {prefix}{value_format(prev)}{suffix})</i>'
                  for x,prev in zip(df_current_sorted[chart], df_prev_sorted[chart])],
            cliponaxis=False,
            textposition='outside',
            marker_color=df_current_sorted[f'quantiles_{chart}'],
            orientation='h',
            hovertemplate=f'<b>Month: </b>{calendar.month_abbr[current_month]} {current_year}<br><b>{top}:</b> '+'%{y}<br>'+f'<b>{chart}:</b>'+'%{text}'+f' <i>{calendar.month_abbr[prev_month]} {prev_year}</i>',
        ),
        row=1, col=index+1,
    ),

    # SET GREY LINES
            #line_colors = {'Total Sales': '#778899', 'Sales Margin %': '#F89C74', 'Total Sales Margin': '#778899'}
    y_line = [y for y in range(len(df_current_sorted))]
    y_line.reverse()

    x_line = []
    x_line = df_current_sorted[chart].tolist()
    x_line.reverse()

    for x, y in zip(x_line, y_line):
        y_start = y - 0.5
        y_end = y + 0.5

        fig.add_shape(type="line",
                      x0=x, y0=y_start,  # start
                      x1=x, y1=y_end,  # end
                      #line=dict(color=line_colors[chart], width=1.5),
                      line=dict(width=1.5),
                      row=1, col=1,
                      )

    fig.update_xaxes(row=1, col=1,
                     title=f'{chart}<br>Current period',
                     title_font={'color': 'grey', 'size': 10},
                     range=[0, 1.5 * df_current_sorted[chart].max()])  # sets the range of xaxis

    fig.update_xaxes(row=1, col=1,
                     title=f'{chart}<br>Current period',
                     title_font={'color': 'grey', 'size': 12},
                     range=[0, 1.35 * df_current_sorted[chart].max()])  # sets the range of xaxis

    fig.update_yaxes(showticklabels=False)
    fig.update_xaxes(showticklabels=False)

    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        autosize=True,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=0,
                    # pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family,
    )

    return fig

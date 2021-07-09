import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
from funcs import font_family, value_format, filter_data, prev, filter_performance_scope, get_palette, kpis_prep

palette = get_palette('dict')


def get_current_and_prev_data(df, 
                              current_year, 
                              current_month, 
                              chart_type, 
                              performance_scope,
                              n_months=24,
                              group_on='Accident Occurrence Date',
                              datefield='Accident Occurrence Date'):
    """
    Get filtered by date data, current and previous values of KPI and their percent difference 
    based on year, month and performance scope.

    Parameters
    ----------
    current_year : int
        Current year filter
    current_month : int
        Current month filter
    chart_type : str
        KPI to calculate and use
    performance_scope : str, optional
        Performance scope filter (default None)
    n_months : int / None
        Number of months to filter grouped data
    group_on : str
        Field name to group data on
    datefield : datetime, optional
        Date field in the data (default 'Accident Occurrence Date')

    Returns
    -------
    df_groupby
        Data for the last N months with datefield and KPI
    curr_value
        KPI for selected period
    prev_value
        KPI for reference period
    diff_percent
        Percent difference between curr_value and prev_value
    """

    if n_months:
        dfN = df[(df[datefield] >= datetime(current_year - n_months//12, current_month, 1)) & 
            (df[datefield] <= datetime(current_year, current_month, calendar.monthrange(current_year, current_month)[1]))].copy()
    else:
        dfN = df.copy()

    column_to_agg, agg = kpis_prep(dfN, chart_type)
    df_current, df_prev = filter_performance_scope(dfN, current_year, current_month, performance_scope)

    if group_on == datefield:
        df_groupby = dfN.groupby(pd.Grouper(key=datefield, freq='M')).agg({column_to_agg: [agg]}).reset_index()
        df_current = df_current.groupby(pd.Grouper(key=datefield, freq='M')).agg({column_to_agg: [agg]}).reset_index()
        df_prev = df_prev.groupby(pd.Grouper(key=datefield, freq='M')).agg({column_to_agg: [agg]}).reset_index()
    else:
        df_groupby = dfN.groupby(group_on).agg({column_to_agg: [agg]}).reset_index()
        df_current = df_current.groupby(group_on).agg({column_to_agg: [agg]}).reset_index()
        df_prev = df_prev.groupby(group_on).agg({column_to_agg: [agg]}).reset_index()
    df_groupby.columns = [group_on, chart_type]
    df_current.columns = [group_on, chart_type]
    df_prev.columns = [group_on, chart_type]    

    if chart_type[-1] == '%' or chart_type == 'Avg Work Interruption' or chart_type == 'Victim Age':
        curr_value = df_current[chart_type].mean()
        prev_value = df_prev[chart_type].mean()
    else:
        curr_value = df_current[chart_type].sum()
        prev_value = df_prev[chart_type].sum()
    diff_percent = (curr_value - prev_value) / prev_value * 100

    return df_groupby, curr_value, prev_value, diff_percent


def create_figure(df_x,
                  df_y,
                  value,
                  reference,
                  chart_type):
    """
    Get plotted figure for and indicator.
    
    Parameters
    ----------
    df_x : Series
        X axis data
    df_y : Series
        Y axis data
    value : float
        Value for selected period
    reference: float
        Value for reference period
    chart_type : str
        KPI to calculate and use

    Returns
    -------
    fig 
        Created figure
    """

    prefix = ''
    if chart_type[-1] == '%':
        #value *= 100
        suffix = '%'
    elif chart_type == 'Avg Work Interruption' or chart_type == 'Total Work Interruption':
        suffix = ' d'
    else:
        suffix = ''
    if chart_type[:2] == 'Nb' or chart_type == 'Total Work Interruption':
        valueformat_2 = ''
    else:
        valueformat_2 = '.2s'

    if chart_type in ['Avg Work Interruption', 'Total Work Interruption']:
        fig = go.Figure(
            go.Scatter(
                x=df_x,
                y=df_y,
                mode='lines',
                #fill='tozeroy',
                line_color='#E8E8E8',
                name='',
                text=[(f'<b>{str(calendar.month_abbr[x.month])+" "+str(x.year)}:</b> {prefix}{value_format(y)}{suffix}')
                      for x,y in zip(df_x, df_y)],
                hovertemplate='Last 24 months evolution.<br>%{text}',
            )
        )
    elif chart_type[:2] != 'Nb':
        fig = go.Figure(
            go.Bar(
                x=df_x,
                y=df_y,
                marker_color='#E8E8E8',
                name='',
                text=[(f'<b>{str(calendar.month_abbr[x.month])+" "+str(x.year)}:</b> {prefix}{value_format(y)}{suffix}')
                      for x,y in zip(df_x, df_y)],
                hovertemplate='Last 24 months evolution.<br>%{text}',
            )
        )
    else:
        fig = go.Figure(
            go.Scatter(
                x=df_x,
                y=df_y,
                mode='lines',
                fill='tozeroy',
                line_color='#E8E8E8',
                name='',
                text=[(f'<b>{str(calendar.month_abbr[x.month])+" "+str(x.year)}:</b> {prefix}{value_format(y)}{suffix}')
                      for x,y in zip(df_x, df_y)],
                hovertemplate='Last 24 months evolution.<br>%{text}',
            )
        )

    fig.add_trace(
        go.Indicator(
            mode='number+delta',
            value=value,  # int(value_format(value)[0]),
            title={'text': chart_type,
                   'font': {'size': 17,},
                  },
            number={'prefix': prefix,
                    'suffix': suffix,  # f'{value_format(value)[1:]}{suffix}',
                    'font': {'size': 17,},
                   },
            delta={'position': 'left',
                   'reference': reference,
                   'valueformat': valueformat_2,
                   'font': {'size': 13,},
                  },
            domain={'y': [0, 0.7], 'x': [0.25, 0.75]},
        )
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


def get_indicator_plot(df,
                       current_year,
                       current_month,
                       chart_type,
                       performance_scope,
                       client_type=None,
                       accident_nature=None,
                       accident_status=None,
                       appeal_status=None,
                       datefield='Accident Occurrence Date'):
    """
    Plot an indicator chart.
    
    Parameters
    ----------
    df : dataframe
        Data
    current_year : int
        Current year filter
    current_month : int
        Current month filter
    chart_type : str
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
    datefield : datetime, optional
        Date field in the data (default 'Accident Occurrence Date')

    Returns
    -------
    fig 
        Created figure
    """

    prev_year, prev_month = prev(current_year, current_month, performance_scope)
    df_filtered = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    df_1, dim_1, dim_2, diff = get_current_and_prev_data(df_filtered, current_year, current_month, chart_type, performance_scope)
    df_x = df_1[datefield]
    df_y = df_1[chart_type]

    fig = create_figure(df_x, df_y, dim_1, dim_2, chart_type)

    fig.update_layout(
        xaxis={'showgrid': False,
               'showticklabels': False},
        yaxis={'showgrid': False,
               'showticklabels': False},
        plot_bgcolor='#FFFFFF',
        xaxis_title=f"<b>{'+' if diff > 0 else ''}{value_format(diff)}%</b> vs {calendar.month_abbr[prev_month]}-{prev_year}",
        xaxis_title_font={'color': 'grey',
                          'size': 12,
                         },
        margin=dict(l=0, r=0, b=0, t=15),
        autosize=True,
    )

    return fig


def get_bar_chart_and_line(df,
                           current_year,
                           current_month,
                           chart_type,
                           performance_scope,
                           client_type=None,
                           accident_nature=None,
                           accident_status=None,
                           appeal_status=None,
                           palette=palette,
                           datefield='Accident Occurrence Date'):
    """
    Plot a bar chart with a line.
    
    Parameters
    ----------
    df : dataframe
        Data
    current_year : int
        Current year filter
    current_month : int
        Current month filter
    chart_type : str
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

    # DATA
    df_filtered = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    df_current, _, _, _ = get_current_and_prev_data(
        df_filtered, current_year, current_month, chart_type, performance_scope, n_months=12)
    df_current = df_current.iloc[1:, ].reset_index(drop=True)
    if performance_scope == 'Year-to-Date: Current Year vs Previous Year':
        df_current[chart_type] = df_current[chart_type].cumsum()
        if chart_type[-1] == '%' or chart_type == 'Avg Work Interruption' or chart_type == 'Victim Age':
            df_current[chart_type] = df_current[chart_type] / pd.Series(np.arange(1, len(df_current)+1), df_current.index)

    df_prev, _, _, _ = get_current_and_prev_data(
        df_filtered, current_year-1, current_month, chart_type, performance_scope, n_months=12)
    df_prev = df_prev.iloc[1:, ].reset_index(drop=True)
    if performance_scope == 'Year-to-Date: Current Year vs Previous Year':
        df_prev[chart_type] = df_prev[chart_type].cumsum()
        if chart_type[-1] == '%' or chart_type == 'Avg Work Interruption' or chart_type == 'Victim Age':
            df_prev[chart_type] = df_prev[chart_type] / pd.Series(np.arange(1, len(df_prev)+1), df_prev.index)

    df_current['Month'], df_prev['Month'] = df_current[datefield].dt.month, df_prev[datefield].dt.month
    df_current[datefield] = df_current[datefield].apply(lambda x: f'{calendar.month_abbr[x.month]} {str(x.year)}')
    df_current.columns = [datefield, chart_type, 'Month']
    df_prev[datefield] = df_prev[datefield].apply(lambda x: f'{calendar.month_abbr[x.month]} {str(x.year)}')
    df_prev.columns = [datefield, f'{chart_type} prev', 'Month']

    df_groupby = pd.merge(df_current, df_prev, how='inner', on='Month')
    df_groupby.columns = [datefield, f'{chart_type}', 'Month', datefield+' prev', f'{chart_type} prev']
    
    # COLORING
    df_groupby[f'quantiles_{chart_type}'] = pd.cut(df_groupby[chart_type], bins=len(palette), labels=[key for key in palette.keys()])
    df_groupby[f'quantiles_{chart_type}'] = df_groupby[f'quantiles_{chart_type}'].map(lambda x: palette[x])

    df_x = df_groupby[datefield].values
    df_x_prev = df_groupby[datefield+' prev'].values
    df_y = df_groupby[chart_type].values.T
    df_y_prev = df_groupby[f'{chart_type} prev'].values.T
    
    prefix = ''
    if chart_type[-1] == '%':
        suffix = '%'
    elif chart_type == 'Avg Work Interruption' or chart_type == 'Total Work Interruption':
        suffix = ' d'
    else:
        suffix = ''

    # PLOTTING
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df_x,
            y=df_y,
            name=str(current_year),
            cliponaxis=False,
            text=[(f'{prefix}{value_format(y)}{suffix}') for y in df_y],
            textposition='outside',
            textfont_color=df_groupby[f'quantiles_{chart_type}'],
            marker_color=df_groupby[f'quantiles_{chart_type}'],
            marker_line={
                'color': df_groupby[f'quantiles_{chart_type}'],
                'width': 1,
            },
            orientation='v',
            hovertemplate='%{text}',
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_x,
            y=df_y_prev,
            name=str(current_year-1),
            mode='lines',
            line_color='grey',
            cliponaxis=False,
            text=[(f'<b>{x}:</b> {prefix}{value_format(y)}{suffix}') for x,y in zip(df_x_prev, df_y_prev)],
            hovertemplate='%{text}',
        )
    )

    fig.update_yaxes(showticklabels=False, )

    fig.update_layout(
        font_color='Grey',
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        autosize=True,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=25,
                    # pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family,
    )

    return fig


def get_horizontal_bar_chart(df,
                             current_year,
                             current_month,
                             chart,
                             performance_scope,
                             top,
                             by,
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
    top : str
        KPI used as a Y axis to group by
    by : str
        KPI used for sorting lower bar charts
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
    
    main_kpis = ['Nb of Accidents', 'Work Accidents %', 'Serious Accidents %', 'Accidents with Work Interruption %']

    # DATA
    prev_year, prev_month = prev(current_year, current_month, performance_scope)
    df_filtered = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    if performance_scope == 'Year-to-Date: Current Year vs Previous Year':
        ytd_marker = 'YTD '
    else:
        ytd_marker = ''

    df_current, df_prev = filter_performance_scope(df_filtered, current_year, current_month, performance_scope)

    df_current_init, _, _, _ = get_current_and_prev_data(df_current, current_year, current_month, main_kpis[0], performance_scope, n_months=None, group_on=top)
    df_prev_init, _, _, _ = get_current_and_prev_data(df_prev, current_year, current_month, main_kpis[0], performance_scope, n_months=None, group_on=top)

    for chart_type in main_kpis[1:]:
        df_gb_current, _, _, _ = get_current_and_prev_data(df_current, current_year, current_month, chart_type, performance_scope, n_months=None, group_on=top)
        df_gb_prev, _, _, _ = get_current_and_prev_data(df_prev, current_year, current_month, chart_type, performance_scope, n_months=None, group_on=top)
        df_current_init = pd.merge(df_current_init, df_gb_current, how='left', on=top)
        df_prev_init = pd.merge(df_prev_init, df_gb_prev, how='left', on=top)

    df_current_sorted = df_current_init.sort_values(by=by, ascending=True)
    df_prev_sorted = df_prev_init.sort_values(by=by, ascending=True)

    # PLOTTING
    if chart == 'right':

        fig = make_subplots(
            rows=1, cols=4, start_cell="top-left",
            shared_xaxes=False,
            shared_yaxes=True,
            specs=[[{'type': 'bar'} for column in range(4)]],  # 1 list for 1 row
            horizontal_spacing=0.025,  # space between the columns
        )

        for index, chart_type in enumerate(main_kpis):
            prefix = ''
            if chart_type[-1] == '%':
                suffix = '%'
            elif chart_type == 'Avg Work Interruption' or chart_type == 'Total Work Interruption':
                suffix = ' d'
            else:
                suffix = ''

            # COLORING
            df_current_sorted[f'quantiles_{chart_type}']=pd.cut(df_current_sorted[chart_type], bins=len(palette), labels=[key for key in palette.keys()])
            df_current_sorted[f'quantiles_{chart_type}']=df_current_sorted[f'quantiles_{chart_type}'].map(lambda x: palette[x])

            fig.add_trace(
                go.Bar(
                    x=df_current_sorted[chart_type],
                    y=df_current_sorted[top],
                    name='',
                    text=[f' {prefix}{value_format(x)}{suffix} {ytd_marker}<i>(vs {prefix}{value_format(prev)}{suffix})</i>'
                          for x,prev in zip(df_current_sorted[chart_type], df_prev_sorted[chart_type])],
                    cliponaxis=False,
                    textposition='outside',
                    marker_color=df_current_sorted[f'quantiles_{chart_type}'],
                    orientation='h',
                    hovertemplate=f'<b>Month: </b>{calendar.month_abbr[current_month]} {current_year}<br><b>{top}:</b> '+'%{y}<br>'+f'<b>{chart_type}:</b>'+'%{text}'+f' <i>{calendar.month_abbr[prev_month]} {prev_year}</i>',
                ),
                row=1, col=index+1,
            ),

            fig.update_xaxes(row=1, col=index+1,
                             title=f'{chart_type}<br>Current period',
                             title_font={'color': 'grey', 'size': 12},
                             range=[0, 1.35 * df_current_sorted[chart_type].max()])  # sets the range of xaxis

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

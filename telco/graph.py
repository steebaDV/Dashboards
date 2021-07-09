import plotly.graph_objects as go
import pandas as pd
import numpy as np
import calendar
from plotly.subplots import make_subplots
import plotly.figure_factory as ff

from funcs import font_family, prev, filter_data, augment_days, value_format, get_palette
palette = get_palette()

def get_bar_chart(df, current_year, current_month, chart_type,
                  call_direction,
                  dropped_reason,
                  network,
                  phonetype
                  ):
    years = [current_year]
    months = [current_month]
    for i in range(3):
        month = months[0] - 1
        year = years[0]
        if month == 0:
            month = 12
            year -= 1
        years.insert(0, year)
        months.insert(0, month)

    df_filtered = filter_data(df, call_direction, dropped_reason, network, phonetype)

    if chart_type in ['Total Calls Hist', 'Dropped Calls Hist']:
        df_groupby = df_filtered[(df_filtered['DateTime'] >= f'{years[0]}-{months[0]}-01') & (
                df_filtered['DateTime'] <= f'{years[-1]}-{months[-1]}-31')].groupby(
            pd.Grouper(key='DateTime', freq='M')).agg(
            {chart_type[:-5]: ['sum']}).reset_index()
    else:
        df_groupby = df_filtered[(df_filtered['DateTime'] >= f'{years[0]}-{months[0]}-01') & (
                df_filtered['DateTime'] <= f'{years[-1]}-{months[-1]}-31')].groupby(
            pd.Grouper(key='DateTime', freq='M')).agg(
            {chart_type[:-5]: ['mean']}).reset_index()

    df_groupby['DateTime'] = df_groupby['DateTime'].apply(
        lambda x: f'{calendar.month_abbr[x.month]}-{str(x.year)[-2:]}'
    )

    df_x = df_groupby['DateTime'].values
    df_y = df_groupby.drop(['DateTime'], axis=1).values.T[0]
    # ADDING BARS
    bar_text = []
    for i in range(4):
        diff_text = ''
        if i != 0 and df_y[i - 1] != 0:
            difference = (df_y[i] - df_y[i - 1]) / df_y[i - 1]
            if difference > 0:
                diff_text = f'▲ +{value_format(difference)}%'
            elif difference < 0:
                diff_text = f'▼ {value_format(difference)}%'
            else:
                diff_text = '='
        value_text = f'{value_format(df_y[i])}'
        if chart_type == 'Dropped Calls % Hist':
            value_text += '%'
        elif chart_type == 'Avg Setup Time Hist':
            value_text += ' s'
        bar_text.append(f'<br>{value_text}</br>{diff_text}')

    colors = ['Maroon', 'Sandy brown', 'SteelBlue', 'SaddleBrown']
    fig = go.Figure(go.Bar(x=df_x,
                           y=df_y,
                           cliponaxis=False,

                           text=bar_text,
                           textfont={
                               'color': colors
                           },

                           textposition='outside',
                           marker={'color': colors},
                           # marker_color=df_y,  # bar color
                           # marker={'color': total_df_now[f'quantiles_{chart}'],
                           #         'line':
                           #             {'color': total_df_now[f'quantiles_{chart}'],
                           #              'width': 1
                           #              },
                           #         },
                           # hoverinfo='none', # todo - update info
                           # orientation='h',
                           hoverinfo='none',
                           )
                    )
    fig.update_yaxes(showticklabels=False, )
    fig.update_layout(

        font_color="Grey",
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        autosize=True,
        margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
                    r=0,
                    b=0,
                    t=25,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family
        # width=800,
        # height=500,
    )
    return fig


def get_vertical_bar_chart(df, current_year, current_month, chart,
                           call_direction,
                           dropped_reason,
                           network,
                           phonetype,
                           top,
                           by,
                           palette=palette
                           ):
    years = [current_year]
    months = [current_month]
    for i in range(11):
        month = months[0] - 1
        year = years[0]
        if month == 0:
            month = 12
            year -= 1
        years.insert(0, year)
        months.insert(0, month)

    df_filtered = filter_data(df, call_direction, dropped_reason, network, phonetype)

    df_groupby = df_filtered[(df_filtered['DateTime'] >= f'{years[0]}-{months[0]}-01') & (
            df_filtered['DateTime'] <= f'{years[-1]}-{months[-1]}-31')].groupby(top).agg(
        {'Total Calls': ['sum'], 'Dropped Calls': ['sum'], 'Dropped Calls %': ['mean'],
         'Avg Setup Time': ['mean']}).reset_index()
    df_groupby.columns = [top, 'Total Calls', 'Dropped Calls', 'Dropped Calls %', 'Avg Setup Time']
    df_sorted = df_groupby.sort_values(by=by, ascending=True)

    # PLOTTING
    if chart == 'right':
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

        for index, chart in enumerate(['Total Calls', 'Dropped Calls', 'Dropped Calls %', 'Avg Setup Time']):
            if chart == "Avg Setup Time":
                suffix = ' s'
            # elif chart == 'Avg Conversation Time':
            #     suffix = 'min'
            elif chart == 'Dropped Calls %':
                suffix = '%'
            else:
                suffix = ''
            # if chart == 'Dropped Calls %':
            #     palette = red_palette[:]
            # else:
            #     palette = blue_palette[:]
            # palette = [palette[index] for index in range(1, len(palette) + 1)]

            max_value = df_sorted[chart].max()
            min_value = df_sorted[chart].min()
            range_value = max_value - min_value

            quantile = list(map(round, (len(palette) - 1) * (df_sorted[chart].values - min_value) / range_value))
            fig.add_trace(
                go.Bar(
                    x=df_sorted[chart],
                    y=df_sorted[top],
                    # y=[name + ' ' for name in total_df_now[column_to_group_by]],
                    # y=y_names,
                    text=[f' {value_format(x)}{suffix}' for x in df_sorted[chart]],
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
            fig.update_xaxes(row=1, col=index + 1, range=[0, 1.35 * df_sorted[chart].max()])  # sets the range of xaxis
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
    else:
        fig = go.Figure(go.Bar(
            x=[0] * len(np.unique(df_sorted[top])),
            y=df_sorted[top],
            orientation='h',
            hoverinfo='none',
        ))

        fig.update_xaxes(
            showticklabels=False,
            range=[0, 0],  # sets the range of xaxis
            constrain="domain",  # meanwhile compresses the xaxis by decreasing its "domain"
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


def get_current_and_prev_data(current_year, current_month, df, chart_type, call_direction, dropped_reason, network,
                              phonetype):
    prev_year, prev_month, current_year, current_month = prev(current_year, current_month)

    df_filtered = filter_data(df, call_direction, dropped_reason, network, phonetype)

    df_current = df_filtered[
        (df_filtered['Current Year'] == current_year) & (df_filtered['Current Month'] == current_month)]
    df_prev = df_filtered[(df_filtered['Current Year'] == current_year - 1 * (prev_month == 'Dec')) & (
            df_filtered['Current Month'] == prev_month)]

    if chart_type:
        df_groupby = df_current.groupby(pd.Grouper(key='DateTime', freq='1D')).agg(
            {chart_type: ['sum']}).reset_index()
        df_groupby.columns = ['DateTime', chart_type]
        if chart_type[:3] == 'Avg' or chart_type == 'Calls per Cell Tower' or chart_type[-1] == '%':
            smth_current = round(df_current[chart_type].mean(), 1)
            smth_prev = round(df_prev[chart_type].mean(), 1)
            if chart_type == 'Avg Conversation Time':
                smth_current /= 60
                smth_prev /= 60
                df_groupby['Avg Conversation Time'] /= 60
        else:
            smth_current = df_current[chart_type].sum()
            smth_prev = df_prev[chart_type].sum()

        diff_percent = round((smth_current - smth_prev) / smth_prev * 100, 1)
        return df_groupby, smth_current, smth_prev, diff_percent


def create_figure(df_x, df_y, value, reference, chart_type):
    # if chart_type in ['Avg Conversation Time', 'Avg Setup Time']:
    #     valueformat_1 = "s"
    # else:
    #     valueformat_1 = ",.0f"
    # if chart_type in ['Total Calls', 'Avg Conversation Time', 'Dropped Calls']:
    #     valueformat_2 = ""
    # else:
    #     valueformat_2 = ".2s"
    if chart_type == 'Dropped Calls %':
        suffix = '%'
    elif chart_type == 'Avg Setup Time':
        suffix = ' s'
    elif chart_type == 'Avg Conversation Time':
        suffix = ' min'
    else:
        suffix = ''
    if chart_type in ['Avg Conversation Time', 'Avg Setup Time', 'Nb of Cell Towers']:
        fill = None
    else:
        fill = 'tozeroy'
    if chart_type == 'Dropped Calls':
        color = 'SaddleBrown'
    else:
        color = 'SteelBlue'
    if chart_type in ['Dropped Calls %', 'Avg Handovers']:
        fig = go.Figure(go.Bar(x=df_x,
                               y=df_y,
                               marker_color='#E8E8E8'))
    else:
        fig = go.Figure(go.Scatter(x=df_x,
                                   y=df_y,
                                   mode='lines',
                                   fill=fill,
                                   hovertemplate='<extra></extra>',

                                   line_color='#E8E8E8',
                                   ))
    value = value_format(value)
    fig.add_trace(go.Indicator(mode="number+delta",
                               value=int(value[0]),
                               title={"text": chart_type,
                                      'font': {'size': 17,
                                               'color': color
                                               },
                                      },
                               number={"suffix": f'{value[1:]}{suffix}',
                                       'font': {'size': 17,
                                                'color': color
                                                },
                                       },
                               delta={'position': 'left',
                                      'reference': reference,
                                      # 'valueformat': '',
                                      'font': {'size': 13,
                                               'color': color
                                               },
                                      },
                               domain={'y': [0, 0.7], 'x': [0.25, 0.75]}))
    return fig


def get_indicator_plot(df, current_year, current_month, chart_type, call_direction, dropped_reason, network,
                       phonetype):
    df_1, dim_1, dim_2, diff = get_current_and_prev_data(current_year, current_month, df, chart_type, call_direction,
                                                         dropped_reason, network,
                                                         phonetype)

    df_1 = augment_days(current_month, current_year, df_1)

    prev_year, prev_month, current_year, current_month = prev(current_year, current_month)

    df_x = df_1['DateTime']

    df_y = df_1[chart_type]

    fig = create_figure(df_x, df_y, dim_1, dim_2, chart_type)
    fig.update_layout(xaxis={'showgrid': False,
                             'showticklabels': False},
                      yaxis={'showgrid': False,
                             'showticklabels': False},
                      paper_bgcolor='white',
                      plot_bgcolor='white',
                      # width=800,
                      # height=500,
                      xaxis_title=f"<b>{'+' if diff > 0 else ''}{value_format(diff)}%</b> vs {prev_month}-{prev_year}",  # YTD
                      xaxis_title_font={'color': 'grey',
                                        'size': 12,
                                        },
                      margin=dict(l=0,
                                  r=0,
                                  b=0,
                                  t=15,
                                  #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                                  ),
                      autosize=True,
                      font_family=font_family
                      )
    return fig


def get_dropped_bar_chart(df, current_year, current_month, call_direction, dropped_reason, network, phonetype, palette=palette):
    prev_year, prev_month, current_year, current_month = prev(current_year, current_month)
    df_filtered = filter_data(df, call_direction, dropped_reason, network, phonetype)

    df_current = df_filtered[
        (df_filtered['Current Year'] == current_year) & (df_filtered['Current Month'] == current_month)]

    df_groupby = df_current.groupby(['Dropped Reason']).agg(
        {'Dropped Calls': ['sum']}).reset_index()

    df_groupby.columns = ['Dropped Reason', 'Dropped Calls']
    df_sorted = df_groupby.sort_values(by='Dropped Calls', ascending=True)

    sum = df_sorted['Dropped Calls'].sum()

    max_value = df_sorted['Dropped Calls'].max()
    min_value = df_sorted['Dropped Calls'].min()
    range_value = max_value - min_value

    quantile = list(map(round, (len(palette) - 1) * (df_sorted['Dropped Calls'].values - min_value) / range_value))

    fig = go.Figure(go.Bar(
        x=df_sorted['Dropped Calls'].values,
        y=df_sorted['Dropped Reason'].values,
        text=[f' {value_format(x)} ({value_format(x / sum)}%)' for x in df_sorted['Dropped Calls']],
        cliponaxis=False,
        # outside value formatting
        textposition='outside',
        marker={'color': [palette[q] for q in quantile]},
        # marker_color=products_2010['quantiles'], #bar color
        # marker={'color': total_df_now[f'quantiles_{chart}'],
        #         'line':
        #             {'color': total_df_now[f'quantiles_{chart}'],
        #              'width': 1
        #              },
        #         },
        # hoverinfo='none', # todo - update info
        orientation='h',
        hoverinfo='none',
    ))
    fig.update_xaxes(showticklabels=False, range=[0, 1.35 * df_sorted['Dropped Calls'].max()])
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
                    t=25,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family
        # width=800,
        # height=500,
    )
    return fig


def get_pie_chart(df, current_year, current_month, call_direction, dropped_reason, network, phonetype):
    prev_year, prev_month, current_year, current_month = prev(current_year, current_month)
    df_filtered = filter_data(df, call_direction, dropped_reason, network, phonetype)

    df_current = df_filtered[
        (df_filtered['Current Year'] == current_year) & (df_filtered['Current Month'] == current_month)]

    df_groupby = df_current.groupby(['Call Direction']).agg(
        {'Total Calls': ['sum']}).reset_index()
    print(df_groupby['Total Calls'])
    df_groupby.columns = ['Call Direction', 'Total Calls']
    fig = go.Figure(data=[go.Pie(
        labels=df_groupby['Call Direction'].values,
        values=df_groupby['Total Calls'].values,
        textinfo='label+percent',
        insidetextorientation='radial',
        textposition='outside',
        hole=.7
    )])
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
                    t=25,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family
        # width=800,
        # height=500,
    )
    return fig


def get_cell_towers_bar_chart(df, current_year, current_month, call_direction, dropped_reason, network, phonetype, palette=palette):
    prev_year, prev_month, current_year, current_month = prev(current_year, current_month)
    df_filtered = filter_data(df, call_direction, dropped_reason, network, phonetype)

    df_current = df_filtered[
        (df_filtered['Current Year'] == current_year) & (df_filtered['Current Month'] == current_month)]

    df_groupby = df_current.groupby(['Last Cell Tower']).agg(
        {'Total Calls': ['sum'], 'Dropped Calls': ['sum']}).reset_index()

    df_groupby.columns = ['Last Cell Tower', 'Total Calls', 'Dropped Calls %']

    df_sorted = df_groupby.sort_values(by='Dropped Calls %', ascending=True)

    fig = make_subplots(rows=1, cols=2, start_cell="top-left",
                        # subplot_titles=("Total Calls", "SALES MARGIN %", "Total Calls MARGIN",),
                        # column_titles=[f"<b>{chart.upper()}</b>" for chart in bar_charts],
                        # title_font=dict(size=15),
                        # column_widths=[0.26]*3 + [(1-0.26)/3],
                        shared_xaxes=False,
                        shared_yaxes=True,  # True?
                        specs=[[{'type': 'bar'} for column in range(2)]],  # 1 list for 1 row
                        # vertical_spacing=2,
                        horizontal_spacing=0.1,  # space between the columns
                        )

    for index, chart in enumerate(['Total Calls', 'Dropped Calls %']):
        if chart == 'Dropped Calls %':
            suffix = '%'
        else:
            suffix = ''
        # if chart == 'Dropped Calls %':
        #     palette = red_palette[:]
        # else:
        #     palette = blue_palette[:]
        # palette = [palette[index] for index in range(1, len(palette) + 1)]

        max_value = df_sorted[chart].max()
        min_value = df_sorted[chart].min()
        range_value = max_value - min_value

        quantile = list(map(round, (len(palette) - 1) * (df_sorted[chart].values - min_value) / range_value))

        fig.add_trace(
            go.Bar(
                x=df_sorted[chart],
                y=df_sorted['Last Cell Tower'],
                # y=[name + ' ' for name in total_df_now[column_to_group_by]],
                # y=y_names,
                text=[f' {value_format(x)}{suffix}' for x in df_sorted[chart]],
                cliponaxis=False,
                # outside value formatting
                textposition='outside',
                marker={"color": [palette[q] for q in quantile]},  # bar color
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
        fig.update_xaxes(showticklabels=False,
                         title_text=chart,
                         row=1, col=index + 1,
                         range=[0, 1.35 * df_sorted[chart].max()]
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
                    t=25,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family
        # width=800,
        # height=500,
    )
    return fig


def get_annotations_chart(df, current_year, current_month, call_direction, dropped_reason, network, phonetype):
    prev_year, prev_month, current_year, current_month = prev(current_year, current_month)
    df_filtered = filter_data(df, call_direction, dropped_reason, network, phonetype)

    df_current = df_filtered[
        (df_filtered['Current Year'] == current_year) & (df_filtered['Current Month'] == current_month)]

    df_current['Phone Type'] = df_current['Phone Type'].apply(lambda x: x.split()[0])

    df_groupby = df_current.groupby('Phone Type').agg(
        {'Total Calls': ['sum']}).reset_index()

    df_groupby.columns = ['Phone Type', 'Total Calls']
    df_sorted = df_groupby.sort_values(by='Total Calls', ascending=False)

    max_value = df_sorted['Total Calls'].values[0]
    min_value = df_sorted['Total Calls'].values[-1]
    range_value = max_value - min_value
    size = len(df_sorted)

    fig = go.Figure()
    for index in range(size):
        value = df_sorted['Total Calls'].values[index]
        quantile = (value - min_value) / range_value
        fig.add_annotation(x=60 * (2 - index % 3), y=50 * (index // 3),
                           text=df_sorted['Phone Type'].values[index],
                           showarrow=False,
                           opacity=0.3 + 0.7 * quantile,  # opacity: 0.3..1.0
                           font=dict(color='SteelBlue',
                                     # family="Courier New, monospace",
                                     size=15 + 15 * quantile,  # size: 15..30
                                     ),
                           )
    # fig.add_annotation(x=0, y=0, text='PHONE',
    #                    # font=dict(color='SteelBlue',
    #                    #           # family="Courier New, monospace",
    #                    #           size=10 - 2 * pos,
    #                    #           ),
    #                    )
    fig.update_xaxes(showticklabels=False, range=[-35, 150])
    fig.update_yaxes(showticklabels=False, range=[-50, 50 * ((len(df_sorted[df_sorted['Total Calls'] != 0]) - 1) // 3)])
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
                    t=25,
                    #             pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
        font_family=font_family
        # height=500,
    )
    return fig


def get_top_kpi_trends(df, month_int, year, chart,
                       call_direction='*ALL*',
                       phone_type='*ALL*',
                       network='*ALL*',
                       dropped_reason='*ALL*'
                      ):
    # params
    # month_int = 12
    # year = 2020
    # df = df
    # # kpi = 'Total Calls'
    # # kpi = 'Sales per Dropped Calls'
    # # kpi = 'Average Inventory Amount'
    # # kpi = 'Total On-Hand Amount'
    print(df.columns)

    if call_direction != '*ALL*':
        df = df[df['Call Direction'] == call_direction]
    if phone_type != '*ALL*':
        df = df[df['Phone Type'] == phone_type]
    if network != '*ALL*':
        df = df[df['Network'] == network]
    if dropped_reason != '*ALL*':
        df = df[df['Dropped Reason'] == dropped_reason]

    # Month-to-Date - 1 Year Scope
    end_year = year
    start_year = year - 1  # prev year
    prev_month_int = month_int - 1
    if month_int > 2:
        month_2_ago = month_int - 2
        year_2_ago = year
    else:
        month_2_ago = 10 + month_int
        year_2_ago = year - 1
    month_2_ago = month_int - 2 if month_int > 2 else 12 - month_int

    # 12M
    from calendar import monthrange

    _, max_days = monthrange(year, month_int)
    start_date, end_date = f'{start_year}-{month_int}-01', f'{end_year}-{month_int}-{max_days}'
    # print(start_date, end_date)
    df_12_m = df[
        df['DateTime'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates
    # len(df_12_m) # 650

    # YTD
    from calendar import monthrange

    _, max_days = monthrange(year, month_int)
    start_date, end_date = f'{year}-01-01', f'{year}-{month_int}-{max_days}'
    current_df_ytd = df[df['DateTime'].between(start_date, end_date, inclusive=True)].copy()

    start_date, end_date = f'{start_year}-01-01', f'{start_year}-{month_int}-{max_days}'
    prev_df_ytd = df[df['DateTime'].between(start_date, end_date, inclusive=True)].copy()

    if chart:
        # upper part
        if chart in ['Avg Setup Time', 'Dropped Calls %']:
            df_groupby = df_12_m.groupby(pd.Grouper(key='DateTime', freq='M')).agg({chart: ['mean']}).reset_index()
            df_groupby.columns = ['DateTime', chart]
            current_month_kpi = round(df_groupby[df_groupby['DateTime'].dt.month == month_int][chart].mean(), 1)
            prev_month_kpi = round(df_groupby[df_groupby['DateTime'].dt.month == prev_month_int][chart].mean(), 1)
            prev_year_kpi = \
                df_groupby[
                    (df_groupby['DateTime'].dt.month == month_int) & (df_groupby['DateTime'].dt.year == start_year)][
                    chart].mean()

            month_diff, year_diff = 0, 0  # handling /0 error
            if (prev_month_kpi > 0) and (prev_year_kpi > 0):
                month_diff = round((current_month_kpi - prev_month_kpi) / prev_month_kpi * 100,
                                   1)  # current month - prev month %
                year_diff = round((current_month_kpi - prev_year_kpi) / prev_year_kpi * 100,
                                  1)  # current month - prev year month %
            current_ytd_grouped = current_df_ytd.groupby(pd.Grouper(key='DateTime', freq='M')).agg(
                {chart: ['mean']}).reset_index()
            current_ytd_grouped.columns = ['DateTime', chart]

            # prev ytd
            prev_ytd_grouped = prev_df_ytd.groupby(pd.Grouper(key='DateTime', freq='M')).agg(
                {chart: ['mean']}).reset_index()
            prev_ytd_grouped.columns = ['DateTime', chart]

            current_ytd_grouped_last3 = current_ytd_grouped[
                current_ytd_grouped['DateTime'].between(
                    f'{year_2_ago}-{month_2_ago}-1',
                    f'{year}-{month_int}-{max_days}',
                    inclusive=True)
            ].copy()

            prev_ytd_grouped_last3 = prev_ytd_grouped[
                prev_ytd_grouped['DateTime'].between(
                    f'{year_2_ago}-{month_2_ago}-1',
                    f'{year}-{month_int}-{max_days}',
                    inclusive=True)
            ].copy()
            current_ytd_kpi = round(current_ytd_grouped[chart].mean(), 1)
            prev_ytd_kpi = round(prev_ytd_grouped[chart].mean(), 1)

            current_ytd_kpi_last3 = round(current_ytd_grouped[chart].mean(), 1)
            prev_ytd_kpi_last3 = round(prev_ytd_grouped[chart].mean(), 1)

            ytd_diff = 0
            if (prev_ytd_kpi > 0):
                ytd_diff = round((current_ytd_kpi - prev_ytd_kpi) / prev_ytd_kpi * 100, 1)
        else:
            df_groupby = df_12_m.groupby(pd.Grouper(key='DateTime', freq='M')).agg({chart: ['sum']}).reset_index()
            df_groupby.columns = ['DateTime', chart]
            current_month_kpi = df_groupby[df_groupby['DateTime'].dt.month == month_int][chart].sum()
            prev_month_kpi = df_groupby[df_groupby['DateTime'].dt.month == prev_month_int][chart].sum()
            prev_year_kpi = \
                df_groupby[
                    (df_groupby['DateTime'].dt.month == month_int) & (df_groupby['DateTime'].dt.year == start_year)][
                    chart].sum()

            month_diff, year_diff = 0, 0  # handling /0 error
            if (prev_month_kpi > 0) and (prev_year_kpi > 0):
                month_diff = round((current_month_kpi - prev_month_kpi) / prev_month_kpi * 100,
                                   1)  # current month - prev month %
                year_diff = round((current_month_kpi - prev_year_kpi) / prev_year_kpi * 100,
                                  1)  # current month - prev year month %
            current_ytd_grouped = current_df_ytd.groupby(pd.Grouper(key='DateTime', freq='M')).agg(
                {chart: ['sum']}).reset_index()
            current_ytd_grouped.columns = ['DateTime', chart]
            current_ytd_grouped['cumsum'] = current_ytd_grouped[chart].cumsum()
            # prev ytd
            prev_ytd_grouped = prev_df_ytd.groupby(pd.Grouper(key='DateTime', freq='M')).agg(
                {chart: ['sum']}).reset_index()
            prev_ytd_grouped.columns = ['DateTime', chart]
            prev_ytd_grouped['cumsum'] = prev_ytd_grouped[chart].cumsum()

            current_ytd_grouped_last3 = current_ytd_grouped[
                current_ytd_grouped['DateTime'].between(
                    f'{year_2_ago}-{month_2_ago}-1',
                    f'{year}-{month_int}-{max_days}',
                    inclusive=True)
            ].copy()

            prev_ytd_grouped_last3 = prev_ytd_grouped[
                prev_ytd_grouped['DateTime'].between(
                    f'{year_2_ago}-{month_2_ago}-1',
                    f'{year}-{month_int}-{max_days}',
                    inclusive=True)
            ].copy()

            current_ytd_kpi = current_ytd_grouped[chart].sum()
            prev_ytd_kpi = prev_ytd_grouped[chart].sum()

            current_ytd_kpi_last3 = current_ytd_grouped_last3[chart].sum()
            prev_ytd_kpi_last3 = prev_ytd_grouped_last3[chart].sum()

            ytd_diff = 0
            if (prev_ytd_kpi > 0):
                ytd_diff = round((current_ytd_kpi - prev_ytd_kpi) / prev_ytd_kpi * 100, 1)

        # lower part
        # current ytd

        # f'{prev_ytd_kpi:,}', f'{current_ytd_kpi:,}'

    fig = make_subplots(rows=2, cols=1, start_cell="top-left",
                        # subplot_titles=("Total Calls", "SALES MARGIN %", "Total Calls MARGIN",),
                        # column_titles=[f"<b>{chart}</b>" for chart in bar_charts],
                        shared_xaxes=False,  # ! step-like bars
                        shared_yaxes=False,
                        # vertical_spacing=2,
                        horizontal_spacing=0.03,  # space between the columns
                        vertical_spacing=0.3,
                        )

    # 2 ROWS
    if chart == 'Dropped Calls %':
        fig.add_trace(
            go.Bar(x=df_groupby['DateTime'],  # +-1/2 day difference
                   y=df_groupby[chart],
                   cliponaxis=False,
                   marker={'color': 'darkgray'},
                   # marker_color=df_y,  # bar color
                   # marker={'color': total_df_now[f'quantiles_{chart}'],
                   #         'line':
                   #             {'color': total_df_now[f'quantiles_{chart}'],
                   #              'width': 1
                   #              },
                   #         },
                   # hoverinfo='none', # todo - update info
                   # orientation='h',
                   hoverinfo='none',
                   ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Bar(x=current_ytd_grouped_last3['DateTime'],
                   y=current_ytd_grouped_last3[chart],
                   cliponaxis=False,
                   marker={'color': 'darkgray'},
                   # marker_color=df_y,  # bar color
                   # marker={'color': total_df_now[f'quantiles_{chart}'],
                   #         'line':
                   #             {'color': total_df_now[f'quantiles_{chart}'],
                   #              'width': 1
                   #              },
                   #         },
                   # hoverinfo='none', # todo - update info
                   # orientation='h',
                   hoverinfo='none',
                   ),
            row=2,
            col=1,
        )
    else:
        fig.add_trace(
            go.Scatter(x=df_groupby['DateTime'],  # +-1/2 day difference
                       y=df_groupby[chart],
                       mode='lines',
                       fill=None if chart == 'Avg Setup Time' else 'tozeroy',
                       hovertemplate='<extra></extra>',
                       line_color='darkgray',  # #E8E8E8
                       ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=current_ytd_grouped_last3['DateTime'],
                       y=current_ytd_grouped_last3[chart] if chart == 'Avg Setup Time' else current_ytd_grouped_last3[
                           'cumsum'],
                       mode='lines',
                       fill=None if chart == 'Avg Setup Time' else 'tozeroy',
                       hovertemplate='<extra></extra>',
                       line_color='darkgray',  # #E8E8E8
                       ),
            row=2,
            col=1,
        )
    # fig.add_trace(
    #     go.Scatter(x=df_groupby['DateTime'],  # +-1/2 day difference
    #                y=df_groupby[chart].mean(),
    #                mode='lines',
    #                fill=None if chart == 'Avg Setup Time' else 'tozeroy',
    #                hovertemplate='<extra></extra>',
    #                line_color='Cyan',  # #E8E8E8
    #                ),
    #     row=1,
    #     col=1,
    # )
    # UPDATE AXES FOR EACH ROW
    # ROW 1
    fig.update_xaxes(
        showline=False,
        showgrid=False,
        showticklabels=True,
        dtick="M1",
        tickformat="%b-%y",
        tickfont=dict(size=8,  # customize tick size
                      # color='default',
                      ),
        ticks='',  # |
        tickangle=45,
        row=1, col=1,
    )

    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
        row=1, col=1,
    )
    fig.update_xaxes(
        nticks=6,
        row=1, col=1,
    )

    # ROW 2
    fig.update_xaxes(
        nticks=3,
        showline=False,
        showgrid=False,
        showticklabels=True,
        dtick="M1",
        tickformat="%b",
        tickfont=dict(size=9,  # customize tick size
                      # color='default',
                      ),
        ticks='',  # |
        tickangle=0,
        row=2, col=1,
    )

    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
        row=2, col=1,
    )

    # UPPER
    # KPI
    if chart == "Avg Setup Time":
        suffix = ' s'
    elif chart == 'Dropped Calls %':
        suffix = '%'
    else:
        suffix = ''

    fig.add_annotation(text=f"<b>{current_month_kpi:,}{suffix}</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=18,
                           #  color="black"
                       ),
                       x=0.01, y=1, showarrow=False)
    # DIFF
    fig.add_annotation(text=f"<b>▲ {value_format(month_diff)}%</b>" if month_diff > 0 else f"<b>▼ {value_format(month_diff)}%</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=14,
                           color="royalblue"
                       ),
                       x=0.35, y=0.97, showarrow=False)

    fig.add_annotation(text=f"<b>▲ {value_format(year_diff)}%</b>" if year_diff > 0 else f"<b>▼ {value_format(year_diff)}%</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=14,
                           color="royalblue"
                       ),
                       x=0.7, y=0.97, showarrow=False)

    # LOWER
    # KPI

    fig.add_annotation(text=f"<b>{value_format(current_ytd_kpi)}{suffix}</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=18,
                           #  color="black"
                       ),
                       x=0.01, y=0.5, showarrow=False)
    # DIFF
    fig.add_annotation(text=f"<b>▲ {value_format(ytd_diff)}%</b>" if ytd_diff > 0 else f"<b>▼ {value_format(ytd_diff)}%</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=14,
                           color="royalblue"
                       ),
                       x=0.7, y=0.455, showarrow=False)

    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        autosize=True,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=20,
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


# call_direction=None,
#                         reason=None,
#                         network=None,
#                         phone_type=None,
def get_heatmap(df,
                dimension,  # looks like 'dimension1 x dimension2'
                kpi,
                palette=palette,
                dates=None,
                call_direction=None,
                reason=None,
                network=None,
                phone_type=None,
                last_cell_tower=None):
    # CURRENCY KPIs
    dollar_kpis = ['Total Sales',
                   'Sales per reason',
                   'Average Inventory Amount',
                   'Total On-Hand Amount',
                   'Average Selling Price',
                   'Average On-hand Price',
                   ]

    # FILTERS
    # TO-DO: more options for dates
    if dates:
        # last n months
        if dates.split()[0] == 'last' and dates.split()[2] == 'months':
            n = int(dates.split()[1])
            start = df['DateTime'].max() - pd.DateOffset(months=n)
            df = df[df['DateTime'] >= start]
        # last n years
        if dates.split()[0] == 'last' and dates.split()[2] == 'years':
            n = int(dates.split()[1])
            df = df[df['Current Year'] > (df['Current Year'].max() - n)]
    if reason != '*ALL*':
        df = df[df['Dropped Reason'] == reason]
    if phone_type != '*ALL*':
        df = df[df['Phone Type'] == phone_type]
    if call_direction != '*ALL*':
        df = df[df['Call Direction'] == call_direction]
    if network != '*ALL*':
        df = df[df['Network'] == network]
    if last_cell_tower:
        df = df[df['Last Cell Tower'] == last_cell_tower]
    dimension1, dimension2 = dimension.split(' x ')

    # DATA

    if dimension1 == 'Year':
        df[dimension1] = df['DateTime'].dt.year
    elif dimension1 == 'Month':
        df[dimension1] = df['DateTime'].dt.month_name()
        df[f'{dimension1} optional'] = df['DateTime'].dt.month
    elif dimension1 == 'Week':
        df[dimension1] = 'w' + df['DateTime'].dt.isocalendar().week.astype('str')
        df[f'{dimension1} optional'] = df['DateTime'].dt.isocalendar().week
    elif dimension1 == 'Day of Week':
        df[dimension1] = df['DateTime'].dt.day_name()
        df[f'{dimension1} optional'] = df['DateTime'].dt.dayofweek

    if dimension2 == 'Quarter':
        df[dimension2] = 'Q' + df['DateTime'].dt.quarter.astype('str')
    elif dimension2 == 'Month':
        df[dimension2] = df['DateTime'].dt.month_name()
        df[f'{dimension2} optional'] = df['DateTime'].dt.month
    elif dimension2 == 'Week':
        df[dimension2] = 'w' + df['DateTime'].dt.isocalendar().week.astype('str')
        df[f'{dimension2} optional'] = df['DateTime'].dt.isocalendar().week
    elif dimension2 == 'Day of Year':
        df[dimension2] = df['DateTime'].dt.dayofyear
    elif dimension2 == 'Day of Month':
        df[dimension2] = df['DateTime'].dt.day
    elif dimension2 == 'Day of Week':
        df[dimension2] = df['DateTime'].dt.day_name()
        df[f'{dimension2} optional'] = df['DateTime'].dt.dayofweek
    elif dimension2 == 'Hour':
        df[dimension2] = df['DateTime'].dt.hour

    # DATA - RIGHT BAR CHART - dimension1
    if dimension1 in ['Month', 'Week', 'Day of Week']:
        df1 = df.groupby([dimension1, f'{dimension1} optional']).agg({kpi: ['sum']}).reset_index()
        df1.columns = [dimension1, f'{dimension1} optional', kpi]
        df1 = df1.sort_values(by=f'{dimension1} optional', ascending=True)
        df1.drop(f'{dimension1} optional', axis=1, inplace=True)
    else:
        df1 = df.groupby(dimension1).agg({kpi: ['sum']}).reset_index()
        df1.columns = [dimension1, kpi]
        df1 = df1.sort_values(by=dimension1, ascending=True)
    df1 = df1.reset_index(drop=True)

    # DATA - TOP BAR CHART - dimension2
    if dimension2 in ['Month', 'Week', 'Day of Week']:
        df2 = df.groupby([dimension2, f'{dimension2} optional']).agg({kpi: ['sum']}).reset_index()
        df2.columns = [dimension2, f'{dimension2} optional', kpi]
        df2 = df2.sort_values(by=f'{dimension2} optional', ascending=True)
        df2.drop(f'{dimension2} optional', axis=1, inplace=True)
    else:
        df2 = df.groupby(dimension2).agg({kpi: ['sum']}).reset_index()
        df2.columns = [dimension2, kpi]
        df2 = df2.sort_values(by=dimension2, ascending=True)
    df2 = df2.reset_index(drop=True)

    # DATA - HEATMAP
    if dimension == 'Week x Day of Week':
        df3 = df.groupby([f'{dimension2} optional', f'{dimension1} optional']).agg({kpi: ['sum']}).reset_index()
        df3.columns = [f'{dimension2} optional', f'{dimension1} optional', kpi]
        df3 = df3.pivot(index=f'{dimension1} optional', columns=f'{dimension2} optional', values=kpi)
        df3.index = df1[dimension1].unique()
        df3.columns = df2[dimension2].unique()
    if dimension != 'Week x Day of Week' and dimension1 in ['Month', 'Week', 'Day of Week']:
        df3 = df.groupby([dimension2, f'{dimension1} optional']).agg({kpi: ['sum']}).reset_index()
        df3.columns = [dimension2, f'{dimension1} optional', kpi]
        df3 = df3.pivot(index=f'{dimension1} optional', columns=dimension2, values=kpi)
        df3.index = df1[dimension1].unique()
    if dimension != 'Week x Day of Week' and dimension2 in ['Month', 'Week', 'Day of Week']:
        df3 = df.groupby([f'{dimension2} optional', dimension1]).agg({kpi: ['sum']}).reset_index()
        df3.columns = [f'{dimension2} optional', dimension1, kpi]
        df3 = df3.pivot(index=dimension1, columns=f'{dimension2} optional', values=kpi)
        df3.columns = df2[dimension2].unique()
    if dimension1 not in ['Month', 'Week', 'Day of Week'] and dimension2 not in ['Month', 'Week', 'Day of Week']:
        df3 = df.groupby([dimension2, dimension1]).agg({kpi: ['sum']}).reset_index()
        df3.columns = [dimension2, dimension1, kpi]
        df3 = df3.pivot(index=dimension1, columns=dimension2, values=kpi)

    # COLORING
    palette2 = {}
    for i, c in zip(range(len(palette)), palette):
        palette2[i+1] = c
    df1[f'quantiles_{kpi}'] = pd.cut(df1[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    df1[f'quantiles_{kpi}'] = df1[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    df2[f'quantiles_{kpi}'] = pd.cut(df2[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    df2[f'quantiles_{kpi}'] = df2[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()

    # PLOTTING
    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.7, 0.3],
        row_heights=[0.3, 0.7],
        horizontal_spacing=0.01,
    )  # print_grid=True)

    # TOP Vertical Bar Chart for kpi + dimension2
    fig.add_trace(
        go.Bar(
            x=df2[dimension2],
            y=df2[kpi],
            name='',
            text=[(f'{value_format(x)}') if kpi in dollar_kpis else (f'{value_format(x)}') for x in df2[kpi]],
            textposition='outside',
            marker_color=df2[f'quantiles_{kpi}'],
            marker_line={
                'color': df2[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='v',
            hovertemplate=f'{dimension2}:' + ' %{x}<br>' + f'{kpi}:' + '%{text}',
        ),
        row=1, col=1,
    )

    # RIGHT Horizontal Bar Chart for kpi + dimension1
    fig.add_trace(
        go.Bar(
            x=df1[kpi],
            y=df1[dimension1],
            name='',
            text=[(f' {value_format(x)}') if kpi in dollar_kpis else (f' {value_format(x)}') for x in df1[kpi]],
            textposition='outside',
            marker_color=df1[f'quantiles_{kpi}'],
            marker_line={
                'color': df1[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='h',
            hovertemplate=f'{dimension1}:' + ' %{y}<br>' + f'{kpi}:' + '%{text}',
        ),
        row=2, col=2,
    )

    # HEATMAP
    hm = ff.create_annotated_heatmap(
        z=df3.values,
        x=list(df3.columns),
        y=list(df3.index),
        name='',
        annotation_text=[[(f' {value_format(x)}') if kpi in dollar_kpis else (f' {value_format(x)}') for x in row] for row in
                         df3.values],
        # font_colors = ['black', 'black'],
        hovertemplate=f'{dimension1}:' + ' %{y}<br>' + f'{dimension2}:' + ' %{x}<br>' + f'{kpi}:' + ' %{z:,.0f}',
        hoverongaps=False,
        colorscale=list(palette2.values()),
        showscale=False,
    )
    fig.add_trace(
        hm.data[0],
        row=2, col=1,
    )

    # TO-DO: Add annotations to heatmap
    # annot_bars = list(fig.layout.annotations)
    # annot_hm = list(hm.layout.annotations)
    # for k in range(len(annot_hm)):
    #     annot_hm[k]['xref'] = 'x3'
    #     annot_hm[k]['yref'] = 'y3'
    # # fig.update_layout(
    # #     annotations=annot_bars+annot_hm
    # # )
    # fig.layout.annotations += tuple(annot_hm)

    # Update X axis
    fig.update_xaxes(
        zeroline=False,
        showline=False,
        showgrid=False,
        showticklabels=False,
        dtick='M1',
        # tickformat='%b\n%Y',
        ticks='',
        tickangle=0,
        type='category',
        row=1, col=1,
    )

    fig.update_xaxes(
        zeroline=False,
        showline=False,
        showgrid=False,
        showticklabels=False,
        dtick='M1',
        # tickformat='%b\n%Y',
        ticks='',
        tickangle=0,
        range=[0, df1[kpi].max() + (df1[kpi].max() * 0.2)],
        row=2, col=2,
    )

    fig.update_xaxes(
        type='category',
        showticklabels=True,
        side='top',
        row=2, col=1,
    )

    # Update Y axis
    fig.update_yaxes(
        showticklabels=False,
        range=[0, df2[kpi].max() + (df2[kpi].max() * 0.2)],
        row=1, col=1,
    )

    fig.update_yaxes(
        showticklabels=False,
        type='category',
        row=2, col=2,
    )

    fig.update_yaxes(
        type='category',
        row=2, col=1,
    )

    # UPDATE TITLE FONT
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=12, )

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        autosize=True,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=25,
                    # pad=0  # Sets the amount of padding (in px) between the plotting area and the axis lines
                    ),
    )

    # SET FONT
    fig.update_layout(autosize=True,
                      font={
                          'family': font_family,
                          'color': 'black',
                          'size': 12
                      },
                      )

    return fig

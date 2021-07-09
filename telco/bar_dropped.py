from clickhouse_driver import Client
import pandas as pd
import plotly.graph_objects as go
import calendar

from funcs import augment_days, grey_palette, font_family, get_palette, value_format

palette = get_palette()


def get_bar_charts_h(month_int, year, df,
                     column_to_group_by,
                     max_bars, bar_charts,
                     palette=palette,
                     column_widths=None,
                     call_direction=None,
                     phone_type=None,
                     network=None,
                     dropped_reason=None, ):
    palette = {index + 1: color for index, color in enumerate(palette)}
    month_name = calendar.month_name[month_int]
    previous_year = year - 1
    # ADD LINES
    '''Total Sales = SUM Total Sales'''
    # NOW
    df_month_now = df[(df['DateTime'].dt.month == month_int) & (df['DateTime'].dt.year == year)].copy()

    if call_direction != '*ALL*':
        df_month_now = df_month_now[df_month_now['Call Direction'] == call_direction]
    if phone_type != '*ALL*':
        df_month_now = df_month_now[df_month_now['Phone Type'] == phone_type]
    if network != '*ALL*':
        df_month_now = df_month_now[df_month_now['Network'] == network]
    if dropped_reason != '*ALL*':
        df_month_now = df_month_now[df_month_now['Dropped Reason'] == dropped_reason]

    total_df_now = df_month_now.groupby([column_to_group_by]).agg(
        {'Total Calls': ['sum'], 'Dropped Calls': ['sum']}).reset_index()
    total_df_now.columns = [column_to_group_by, 'Total Calls', 'Dropped Calls']

    '''Dropped Calls %  = (SUM Dropped Calls / SUM Total Calls)*100'''
    total_df_now['Dropped Calls %'] = round((total_df_now['Dropped Calls'] / total_df_now[
        'Total Calls']) * 100, 2)

    total_df_now = total_df_now.sort_values(by='Total Calls', ascending=False).head(max_bars)

    # CALCULATE GREY LINES  - AVG FOR THE PAST 12 MONTH
    from calendar import monthrange
    _, max_days = monthrange(year, month_int - 1)  # not including the current month
    start_date, end_date = f'{previous_year}-{month_int}-01', f'{year}-{month_int - 1}-{max_days}'
    # print(start_date, end_date)  # 2010-7-01 2011-6-30
    df_12_m = df[
        df['DateTime'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates

    total_df_12_m = df_12_m.groupby([column_to_group_by]).agg(
        {'Total Calls': ['sum'], 'Dropped Calls': ['sum']}).reset_index()
    total_df_12_m.columns = [column_to_group_by, 'Total Calls', 'Dropped Calls']
    total_df_12_m['Dropped Calls %'] = round((total_df_12_m['Dropped Calls'] / total_df_12_m['Total Calls']) * 100, 2)
    total_df_12_m['Total Calls'] = total_df_12_m['Total Calls'] / 12
    total_df_12_m['Dropped Calls'] = total_df_12_m['Dropped Calls'] / 12

    # JOIN ON THE COMMON COLUMN
    total_df_now = total_df_now.merge(total_df_12_m, on=column_to_group_by, how='left')  # total_df_now =
    total_df_now.columns = [column_to_group_by, 'Total Calls', 'Dropped Calls', 'Dropped Calls %',
                            'Total Calls_avg', 'Dropped Calls_avg', 'Dropped Calls %_avg']

    # BINNING AND MAPPING BY COLOR
    # TOTAL SALES
    total_df_now['quantiles_Total Calls'] = pd.cut(total_df_now['Total Calls'], bins=len(palette),
                                                   labels=[key for key in palette.keys()])
    total_df_now['quantiles_Total Calls'] = total_df_now['quantiles_Total Calls'].map(lambda x: palette[x])

    # SALES MARGIN %
    total_df_now['quantiles_Dropped Calls %'] = pd.cut(total_df_now['Dropped Calls %'], bins=len(grey_palette),
                                                       labels=[key for key in grey_palette.keys()])
    total_df_now['quantiles_Dropped Calls %'] = total_df_now['quantiles_Dropped Calls %'].map(lambda x: grey_palette[x])

    # TOTAL SALES MARGIN
    total_df_now['quantiles_Dropped Calls'] = pd.cut(total_df_now['Dropped Calls'], bins=len(palette),
                                                     labels=[key for key in palette.keys()])
    total_df_now['quantiles_Dropped Calls'] = total_df_now['quantiles_Dropped Calls'].map(
        lambda x: palette[x])

    # PLOTTING
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=len(bar_charts), start_cell="top-left",
                        # subplot_titles=("TOTAL CALLS", "DROPPED CALLS %", "DROPPED CALLS",),
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
    y_names = [name + ' ' for name in total_df_now[column_to_group_by]]
    y_names.reverse()  # update_yaxes - ticktext
    # print(y_names)

    # 1st for loop
    num = 0
    for chart in bar_charts:  # Total Sales, Sales Margin %
        num += 1
        # print(f'chart: {chart}, num: {num}')
        # ADDING BARS
        fig.add_trace(
            go.Bar(
                x=total_df_now[chart],
                # y=[name + ' ' for name in total_df_now[column_to_group_by]],
                # y=y_names,
                text=[(f' {value_format(x)}%' if chart == 'Dropped Calls %' else f'{value_format(x)}') for x in total_df_now[chart]],
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
        line_colors = {'Total Calls': '#778899', 'Dropped Calls %': '#F89C74', 'Dropped Calls': '#778899'}
        y_line = [y for y in range(len(total_df_now))]
        y_line.reverse()
        # chart = 'Total Sales Margin'
        # print(f'y_line: {y_line}')

        x_line = []
        if chart == 'Total Calls':
            x_line = total_df_now[f'{chart}_avg'].tolist()
            x_line.reverse()
        elif chart == 'Dropped Calls %':
            x_line = total_df_now[f'{chart}_avg'].tolist()
            # x_target = [x - x * .1 if int(x) % 2 == 0 else x + x * .2 for x in total_df_now['Sales Margin %']];
            x_line.reverse()
        elif chart == 'Dropped Calls':
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
        coef = {'Total Calls': 1.21, 'Dropped Calls %': 1.85, 'Dropped Calls': 1.2}
        x_max = total_df_now[chart].max() * coef[chart]
        # print(f'chart: {coef[chart]}')
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            range=[0, x_max],  # [from value, to value]
            # tickangle=45,
            title_text=f"<b>{chart}</b><br>Current Period",
            title_font={'color': 'grey',
                        'size': 10,
                        },
            row=1, col=bar_charts.index(chart) + 1,

        )

        fig.update_yaxes(
            categoryorder='total ascending' if chart == 'Total Calls' else None,
            autorange='reversed',
            # autorange='reversed' if chart != 'Total Sales' else None,
            showgrid=False,
            showline=False,
            showticklabels=True if chart == 'Total Calls' else False,

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
        paper_bgcolor='white',
        plot_bgcolor='white',
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
                          'size': 10
                      },
                      )

    return fig


def get_hourly_statistics(month_int, year, df,
                          palette=palette,
                          column_widths=None,
                          call_direction=None,
                          phone_type=None,
                          network=None,
                          dropped_reason=None):

    palette = {index + 1: color for index, color in enumerate(palette)}

    month_name = calendar.month_name[month_int]
    previous_year = year - 1

    # FILTERS
    df_month_now = df[(df['DateTime'].dt.month == month_int) & (df['DateTime'].dt.year == year)].copy()

    if call_direction != '*ALL*':
        df_month_now = df_month_now[df_month_now['Call Direction'] == call_direction]
    if phone_type != '*ALL*':
        df_month_now = df_month_now[df_month_now['Phone Type'] == phone_type]
    if network != '*ALL*':
        df_month_now = df_month_now[df_month_now['Network'] == network]
    if dropped_reason != '*ALL*':
        df_month_now = df_month_now[df_month_now['Dropped Reason'] == dropped_reason]

    # COLUMNS SELECTION
    df_hour = df_month_now[['Total Calls', 'Dropped Calls', 'Total Handovers', 'Network']]
    df_hour['Hour'] = df_month_now['DateTime'].dt.day
    # СТРОКОЙ ВЫШЕ ЗАМЕНИТЬ ДЕНЬ НА ЧАС

    # dataframe for different networks
    total_net = df_hour.groupby(['Network', 'Hour']).agg(
        {'Dropped Calls': ['sum'],
         }).reset_index()
    total_net.columns = ['Network', 'Hour', 'Dropped Calls']

    total_df_now = df_hour.groupby(['Hour']).agg(
        {'Total Calls': ['sum'], 'Dropped Calls': ['sum'],
         'Total Handovers': ['sum'],
         }).reset_index()
    total_df_now.columns = ['Hour', 'Total Calls', 'Dropped Calls', 'Total Handovers']

    '''Dropped Calls %  = (SUM Dropped Calls / SUM Total Calls)*100'''
    total_df_now['Dropped Calls %'] = (total_df_now['Dropped Calls'] / total_df_now[
        'Total Calls']) * 100

    total_df_now = total_df_now.sort_values(by='Hour', ascending=False)
    total_net = total_net.sort_values(by='Hour', ascending=False)

    # BINNING AND MAPPING BY COLOR
    # TOTAL CALLS
    total_df_now['quantiles_Total Calls'] = pd.cut(total_df_now['Total Calls'], bins=len(palette),
                                                   labels=[key for key in palette.keys()])
    total_df_now['quantiles_Total Calls'] = total_df_now['quantiles_Total Calls'].map(lambda x: palette[x])

    # DROPPED CALLS %
    total_df_now['quantiles_Dropped Calls %'] = pd.cut(total_df_now['Dropped Calls %'], bins=len(grey_palette),
                                                       labels=[key for key in grey_palette.keys()])
    total_df_now['quantiles_Dropped Calls %'] = total_df_now['quantiles_Dropped Calls %'].map(lambda x: grey_palette[x])

    # DROPPED CALLS
    total_df_now['quantiles_Dropped Calls'] = pd.cut(total_df_now['Dropped Calls'], bins=len(palette),
                                                     labels=[key for key in palette.keys()])
    total_df_now['quantiles_Dropped Calls'] = total_df_now['quantiles_Dropped Calls'].map(lambda x: palette[x])

    # TOTAL HANDOVERS
    total_df_now['quantiles_Total Handovers'] = pd.cut(total_df_now['Total Handovers'], bins=len(grey_palette),
                                                       labels=[key for key in grey_palette.keys()])
    total_df_now['quantiles_Total Handovers'] = total_df_now['quantiles_Total Handovers'].map(lambda x: grey_palette[x])

    # PLOTTING
    from plotly.subplots import make_subplots
    import plotly.express as px

    fig = make_subplots(rows=3, cols=1, start_cell="top-left",
                        # subplot_titles=("TOTAL CALLS", "DROPPED CALLS", "DROPPED CALLS",),
                        # row_titles=[f"<b>{chart.upper()}</b>" for chart in bar_charts],
                        # title_font=dict(size=15),
                        column_widths=column_widths,
                        shared_xaxes=True,
                        shared_yaxes=False,
                        # specs=[[{'type': 'bar'} for column in range(len(bar_charts))]],  # 1 list for 1 row
                        # vertical_spacing=2,
                        vertical_spacing=0.08,  # space between the columns
                        specs=[[{'secondary_y': True}], [{"type": "scatter"}],
                               [{"type": "bar"}]],
                        )
    # ____________________________________________
    # First plot

    text_buf = []
    n_min, n_max = True, True
    for el in total_df_now['Total Calls']:
        if el == total_df_now['Total Calls'].min() and n_min:
            text_buf.append(value_format(el))
            n_min = False
        elif el == total_df_now['Total Calls'].max() and n_max:
            text_buf.append(value_format(el))
            n_max = False
        else:
            text_buf.append('')

    # text_buf = text_buf[::-1]

    fig.add_trace(
        go.Scatter(
            x=total_df_now['Hour'],
            y=total_df_now['Total Calls'],
            mode='lines+text',
            name='Total Calls',
            yaxis='y1',
            fill='tonexty',
            text=text_buf,
            # texttemplate='%{text}',
            textposition='top center',
            hoverinfo='none',
            marker={'color': total_df_now[f'quantiles_Total Calls'],
                    'line':
                        {'color': total_df_now[f'quantiles_Total Calls'],
                         'width': 0,
                         },
                    },
        ),
        row=1, col=1,
        secondary_y=False,
    )
    # fig.update_yaxes(title_text='Total Calls',
    #                  row=1, col=1, range=[0, 1.35*total_df_now['Total Calls'].max()])
    fig.update_xaxes(nticks=24)

    text_buf = []
    n_min, n_max = True, True
    for el in total_df_now['Dropped Calls %']:
        if el == total_df_now['Dropped Calls %'].min() and n_min:
            text_buf.append(value_format(el))
            n_min = False
        elif el == total_df_now['Dropped Calls %'].max() and n_max:
            text_buf.append(value_format(el))
            n_max = False
        else:
            text_buf.append('')

    # text_buf = text_buf[::-1]

    fig.add_trace(
        go.Scatter(
            x=total_df_now['Hour'],
            y=total_df_now['Dropped Calls %'],
            mode='lines+text',
            name='Dropped Calls %',
            yaxis='y2',

            text=text_buf,
            # texttemplate='%{text}',
            textposition='top center',
            hoverinfo='none',
            marker={'color': total_df_now[f'quantiles_Dropped Calls'],
                    'line':
                        {'color': total_df_now[f'quantiles_Dropped Calls'],
                         'width': 1,
                         },
                    },
        ),
        row=1, col=1,
        secondary_y=True,
    )
    fig.update_yaxes(
        # tickangle = 90,
        title_text='Total Calls',
        secondary_y=False,
        range=[0, 1.35 * total_df_now['Total Calls'].max()],
        row=1, col=1
    )
    fig.update_yaxes(title='Dropped Calls %',
                     # overlaying='y',
                     # side='right',
                     mirror=True,
                     showticklabels=True,
                     secondary_y=True,
                     row=1, col=1,
                     range=[0, 1.35 * total_df_now['Dropped Calls %'].max()],
                     )
    fig.update_traces(hoverinfo='none', )

    # _________________________________________________
    # 2
    # Scatter-plots for different networks
    for net in total_net.Network.unique():
        fig.add_trace(
            go.Scatter(
                x=total_net[total_net.Network == net]['Hour'],
                y=total_net[total_net.Network == net]['Dropped Calls'],
                mode='lines+text',

                # text=['', net] + ['' for i in range(total_net[total_net.Network == net].shape[0] - 2)],
                text=[net if index == 1 else '' for
                      index, net in enumerate(total_net[total_net.Network == net]['Network'])],
                texttemplate='%{text}',
                textposition="top left",
                hoverinfo='none',
                marker={'color': total_df_now[f'quantiles_Dropped Calls'],
                        'line':
                            {'color': total_df_now[f'quantiles_Dropped Calls'],
                             'width': 1,
                             },
                        },
            ),
            row=2, col=1,
        )
        print(total_net.Network.unique())

    fig.update_yaxes(title_text='Dropped Calls',
                     row=2, col=1, range=[0, 1.35 * total_net['Dropped Calls'].max()])
    # _________________________________________________
    # 3
    # Barchart
    fig.add_trace(
        go.Bar(
            x=total_df_now['Hour'],
            y=total_df_now['Total Handovers'],
            name='Handovers',
            text=[value_format(el) if (el == total_df_now['Total Handovers'].min() or
                         el == total_df_now['Total Handovers'].max()) else ''
                  for el in total_df_now['Total Handovers']],
            texttemplate='%{text}',
            textposition='outside',
            textangle=-90,
            marker={'color': total_df_now[f'quantiles_Total Handovers'],
                    'line':
                        {'color': total_df_now[f'quantiles_Total Handovers'],
                         'width': 1,
                         },
                    },
        ),
        row=3, col=1,
    )
    fig.update_yaxes(title_text='Total Handovers',
                     row=3, col=1, range=[0, 1.35 * total_df_now['Total Handovers'].max()]
                     )
    fig.update_traces(hoverinfo='none',
                      # hovertemplate="%{y}",
                      row=3, col=1,
                      )
    # Update Title Font
    for i in fig['layout']['annotations']:
        # print(i)
        i['font'] = dict(size=12,
                         # color='red',
                         )

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
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
                          'size': 12
                      },
                      )

    return fig


def dropped_calls_tower(month_int, year, df,
                        palette=palette,
                        # column_widths=None,
                        call_direction=None,
                        phone_type=None,
                        network=None,
                        dropped_reason=None):
    month_name = calendar.month_name[month_int]
    previous_year = year - 1

    # FILTERS
    df_month_now = df[(df['DateTime'].dt.month == month_int) & (df['DateTime'].dt.year == year)].copy()

    if call_direction != '*ALL*':
        df_month_now = df_month_now[df_month_now['Call Direction'] == call_direction]
    if phone_type != '*ALL*':
        df_month_now = df_month_now[df_month_now['Phone Type'] == phone_type]
    if network != '*ALL*':
        df_month_now = df_month_now[df_month_now['Network'] == network]
    if dropped_reason != '*ALL*':
        df_month_now = df_month_now[df_month_now['Dropped Reason'] == dropped_reason]

    # COLUMNS SELECTION
    df_tower = df_month_now[['Total Calls', 'Dropped Calls', 'Last Cell Tower']]

    # dataframe for different networks
    total_tower = df_tower.groupby(['Last Cell Tower']).agg(
        {'Total Calls': ['sum'],
         'Dropped Calls': ['sum'],
         }).reset_index()
    total_tower.columns = ['Last Cell Tower', 'Total Calls', 'Dropped Calls']

    '''Dropped Calls %  = (SUM Dropped Calls / SUM Total Calls)*100'''
    total_tower['Dropped Calls %'] = (total_tower['Dropped Calls'] / total_tower[
        'Total Calls']) * 100

    total_tower = total_tower.sort_values(by=['Total Calls', 'Dropped Calls %'], ascending=False)

    # PLOTTING
    from plotly.subplots import make_subplots
    import plotly.express as px

    # fig = px.scatter(total_tower, x='Total Calls', y='Dropped Calls %',
    #               color='Total Calls', size='Dropped Calls %')
    max_value = total_tower['Total Calls'].max()
    min_value = total_tower['Total Calls'].min()
    range_value = max_value - min_value

    quantile = list(map(round, (len(palette) - 1) * (total_tower['Total Calls'].values - min_value) / range_value))

    fig = go.Figure(data=go.Scatter(
        x=total_tower['Total Calls'],
        y=total_tower['Dropped Calls %'],
        mode='markers',
        marker=dict(
            size=total_tower['Dropped Calls %'],
            color=[palette[q] for q in quantile],  # set color equal to a variable
            colorscale='Oranges',  # one of plotly colorscales
            showscale=False,
        ),
        hoverinfo='none',
        customdata=total_tower['Last Cell Tower'],
        hovertemplate="%{customdata}",
        # hovertext="",
        # hovertemplate='',
    ))
    #    import plotly.express as px
    #    fig = go.Figure(data=px.scatter(
    #                    total_tower,
    #                    x="Total Calls",
    #                    y="Dropped Calls %",
    #                    color="Total Calls",
    #                    colorscale='Oranges',
    #                    size='Dropped Calls %',
    #                    hover_data=['Last Cell Tower'])
    #                    )

    # Update Title Font
    for i in fig['layout']['annotations']:
        # print(i)
        i['font'] = dict(size=12,
                         # color='red',
                         )

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        showlegend=False,
        # title='Dropped Calls per Cell Tower',
        xaxis_title='Total Calls',
        yaxis_title='Dropped Calls %',
        coloraxis_showscale=False,
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
                          'size': 12
                      },
                      )

    return fig

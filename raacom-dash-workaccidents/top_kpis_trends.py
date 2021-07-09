import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import optimize
from datetime import datetime
import calendar
from funcs import font_family, value_format, filter_data, prev, filter_performance_scope, kpis_prep


def get_top_kpi_trends(month_int, year, df, chart, client_type=None,
                       accident_nature=None,
                       accident_status=None,
                       appeal_status=None, ):
    # Filters
    df = filter_data(df, client_type,
                     accident_nature,
                     accident_status,
                     appeal_status, )

    df = df.rename(columns={'Accident Occurrence Date': "DateTime"})
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    # for column in ['Work Accident Flag', 'Serious Accident Flag']:
    #     df[column] = df[column].apply(lambda x: 1 if x == 'Y' else 0)
    # df['Work Interruption (days)'] = df['Work Interruption (days)'].apply(lambda x: 1 if x else 0)
    df.iloc[:1250, -1] = [0] * 1250

    # Month-to-Date - 1 Year Scope
    end_year = year
    start_year = year - 1  # prev year
    # prev_month_int = month_int - 1
    prev_month_int = month_int - 1 if month_int != 1 else 12
    if month_int > 2:
        month_2_ago = month_int - 2
        year_2_ago = year
    else:
        month_2_ago = 10 + month_int
        year_2_ago = year - 1
    # month_2_ago = month_int - 2 if month_int > 2 else 12 - month_int

    # Last 12M
    from calendar import monthrange
    _, max_days = monthrange(year, month_int)
    if month_int < 10:
        start_date, end_date = f'{start_year}-0{month_int}-01', f'{end_year}-0{month_int}-{max_days}'
    else:
        start_date, end_date = f'{start_year}-{month_int}-01', f'{end_year}-{month_int}-{max_days}'
    df_12_m = df[
        df['DateTime'].between(start_date, end_date, inclusive=True)].copy()  # include 1st and last 30(1)st dates

    # YTD
    _, max_days = monthrange(year, month_int)
    if month_int < 10:
        start_date, end_date = f'{year}-01-01', f'{year}-0{month_int}-{max_days}'
    else:
        start_date, end_date = f'{year}-01-01', f'{year}-{month_int}-{max_days}'
    current_df_ytd = df[df['DateTime'].between(start_date, end_date, inclusive=True)].copy()

    start_date, end_date = f'{start_year}-01-01', f'{start_year}-{month_int}-{max_days}'
    prev_df_ytd = df[df['DateTime'].between(start_date, end_date, inclusive=True)].copy()

    # UPPER PART
    column_to_agg, agg = kpis_prep(df, chart)

    df_groupby = df_12_m.groupby(pd.Grouper(key='DateTime', freq='M')).agg(
        {column_to_agg: agg}).reset_index()
    df_groupby.columns = ['DateTime', chart]
    current_month_kpi = df_groupby[
        (df_groupby['DateTime'].dt.month == month_int) & (df_groupby['DateTime'].dt.year == year)
        ][chart].sum()
    prev_month_kpi = df_groupby[
        (df_groupby['DateTime'].dt.month == prev_month_int) &
        (df_groupby['DateTime'].dt.year == year if month_int != 1 else start_year)
        ][chart].sum()
    prev_year_kpi = df_groupby[
        (df_groupby['DateTime'].dt.month == month_int) & (df_groupby['DateTime'].dt.year == start_year)
        ][chart].sum()

    month_diff, year_diff = 0, 0  # handling /0 error
    if (prev_month_kpi > 0) and (prev_year_kpi > 0):
        month_diff = round((current_month_kpi - prev_month_kpi) / prev_month_kpi * 100,
                           1)  # current month - prev month %
        year_diff = round((current_month_kpi - prev_year_kpi) / prev_year_kpi * 100,
                          1)  # current month - prev year month %

    current_ytd_grouped = current_df_ytd.groupby(pd.Grouper(key='DateTime', freq='M')).agg(
        {column_to_agg: agg}).reset_index()
    current_ytd_grouped.columns = ['DateTime', chart]
    current_ytd_grouped['cumsum'] = current_ytd_grouped[chart].cumsum()

    # prev ytd
    prev_ytd_grouped = prev_df_ytd.groupby(pd.Grouper(key='DateTime', freq='M')).agg(
        {column_to_agg: agg}).reset_index()
    prev_ytd_grouped.columns = ['DateTime', chart]
    prev_ytd_grouped['cumsum'] = prev_ytd_grouped[chart].cumsum()

    # current_ytd_grouped_last3 = current_ytd_grouped[
    #    current_ytd_grouped['DateTime'].between(
    #        f'{year_2_ago}-{month_2_ago}-1',
    #        f'{year}-{month_int}-{max_days}',
    #        inclusive=True)
    # ].copy()
    # prev_ytd_grouped_last3 = prev_ytd_grouped[
    #    prev_ytd_grouped['DateTime'].between(
    #        f'{year_2_ago}-{month_2_ago}-1',
    #        f'{year}-{month_int}-{max_days}',
    #        inclusive=True)
    # ].copy()

    if chart == 'Nb of Accidents':
        current_ytd_kpi = round(current_ytd_grouped[chart].sum(), 1)
        prev_ytd_kpi = round(prev_ytd_grouped[chart].sum(), 1)
    else:
        current_ytd_kpi = round(current_ytd_grouped[chart].mean(), 1)
        prev_ytd_kpi = round(prev_ytd_grouped[chart].mean(), 1)

    # current_ytd_kpi_last3 = round(current_ytd_grouped[chart]_last3.sum(), 1)
    # prev_ytd_kpi_last3 = round(prev_ytd_grouped[chart]_last3.sum(), 1)

    ytd_diff = 0
    if (prev_ytd_kpi > 0):
        ytd_diff = round((current_ytd_kpi - prev_ytd_kpi) / prev_ytd_kpi * 100, 1)


    # LOWER PART
    # current ytd
    # f'{prev_ytd_kpi:,}', f'{current_ytd_kpi:,}'

    fig = make_subplots(rows=2, cols=1, start_cell="top-left",
                        shared_xaxes=False,  # ! step-like bars
                        shared_yaxes=False,
                        vertical_spacing=0.2,
                        # horizontal_spacing=0.03,  # space between the columns
                        )

    # ALL
    prefix = ''
    if chart != 'Nb of Accidents':
        suffix = '%'
    else:
        suffix = ''
    round_option = 2 if chart != 'Nb of Accidents' else 0

    # 2 ROWS
    if chart != 'Nb of Accidents':
        fig.add_trace(
            go.Bar(x=df_groupby['DateTime'],  # +-1/2 day difference
                   y=df_groupby[chart],
                   name='',
                   text=[f'Month: {m} {y}<br>{chart}: {prefix}{value_format(round(v, round_option))}{suffix}'
                         for m, y, v in zip(df_groupby['DateTime'].dt.month_name(),
                                            df_groupby['DateTime'].dt.year,
                                            df_groupby[chart])],
                   cliponaxis=False,
                   marker={'color': 'darkgray'},
                   hoverinfo='none',
                   ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Bar(x=current_ytd_grouped['DateTime'],  # current_ytd_grouped_last3['DateTime'],
                   y=current_ytd_grouped[chart],  # current_ytd_grouped_last3[chart]
                   name='',
                   cliponaxis=False,
                   marker={'color': 'darkgray'},
                   hoverinfo='none',
                   ),
            row=2, col=1,
        )
    else:
        fig.add_trace(
            go.Scatter(x=df_groupby['DateTime'],  # +-1/2 day difference
                       y=df_groupby[chart],
                       name='',
                       text=[f'Month: {m} {y}<br>{chart}: {prefix}{value_format(int(v))}{suffix}'
                             for m, y, v in zip(df_groupby['DateTime'].dt.month_name(),
                                                df_groupby['DateTime'].dt.year,
                                                df_groupby[chart])],
                       mode='lines',
                       fill=None if chart == 'Customer' else 'tozeroy',
                       hovertemplate='<extra></extra>',
                       line_color='darkgray',  # #E8E8E8
                       ),
            row=1, col=1,
        )
        fig.add_trace(
            go.Scatter(x=current_ytd_grouped['DateTime'],  # current_ytd_grouped_last3['DateTime'],
                       y=current_ytd_grouped['cumsum'],
                       # if chart == 'Customer' else current_ytd_grouped_last3['cumsum'],
                       name='',
                       mode='lines',
                       fill=None if chart == 'Customer' else 'tozeroy',
                       hovertemplate='<extra></extra>',
                       line_color='darkgray',  # #E8E8E8
                       ),
            row=2, col=1,
        )

    # Previous year line for the 2d row
    fig.add_trace(
        go.Scatter(x=current_ytd_grouped['DateTime'],
                   # df[df['DateTime'].between(start_date, end_date, inclusive=True)],  # +-1/2 day difference
                   y=prev_ytd_grouped['cumsum' if chart == 'Nb of Accidents' else chart],
                   name=f'{start_year}',
                   mode='lines',
                   fill=None,
                   # text=f'{start_year}',
                   text=[f'Month: {m}<br>{chart}: {prefix}{value_format(round(v, round_option))}{suffix}'
                         for m, v in zip(current_ytd_grouped['DateTime'].dt.month_name(),
                                         prev_ytd_grouped['cumsum' if chart != 'Sales Margin %' else chart])],
                   textposition="top center",
                   line_color='#565656',  # #E8E8E8
                   hovertemplate='%{text}',
                   ),
        row=2, col=1,
    )

    # # TREND LINE FOR 1 ROW
    x = np.array(list(range(len(df_groupby['DateTime']))))
    y = df_groupby[chart].values
    k, b = optimize.minimize(lambda w: (((y - (w[0]*x + w[1]))**2).sum()), np.array([[0], [0]]), method='BFGS').x

    x_trend = df_groupby['DateTime']
    y_trend = k * x + b

    fig.add_trace(
        go.Scatter(x=x_trend,
                   y=y_trend,
                   name='',
                   text=[
                       f'Month: {calendar.month_abbr[d.month]} {d.year}<br>{chart}: {prefix}{round(v, round_option)}{suffix}'
                       for d, v in zip(x_trend, y_trend)],
                   line_color='Cyan',
                   # hoverinfo=None,
                   hovertemplate='%{text}',
                   mode='lines',
                   ),
        row=1, col=1,
    )

    # UPDATE AXES FOR EACH ROW
    # ROW 1
    fig.update_xaxes(
        showline=False,
        showgrid=False,
        showticklabels=True,
        dtick="M1",
        tickformat="%b-%y",
        tickfont=dict(size=9,  # customize tick size
                      # color='default',
                      ),
        ticks='',  # |
        tickangle=30,
        nticks=6,
        row=1, col=1,
    )
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
        range=[0, 1.5 * df_groupby[chart].max()],
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
        tickfont=dict(size=9),
        ticks='',  # |
        tickangle=0,
        row=2, col=1,
    )
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
        range=[0, 1.5 * (current_ytd_grouped[chart if chart != 'Nb of Accidents' else 'cumsum'].max())],
        row=2, col=1,
    )

    # UPPER
    # KPI
    fig.add_annotation(text=f"<b>{prefix} {value_format(round(current_month_kpi, 1))}{suffix}</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           # family="Courier New, monospace",
                           size=18,
                           #  color="black"
                       ),
                       x=0.01, y=1, showarrow=False)
    fig.add_annotation(text=f"{calendar.month_abbr[month_int]}-{year}",
                       xref="paper", yref="paper",
                       font_size=10,
                       x=0.01, y=0.96, showarrow=False)

    # UPPER
    # DIFF
    fig.add_annotation(text=f"<b>▲ +{value_format(month_diff)}%</b>" if month_diff > 0 else f"<b>▼ {value_format(month_diff)}%</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           size=14,
                           color="royalblue" if month_diff > 0 else "darkred",
                       ),
                       x=0.35, y=0.97, showarrow=False)
    fig.add_annotation(text=f"vs {calendar.month_abbr[prev_month_int]}-{year if month_int != 1 else start_year}",
                       xref="paper", yref="paper",
                       font_size=10,
                       font_color="royalblue" if month_diff > 0 else "darkred",
                       x=0.35, y=0.94, showarrow=False)

    fig.add_annotation(text=f"<b>▲ +{value_format(year_diff)}%</b>" if year_diff > 0 else f"<b>▼ {value_format(year_diff)}%</b>",
                       xref="paper", yref="paper",
                       font=dict(
                           size=14,
                           color="royalblue" if year_diff > 0 else "darkred",
                       ),
                       x=0.7, y=0.97, showarrow=False)
    fig.add_annotation(text=f"vs {calendar.month_abbr[month_int]}-{start_year}",
                       xref="paper", yref="paper",
                       font_size=10,
                       font_color="royalblue" if year_diff > 0 else "darkred",
                       x=0.7, y=0.94, showarrow=False)

    # LOWER
    # KPI
    fig.add_annotation(text=f"<b>{prefix} {value_format(current_ytd_kpi)}{suffix}</b>",
                       xref="paper", yref="paper",
                       font_size=18,
                       x=0.01, y=0.5, showarrow=False)
    fig.add_annotation(text=f"{calendar.month_abbr[month_int]}-{year}",
                       xref="paper", yref="paper",
                       font_size=10,
                       x=0.01, y=0.46, showarrow=False)

    # UPPER
    # DIFF
    fig.add_annotation(text=f"<b>▲ +{value_format(ytd_diff)}%</b>" if ytd_diff > 0 else f"<b>▼ {value_format(ytd_diff)}%</b>",
                       xref="paper", yref="paper",
                       font_size=14,
                       font_color="royalblue" if ytd_diff > 0 else "darkred",
                       x=0.7, y=0.455, showarrow=False)
    fig.add_annotation(text=f"vs YTD {calendar.month_abbr[month_int]}-{start_year}",
                       xref="paper", yref="paper",
                       font_size=10,
                       font_color="royalblue" if ytd_diff > 0 else "darkred",
                       x=0.7, y=0.425, showarrow=False)

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
    fig.update_layout(
        font={
            'family': font_family,
            # 'color': 'black',
            # 'size': 12
        },
    )

    return fig




import plotly.graph_objects as go
import pandas as pd
import numpy as np
import calendar
from plotly.subplots import make_subplots

from funcs import get_palette, font_family, value_format

palette = get_palette()
def get_trend_graph(df_copy,
                    kpi,
                    palette=palette,
                    dates=None,
                    call_direction=None,
                    reason=None,
                    network=None,
                    last_cell_tower=None,
                    phone_type=None):
    # FILTERS
    df = df_copy.copy(deep=True)
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
    # DATA
    df['DateTime'] = df['DateTime'].astype('datetime64[M]')
    df_months = df.groupby('DateTime').agg({kpi: ['sum']}).reset_index()
    df_months.columns = ['Current Month', kpi]
    df_months = df_months.sort_values(by='Current Month', ascending=True)

    # COLORING
    colored_years = df_months['Current Month'].dt.year.unique().tolist()
    colored_years.reverse()
    palette2 = {}
    for c, y in zip(palette, colored_years):
        palette2[y] = c
    colored_years.reverse()

    # PLOTTING
    fig = go.Figure()

    # Separate for each year
    for year in colored_years:
        fig.add_trace(
            go.Scatter(
                x=df_months[df_months['Current Month'].dt.year == year]['Current Month'],
                y=df_months[df_months['Current Month'].dt.year == year][kpi],
                name='',
                mode='lines+text',
                # mode = 'lines',
                line_color=palette2[year],
                fill='tozeroy',
                fillcolor=palette2[year],
                # textfont_color = '#365da9',
                text=[(f'{value_format(x)}') for x in df_months[df_months['Current Month'].dt.year == year][kpi]],
                textposition='top left',
                # hovertemplate = '%{text}',
                hovertemplate='Month: %{x}<br>' + f'{kpi}:' + ' %{text}',
            ),
        )

    # Add grey rectangle for half of the years on the graph
    min_y = df_months[kpi].min()
    max_y = df_months[kpi].max()
    for year in colored_years:
        max_date = df_months.loc[df_months['Current Month'].dt.year == year].max()[0].strftime("%Y-%m-%d")
        min_date = df_months.loc[df_months['Current Month'].dt.year == year].min()[0].strftime("%Y-%m-%d")
        fig.add_vrect(
            x0=min_date,
            x1=max_date,
            y0=min_y if min_y < 0 else 0,
            y1=max_y + max_y * 0.1,
            fillcolor=["#E8E8E8" if year % 2 == 0 else "#FFFFFF"][0],
            opacity=0.3,
            layer="below",
            line_width=0,
            annotation_text=year,
            annotation_font_color='black',
            annotation_position="top left",
        )

    # Update X axis
    fig.update_xaxes(
        showline=False,
        showgrid=False,
        showticklabels=True,
        dtick='M1',
        tickformat='%b',
        ticks='',
        tickangle=0,
        title_text=f'<b>{kpi}</b>',
        title_font_color='grey',
    )

    # Update Y axis
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
        range=[0, 1.2 * df_months[kpi].max()],
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
                    t=20,
                    # pad=100 # Sets the amount of padding (in px) between the plotting area and the axis lines
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


def get_distribution_graph(df,
                           kpi,
                           column_to_group_by,
                           palette=palette,
                           max_bars=None,
                           dates=None,
                           call_direction=None,
                           reason=None,
                           network=None,
                           last_cell_tower=None,
                           phone_type=None):
    # FILTERS
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

    # DATA
    df['Phone Type'] = df['Phone Type'].apply(lambda x: x.split()[0])
    total_df = df.groupby([column_to_group_by]).agg(
        {kpi: ['sum']}).reset_index()
    calc = 'Percent of All'
    total_df[calc] = total_df[kpi] / total_df[kpi].sum() * 100
    total_df.columns = [column_to_group_by, kpi, calc]

    if not max_bars:
        total_df = total_df.sort_values(by=calc, ascending=False)
    else:
        total_df = total_df.sort_values(by=calc, ascending=False).head(max_bars)

    # COLORING
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette) + 1), palette):
        palette2[i] = c
    total_df[f'quantiles_{kpi}'] = pd.cut(total_df[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    total_df[f'quantiles_{kpi}'] = total_df[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()

    # PLOTTING

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=total_df[kpi],
            y=[name + ' ' for name in total_df[column_to_group_by]],
            text=[(f' {value_format(x)}   <i>{value_format(y)}%<i>') for x, y in zip(total_df[kpi], total_df[calc])],
            textfont_color=total_df[f'quantiles_{kpi}'],
            textposition='outside',
            marker_color=total_df[f'quantiles_{kpi}'],
            marker_line={
                'color': total_df[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='h',
            hoverinfo='none',
        ),
    )

    # Update X axis
    x_max = total_df[kpi].max() + (total_df[kpi].max() * 0.2)
    fig.update_xaxes(
        zeroline=False,
        showline=False,
        showgrid=False,
        showticklabels=False,
        range=[0, x_max],
        title_text=f"<b>{kpi}</b><br>by {column_to_group_by}",
        title_font={
            'color': 'grey',
            'size': 10,
        },
    )

    # Update Y axis
    fig.update_yaxes(
        categoryorder='total ascending',
        showgrid=False,
        showline=False,
        showticklabels=True,
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


def get_pareto_analysis(df,
                        kpi,
                        column_to_group_by='Phone Type',
                        palette=palette,
                        dates=None,
                        call_direction=None,
                        reason=None,
                        network=None,
                        last_cell_tower=None,
                        phone_type=None):
    # FILTERS
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

    # DATA
    df['Phone Type'] = df['Phone Type'].apply(lambda x: x.split()[0])
    total_df = df.groupby([column_to_group_by]).agg(
        {kpi: ['sum']}).reset_index()
    total_df.columns = [column_to_group_by, kpi]
    total_df = total_df.sort_values(by=kpi, ascending=False)
    cumsum = 'Cumulative kpi'
    total_df[cumsum] = total_df[kpi].cumsum()
    calc = 'Cumulative Percent'
    total_df[calc] = total_df[cumsum] / total_df[kpi].sum() * 100
    total_df.columns = [column_to_group_by, kpi, cumsum, calc]

    # COLORING
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette) + 1), palette):
        palette2[i] = c
    total_df[f'quantiles_{kpi}'] = pd.cut(total_df[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    total_df[f'quantiles_{kpi}'] = total_df[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()

    # PLOTTING
    fig = go.Figure()

    # Line Chart for cumulative percents
    fig.add_trace(
        go.Scatter(
            x=total_df[column_to_group_by],
            y=total_df[calc],
            name='',
            mode='lines',
            line_shape='spline',
            line_color='#F0F0F0',
            fill='tozeroy',
            fillcolor='#F0F0F0',
            hoverinfo='none',
            opacity=0.3,
        ),
    )

    # Vertical Bar Chart for kpi + dimension
    fig.add_trace(
        go.Bar(
            x=total_df[column_to_group_by],
            y=total_df[kpi],
            text=[(f' {value_format(x)}') for x in total_df[kpi]],
            textfont_color=total_df[f'quantiles_{kpi}'],
            textposition='outside',
            marker_color=total_df[f'quantiles_{kpi}'],
            marker_line={
                'color': total_df[f'quantiles_{kpi}'],
                'width': 1,
            },
            cliponaxis=False,
            orientation='v',
            hoverinfo='none',
            yaxis='y2',
        ),
    )

    # Text point for Line Chart
    fig.add_trace(
        go.Scatter(
            x=total_df[column_to_group_by],
            y=total_df[calc],
            name='',
            mode='text',
            text=[(f'{value_format(x)}%') for x in total_df[calc]],
            textposition='top center',
            hoverinfo='none',
            yaxis='y3',
        ),
    )

    # Create axis objects
    fig.update_layout(
        yaxis2=dict(
            overlaying='y',
        ),
        yaxis3=dict(
            overlaying='y',
        ),
    )

    # Update Y axis
    fig.update_yaxes(
        showticklabels=False,
        range=[0, 1.1 * total_df[calc].max()],
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

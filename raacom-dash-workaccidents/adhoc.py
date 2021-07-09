import plotly.graph_objects as go
import pandas as pd
import numpy as np
import calendar
from clickhouse_driver import Client
from datetime import datetime
#from statistics import mean
font_family = 'Lato-Regular'

from funcs import get_palette, font_family, value_format, filter_data, filter_on_date, kpis_prep
palette = get_palette('list')

def trends_function(df,
                    kpi,
                    palette=palette,
                    dates=None,
                    client_type=None,
                    accident_nature=None,
                    accident_status=None,
                    appeal_status=None,
                   ):
    """
    Making trend vizualization depending on choosen kpi

    Parameters
    ----------
    df : dataframe
        Data
    kpi : str  
        Parametr to aggregate data. Possible options:
            - Nb of Accidents,
            - Nb of Work Accidents,
            - Work Accidents %,
            - Nb of Serious Accidents,
            - Serious Accidents %,
            - Nb of Accidents with Work Interruption,
            - Accidents with Work Interruption %,
            - Avg Work Interruption,
            - Total Work Interruption,
            - Nb of Victims,
            - Victim Age,
            - Nb of Deceases
    palette : list
        color_palette (default: from config.json file)
    dates: str  
        Date filter
    client_type: list of str, optional
        Client type filter
    accident_nature: list of str, optional
        Accident nature filter
    accident_status: list of str, optional
        Accident status filter
    appeal_status: list of str, optional
        Appeal status filter
    Returns
    -------
    fig
        GO figure (trend line of KPI)
    """

    # FILTERS
    if dates:
        df = filter_on_date(df, dates)
    
    df = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    # DATA
    column_to_agg, agg = kpis_prep(df, kpi)
    #----------------------------------------------------------------------------------------------------
    df['Accident Occurrence Date'] = df['Accident Occurrence Date'].astype('datetime64[M]')
    df_months = df.groupby('Accident Occurrence Date').agg( {column_to_agg: [agg] } ).reset_index()
    df_months.columns = ['Accident Occurrence Date', kpi]
    df_months = df_months.sort_values(by='Accident Occurrence Date', ascending=True)

    # COLORING
    colored_years = df_months['Accident Occurrence Date'].dt.year.unique().tolist()
    colored_years.reverse()
    palette2 = {}
    for c, y in zip(palette, colored_years):
        palette2[y] = c
    colored_years.reverse()
    
    # PLOTTING
    fig = go.Figure()

    # Separate for each year
    for year in colored_years:
        max_val = df_months[df_months['Accident Occurrence Date'].dt.year == year][kpi].max()
        min_val = df_months[df_months['Accident Occurrence Date'].dt.year == year][kpi].min()
        fig.add_trace(
            go.Scatter(
                x = df_months[df_months['Accident Occurrence Date'].dt.year == year]['Accident Occurrence Date'], 
                y = df_months[df_months['Accident Occurrence Date'].dt.year == year][kpi], 
                name = '',
                mode = 'lines+text',
                # mode = 'lines',
                line_color = palette2[year],
                fill = 'tozeroy',
                fillcolor = palette2[year],
                # textfont_color = '#365da9',
                text = [value_format(x) for x in df_months[df_months['Accident Occurrence Date'].dt.year == year][kpi] if x == max_val or x == min_val],
                textposition='top left',
                #hovertemplate = '%{text}',
                hovertemplate = 'Month: %{x}<br>' + f'{kpi}:' + ' %{y}',
            ),
        )

    # Add grey rectangle for half of the years on the graph
    min_y = df_months[kpi].min()
    max_y = df_months[kpi].max()
    for year in colored_years:
        max_date = df_months.loc[df_months['Accident Occurrence Date'].dt.year == year].max()[0].strftime("%Y-%m-%d")
        min_date = df_months.loc[df_months['Accident Occurrence Date'].dt.year == year].min()[0].strftime("%Y-%m-%d")
        fig.add_vrect(
            x0 = min_date,
            x1 = max_date,
            y0 = min_y if min_y < 0 else 0,
            y1 = max_y + max_y * 0.1,
            fillcolor = ["#E8E8E8" if year % 2 == 0 else "#FFFFFF"][0],
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
        tickangle=45,
        nticks=df_months[df_months['Accident Occurrence Date'].dt.year == year]['Accident Occurrence Date'].shape[0] // 4,
        title_text=f'<b>{kpi}</b>',
        title_font_color='grey',
    )

    # Update Y axis
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
        range=[0, 1.2 * df_months[kpi].max()]
    )

    # UPDATE TITLE FONT
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=12,)

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
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

def distribution_function(df,
                          kpi,
                          column_to_group_by,
                          palette=palette,
                          max_bars=None,
                          dates=None,
                          client_type=None,
                          accident_nature=None,
                          accident_status=None,
                          appeal_status=None,
                          ):
    """
    Making vizualization of distribution function depending on choosen kpi

    Parameters
    ----------
    df : dataframe
        Data
    kpi : str  
        Parametr to aggregate data. Possible options:
            - Nb of Accidents,
            - Nb of Work Accidents,
            - Work Accidents %,
            - Nb of Serious Accidents,
            - Serious Accidents %,
            - Nb of Accidents with Work Interruption,
            - Accidents with Work Interruption %,
            - Avg Work Interruption,
            - Total Work Interruption,
            - Nb of Victims,
            - Victim Age,
            - Nb of Deceases
    column_to_group_by: str
        on which column to compute kpi
    palette : list
        color_palette (default: from config.json file)
    max_bars: int, optional
        max amount of bars to be shown
    dates: str  
        Date filter
    client_type: list of str, optional
        Client type filter
    accident_nature: list of str, optional
        Accident nature filter
    accident_status: list of str, optional
        Accident status filter
    appeal_status: list of str, optional
        Appeal status filter
    Returns
    -------
    fig
        GO figure (bar chart of KPI distributed on choosen column)
    """
    # FILTERS
    if dates:
        df = filter_on_date(df, dates)
    
    df_filtered = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    # DATA
    column_to_agg, agg = kpis_prep(df_filtered, kpi)

    total_df = df_filtered.groupby([column_to_group_by]).agg(
        {column_to_agg : agg }).reset_index()
    calc = 'Percent of All'
    total_df.columns = [column_to_group_by, kpi]
    total_df[calc] = total_df[kpi] / total_df[kpi].sum() * 100
    total_df.columns = [column_to_group_by, kpi, calc]
    
    if not max_bars:
        total_df = total_df.sort_values(by=calc, ascending=False)
    else:
        total_df = total_df.sort_values(by=calc, ascending=False).head(max_bars)

    # COLORING
    palette.reverse()
    palette2 = {}
    for i, c in zip(range(1, len(palette)+1), palette):
        palette2[i] = c
    total_df[f'quantiles_{kpi}'] = pd.cut(total_df[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    total_df[f'quantiles_{kpi}'] = total_df[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()


    # PLOTTING
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x = total_df[kpi],
            y = [str(name) + ' ' for name in total_df[column_to_group_by]],
            text = [(f' {value_format(x)}   <i>{value_format(y)}%<i>') for x,y in zip(total_df[kpi], total_df[calc])],
            textfont_color = total_df[f'quantiles_{kpi}'],
            textposition='outside',
            marker_color = total_df[f'quantiles_{kpi}'],
            marker_line = {
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
        i['font'] = dict(size=12,)

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',
        plot_bgcolor='rgb(255,255,255)',
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


def pareto_analysis(df,
                    kpi,
                    column_to_group_by,
                    palette=palette,
                    max_bars=None,
                    dates=None,
                    client_type=None,
                    accident_nature=None,
                    accident_status=None,
                    appeal_status=None,
                    ):
    """
    Making vizualization of pareto analysis depending on choosen kpi

    Parameters
    ----------
    df : dataframe
        Data
    kpi : str  
        Parametr to aggregate data. Possible options:
            - Nb of Accidents,
            - Nb of Work Accidents,
            - Work Accidents %,
            - Nb of Serious Accidents,
            - Serious Accidents %,
            - Nb of Accidents with Work Interruption,
            - Accidents with Work Interruption %,
            - Avg Work Interruption,
            - Total Work Interruption,
            - Nb of Victims,
            - Victim Age,
            - Nb of Deceases
    column_to_group_by: str
        on which column to compute kpi
    palette : list
        color_palette (default: from config.json file)
    max_bars: int, optional
        max amount of bars to be shown
    dates: str  
        Date filter
    client_type: list of str, optional
        Client type filter
    accident_nature: list of str, optional
        Accident nature filter
    accident_status: list of str, optional
        Accident status filter
    appeal_status: list of str, optional
        Appeal status filter
    Returns
    -------
    fig
        GO figure 
    """
    # FILTERS
    if dates:
        df = filter_on_date(df, dates)
    
    df = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

    # DATA
    column_to_agg, agg = kpis_prep(df, kpi)

    # DATA
    total_df = df.groupby([column_to_group_by]).agg(
        {column_to_agg : agg }).reset_index()
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
    for i, c in zip(range(1, len(palette)+1), palette):
        palette2[i] = c
    total_df[f'quantiles_{kpi}'] = pd.cut(total_df[kpi], bins=len(palette), labels=[key for key in palette2.keys()])
    total_df[f'quantiles_{kpi}'] = total_df[f'quantiles_{kpi}'].map(lambda x: palette2[x])
    palette.reverse()

    # PLOTTING
    fig = go.Figure()

    # Line Chart for cumulative percents
    fig.add_trace(
        go.Scatter(
            x = total_df[column_to_group_by],
            y = total_df[calc],
            name = '',
            mode = 'lines',
            line_shape = 'spline',
            line_color = '#F0F0F0',
            fill = 'tozeroy',
            fillcolor = '#F0F0F0',
            hoverinfo='none',
            opacity=0.3,
            textfont_color='black',
        ),
    )

    # Vertical Bar Chart for kpi + dimension
    fig.add_trace(
        go.Bar(
            x = total_df[column_to_group_by],
            y = total_df[kpi],
            text = [(f' {value_format(x)}') for x in total_df[kpi]],
            textfont_color = 'black',
            textposition='outside',
            marker_color = total_df[f'quantiles_{kpi}'],
            marker_line = {
                'color': total_df[f'quantiles_{kpi}'],
                'width': 1,
            },
            orientation='v',
            hoverinfo='none',
            yaxis='y2',
        ),
    )

    # Text point for Line Chart
    fig.add_trace(
        go.Scatter(
            x = total_df[column_to_group_by],
            y = total_df[calc],
            name = '',
            mode = 'text',
            text = [(f'{value_format(x)}%') for x in total_df[calc]],
            textposition='top center',
            hoverinfo='none',
            yaxis='y3',
        ),
    )

    # Create axis objects
    fig.update_layout(
        yaxis2=dict(
            overlaying='y',
            range=[0, 1.1 * total_df[kpi].max()],
        ),
        yaxis3=dict(
            overlaying='y',
            range=[0, 1.1 * total_df[calc].max()],
        ),
    )
    #  UPDATE Y-AXIS
    fig.update_yaxes(
        showticklabels=False,
        #range=[0, 1.1 * total_df[calc].max()],
    )
 

    # UPDATE TITLE FONT
    for i in fig['layout']['annotations']:
        i['font'] = dict(size=12,)

    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',
        plot_bgcolor='rgb(255,255,255)',
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
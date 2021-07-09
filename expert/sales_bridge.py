import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import calendar
from funcs import prev, filter_data, augment_days, font_family, get_currency_sign, value_format, get_palette

currency_sign = get_currency_sign()

palette = get_palette()
palette = [palette[index] for index in range(1, len(palette) + 1)]

def get_sales_bridge(df,
                     current_year,
                     current_month,
                     dimension=None,
                     # for grouping the right vertical bar chart; if None - the func plots the left vertical bar chart | possible dimensions: ['Date', 'Customer', 'Product Group', 'Country']
                     customer=None,
                     country=None,
                     product_group=None):
    if dimension == 'Date':
        df[dimension] = df['DateTime'].dt.date.astype('str')
    elif dimension == 'Product Group':
        dimension = 'Business Line'

    # Filtering Data
    prev_year, prev_month, current_year, current_month = prev(current_year, current_month)
    df_filtered = filter_data(df, customer, country, product_group)
    df_filtered['Period'] = df_filtered['Current Month'].astype(str) + ' ' + df_filtered['Current Year'].astype(str)
    df_current = df_filtered[
        (df_filtered['Current Year'] == current_year) & (df_filtered['Current Month'] == current_month)]
    # df_prev = df_filtered[ (df_filtered['Current Year'] == current_year - 1 * (prev_month == 'Dec')) & (df_filtered['Current Month'] == prev_month) ]
    df_prev = df_filtered[(df_filtered['Current Year'] == prev_year) & (df_filtered['Current Month'] == prev_month)]

    # Group the data
    if dimension:
        data = pd.merge(
            df_prev.groupby([dimension, 'Period']).agg({'Total Sales': ['sum'], 'Total Sold Quantity': ['sum'],
                                                        'Average Selling Price': ['mean']}).reset_index(),
            df_current.groupby([dimension, 'Period']).agg({'Total Sales': ['sum'], 'Total Sold Quantity': ['sum'],
                                                           'Average Selling Price': ['mean']}).reset_index(),
            how='outer',
            on=dimension
        )
        data.columns = [dimension, 'Ref Period'] + ['Ref Total Sales', 'Ref Total Sold Quantity',
                                                    'Ref Average Selling Price'] + ['Act Period'] + ['Act Total Sales',
                                                                                                     'Act Total Sold Quantity',
                                                                                                     'Act Average Selling Price']
    else:
        data = pd.concat(
            [df_prev.groupby(['Period']).agg({'Total Sales': ['sum'], 'Total Sold Quantity': ['sum'],
                                              'Average Selling Price': ['mean']}).reset_index(),
             df_current.groupby(['Period']).agg({'Total Sales': ['sum'], 'Total Sold Quantity': ['sum'],
                                                 'Average Selling Price': ['mean']}).reset_index()],
            axis=1,
            ignore_index=True
        )
        data.columns = ['Ref Period'] + ['Ref Total Sales', 'Ref Total Sold Quantity', 'Ref Average Selling Price'] + [
            'Act Period'] + ['Act Total Sales', 'Act Total Sold Quantity', 'Act Average Selling Price']

    data = data.fillna(0)  # Update for Periods
    data['Ref Period'] = [i for i in list(data['Ref Period'].unique()) if i != 0][0]
    data['Act Period'] = [i for i in list(data['Act Period'].unique()) if i != 0][0]

    data['Price Effect'] = data['Ref Total Sold Quantity'] * (
                data['Act Average Selling Price'] - data['Ref Average Selling Price'])
    data['Volume Effect'] = data['Ref Average Selling Price'] * (
                data['Act Total Sold Quantity'] - data['Ref Total Sold Quantity'])
    data['Mix Effect'] = (data['Act Total Sold Quantity'] - data['Ref Total Sold Quantity']) * (
                data['Act Average Selling Price'] - data['Ref Average Selling Price'])

    # Data for plotting
    if dimension:
        dim_list = data[dimension].unique()

        # PLOTTING
        fig = make_subplots(
            rows=len(dim_list), cols=1,
            shared_xaxes=True,
        )

        # Get data and plot waterfal for each dimension item
        for n, d in enumerate(dim_list):
            df_final = data[data[dimension] == d][
                [dimension, 'Ref Total Sales', 'Price Effect', 'Volume Effect', 'Mix Effect', 'Act Total Sales']]
            df_final.columns = [dimension, data[data[dimension] == d]['Ref Period'].item(), 'Price Effect',
                                'Volume Effect', 'Mix Effect', data[data[dimension] == d]['Act Period'].item()]
            df_final.drop(dimension, axis=1, inplace=True)
            df_final = df_final.T.reset_index()
            df_final.columns = ['X', 'Y']
            df_final['Y'] = df_final['Y'].round()
            df_final['Percent_diff'] = (df_final['Y'] / df_final['Y'][0] * 100).round(1)
            df_final['Percent_diff'][4] = ((df_final['Y'][4] - df_final['Y'][0]) / df_final['Y'][0] * 100).round(1)
            df_final = df_final.replace([np.inf, -np.inf], 0)
            df_final = df_final.fillna(0)
            df_final['Percent_diff'] = pd.Series(
                [f'+{value_format(i)}%' if i > 0 and i < 100 else f'{value_format(i)}%' for i in df_final['Percent_diff']])
            df_final['Percent_diff'][0] = ''

            df_x = df_final['X'].values
            df_y = df_final['Y'].values
            df_p = df_final['Percent_diff'].values

            # PLOTTING
            fig.add_trace(
                go.Waterfall(
                    x=df_x,
                    y=df_y,
                    name='',
                    measure=['absolute', 'relative', 'relative', 'relative', 'total'],
                    text=[(f'{currency_sign} {value_format(y)}<br><i>{p}</i>') for y, p in zip(df_y, df_p)],
                    textposition='outside',
                    orientation='v',
                    connector_line_color='rgb(255,255,255)',
                    hovertemplate=f'<b>{d}</b><br>' + '%{text}',
                ),
                row=n + 1, col=1,
            )

            fig.update_xaxes(
                showticklabels=False,
                row=n + 1, col=1,
            )

            fig.update_yaxes(
                title_text=d,
                # title_font_size=20,
                # title_font_color='black',
                showticklabels=False,
                range=[0, df_final[0:4][df_final['Y'] > 0]['Y'].sum() + (
                            df_final[0:4][df_final['Y'] > 0]['Y'].sum() * 0.5)],
                row=n + 1, col=1,
            )

        fig.update_xaxes(
            type='category',
            showticklabels=True,
            # tickfont_color='black',
            side='top',
            row=1, col=1,
        )

    else:
        df_final = data[['Ref Total Sales', 'Price Effect', 'Volume Effect', 'Mix Effect', 'Act Total Sales']]
        df_final.columns = [data['Ref Period'].item(), 'Price Effect', 'Volume Effect', 'Mix Effect',
                            data['Act Period'].item()]
        df_final = df_final.T.reset_index()
        df_final.columns = ['X', 'Y']
        df_final['Y'] = df_final['Y'].round()
        df_final['Percent_diff'] = (df_final['Y'] / df_final['Y'][0] * 100).round(1)
        df_final['Percent_diff'][4] = ((df_final['Y'][4] - df_final['Y'][0]) / df_final['Y'][0] * 100).round(1)
        df_final = df_final.replace([np.inf, -np.inf], 0)
        df_final = df_final.fillna(0)
        df_final['Percent_diff'] = pd.Series(
            [f'+{value_format(i)}%' if i > 0 and i < 100 else f'{value_format(i)}%' for i in df_final['Percent_diff']])
        df_final['Percent_diff'][0] = ''

        df_x = df_final['X'].values
        df_y = df_final['Y'].values
        df_p = df_final['Percent_diff'].values
        texts = ['',
                 'Deviation due to apply higher <br>or lower Selling Prices',
                 'Variation in the Total Sales <br>due to the Total Sold Quantity',
                 'Measures the impact in the <br>Total Sales resulting from <br>a change in the mix of the <br>Total Sold Quantity <br>(% of units sold per <br>reference over the total)',
                 '']

        # PLOTTING
        fig = go.Figure()

        fig.add_trace(
            go.Waterfall(
                x=df_x,
                y=df_y,
                name='',
                measure=['absolute', 'relative', 'relative', 'relative', 'total'],
                text=[(f'<b>{x}:</b><br>{currency_sign} {value_format(y)}<br><i>{p}</i><br>{t}') for x, y, p, t in
                      zip(df_x, df_y, df_p, texts)],
                textposition='outside',
                orientation='v',
                connector_line_color='rgb(255,255,255)',
                hovertemplate='%{text}',
            )
        )

        fig.update_xaxes(
            type='category',
            showticklabels=True,
            # tickfont_color='black',
            side='top',
        )

        fig.update_yaxes(
            showticklabels=False,
            range=[0,
                   df_final[0:4][df_final['Y'] > 0]['Y'].sum() + (df_final[0:4][df_final['Y'] > 0]['Y'].sum() * 0.5)],
        )

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

    if dimension:
        fig.update_layout(height=250 * len(dim_list))

    return fig
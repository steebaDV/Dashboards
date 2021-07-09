import plotly.graph_objects as go
import pandas as pd
import numpy as np
import calendar
from clickhouse_driver import Client
import random
import datetime
from urllib.request import urlopen
import json
import calendar
from funcs import font_family, augment_days
from plotly.subplots import make_subplots
from funcs import font_family, augment_days, filter_data, get_palette, get_currency_sign

palette = get_palette()
palette = [palette[index] for index in range(1, len(palette) + 1)]

with open('params.json', 'r') as f:
    params = json.load(f)

# Customer segment descriptions
customer_segments_desc = {
    'Champions': 'Bought recently, buy often and spend the most!',
    'Loyal': 'Spend good money with us often. Responsive to promotions.',
    'Potential Loyalist': 'Recent customers, but spent a good amount and bought more than once.',
    'Promising': 'Recent shoppers, but haven’t spent much.',
    'New Customers': 'Bought most recently, but not often.',
    'Need Attention': 'Above average recency, frequency and monetary values. May not have bought very recently though.',
    'About to Sleep': 'Below average recency, frequency and monetary values. Will lose them if not reactivated.',
    'At Risk': 'Spent big money and purchased often. But long time ago. Need to bring them back!',
    'Cannot Lose Them': 'Made biggest purchases, and often. But haven’t returned for a long time.',
    'Hibernating': 'Last purchase was long back, low spenders and low number of orders.',
    'Lost': 'Lowest recency, frequency and monetary scores.',
}

# Customer segment: Recommended Marketing Actions
# Recommendations are based on main picture from 
# https://linpack-for-tableau.com/data-visualizations/tableau-dashboards/sales-dashboard/rfm-analysis/
customer_segments_rec = {
    'Champions': 'Reward them. Can be early adopters for new products. Will promote your brand.',
    'Loyal': 'Upsell higher value products. Ask for reviews. Engage them.',
    'Potential Loyalist': 'Offer membership / loyalty program, recommend other products.',
    'Promising': 'Create brand awareness, offer free trials.',
    'New Customers': 'Provide on-boarding support, give them early success, start by building relationship.',
    'Need Attention': '',
    'About to Sleep': 'Share valuable resources, recommend popular products / renewals at discount, reconnect with them.',
    'At Risk': '',
    'Cannot Lose Them': '',
    'Hibernating': '',
    'Lost': 'Revive interest with reach out campaign, ignore otherwise.',
}

# Customer segment order
customer_segments_order = {
    'Champions': 1,
    'Loyal': 2,
    'Potential Loyalist': 3,
    'Promising': 4,
    'New Customers': 5,
    'Need Attention': 6,
    'About to Sleep': 7,
    'At Risk': 8,
    'Cannot Lose Them': 9,
    'Hibernating': 10,
    'Lost': 11,
}

def rate(data, column):
    a = np.quantile(data, [params[column.lower()][0][f"{i}"] for i in range(2,6)])
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
                    l.append(i+2)
    return l

def data_prepared(df,
                    class_rfm=None,
                    product=None,
                    country=None,
                    customer=None,
                    ):
    # FILTERS
    df_filtered = filter_data(df, customer=customer, country=country, product_group=product)

    # RFM DATA
    rfm_table = df.groupby(pd.Grouper(key='Customer')).agg(
        {'Total Sales': ['sum'], 'Total Sold Quantity': ['sum'], 'DateTime':['min']}).reset_index()
    rfm_table.columns = ['Customer', 'Monetary', 'Frequency', 'Recency']
    rfm_table['Recency'] = datetime.datetime.today() - rfm_table['Recency']
    rfm_table['Recency'] = pd.Series([x.days for x in rfm_table['Recency']])
    a = np.quantile(rfm_table['Monetary'], q = [0.2, 0.4, 0.6, 0.8])
    rfm_table['MonetaryRate'] = rate(rfm_table['Monetary'], 'Monetary')
    rfm_table['FrequencyRate'] = rate(rfm_table['Frequency'], 'Frequency')
    rfm_table['RecencyRate'] = rate(rfm_table['Recency']*(-1), 'Recency')
    rfm_table['RFMScore'] = rfm_table.apply(lambda x: f"{x['RecencyRate']}{x['FrequencyRate']}{x['MonetaryRate']}", axis=1)

    rfm_align = pd.read_csv('RFM.csv').drop([0,1,2,3,4])
    iterables = [[i for i in range(5,0,-1)],[i for i in range(5,0,-1)]]
    rfm_align.index = pd.MultiIndex.from_product(iterables, names=['Recency', 'Frequency'])
    rfm_align.drop(columns=['There are 125 possible combinations of profile.', 'Unnamed: 1'], axis=1, inplace=True)
    rfm_align.columns=['5','4','3','2','1']

    rfm_metrics = []
    for i in rfm_align.index:
        for j, el in enumerate(rfm_align.loc[i]):
            rfm_metrics.append([i[0], i[1], 5-j, el])

    rfm_metr = pd.DataFrame(rfm_metrics)
    rfm_metr.columns = ['Recency', 'Frequency', 'Monetary', 'Class']
    rfm_metr['RFMScore'] = rfm_metr.apply(lambda x: f"{x['Recency']}{x['Frequency']}{x['Monetary']}", axis=1)

    rfm_class = rfm_table.merge(rfm_metr[['Class','RFMScore']], on='RFMScore', how='left')
    rfm_class['Class_desc'] = rfm_class['Class'].apply(lambda x: customer_segments_desc[x])
    rfm_class['Class_rec'] = rfm_class['Class'].apply(lambda x: customer_segments_rec[x])
    rfm_class['Class_order'] = rfm_class['Class'].apply(lambda x: customer_segments_order[x])

    # Data for plotting
    df_filtered['Active Customers #'] = df_filtered[['Customer', 'Country']].agg(' '.join, axis=1)
    df_filtered = df_filtered.merge(rfm_class, on='Customer', how='left')

    grouped_df = df_filtered.groupby(['Customer', 'Class_order', 'Class', 'RFMScore', 'Class_desc', 'Class_rec','Recency', 'Frequency','Monetary']).agg(
        {'Total Sales': ['sum'], 'Active Customers #': ['nunique']}).reset_index()
    grouped_df.columns = ['Customer', 'Class_order', 'Class', 'RFMScore', 'Class_desc', 'Class_rec', 'Total Sales', 'Active Customers #','Recency', 'Frequency','Monetary']
    grouped_df['Total Sales %'] = round(grouped_df['Total Sales'] / grouped_df['Total Sales'].sum() * 100, 1)
    grouped_df['Active Customers %'] = round(grouped_df['Active Customers #'] / grouped_df['Active Customers #'].sum() * 100, 1)
    grouped_df.sort_values(by='Class_order', ascending=True, inplace=True, ignore_index=True)

    if class_rfm:
        df = grouped_df[grouped_df['Class'] == class_rfm]

    return df

gradation = {5:'Very High',
             4:'High',
             3:'Intermediate',
             2:'Low',
             1:'Very Low'
            }

def customer_by_rfm(df,
                    class_rfm=None,
                    product=None,
                    country=None,
                    customer=None,
                    metric=None,
                    ):

    #metrics = ['Recency', 'Frequency', 'Monetary']
    #df = data_prepared(df, class_rfm, product, country, customer)
    # DATA
    df = filter_data(df, customer=customer, country=country, product_group=product)
    rfm_table = df.groupby(pd.Grouper(key='Customer')).agg(
                {'Total Sales': ['sum'], 'Total Sold Quantity': ['sum'],
                'DateTime':['min']}).reset_index()
    rfm_table.columns = ['Customer', 'Monetary', 'Frequency', 'Recency']
    rfm_table.sort_values(by=['Monetary','Frequency','Recency'], ascending=False).reset_index().drop(columns=['index']).head() 

    rfm_table['Recency'] = datetime.datetime.today() - rfm_table['Recency']
    rfm_table['Recency'] = pd.Series([x.days for x in rfm_table['Recency']])

    rfm_table['MonetaryRate'] = rate(rfm_table['Monetary'], 'Monetary')
    rfm_table['FrequencyRate'] = rate(rfm_table['Frequency'], 'Frequency')
    rfm_table['RecencyRate'] = rate(rfm_table['Recency']*(-1), 'Recency')

    rfm_table['RFMScore'] = rfm_table.apply(lambda x: f"{x['RecencyRate']}{x['FrequencyRate']}{x['MonetaryRate']}", axis=1)

    rfm_align = pd.read_csv('RFM.csv').drop([0,1,2,3,4])
    iterables = [[i for i in range(5,0,-1)],[i for i in range(5,0,-1)]]
    rfm_align.index = pd.MultiIndex.from_product(iterables, names=['Recency', 'Frequency'])
    rfm_align.drop(columns=['There are 125 possible combinations of profile.', 'Unnamed: 1'], axis=1, inplace=True)
    rfm_align.columns=['5','4','3','2','1']

    rfm_metrics = []
    for i in rfm_align.index:
        for j, el in enumerate(rfm_align.loc[i]):
            rfm_metrics.append([i[0], i[1], 5-j, el])

    rfm_metr = pd.DataFrame(rfm_metrics)
    rfm_metr.columns = ['Recency', 'Frequency', 'Monetary', 'Class']
    rfm_metr['RFMScore'] = rfm_metr.apply(lambda x: f"{x['Recency']}{x['Frequency']}{x['Monetary']}", axis=1)

    rfm_class = rfm_table.merge(rfm_metr[['Class','RFMScore']], on='RFMScore', how='left')

    df = rfm_class
    if class_rfm:
        df = df[df['Class'] == class_rfm]


    df[f'quantiles_{metric}'] = pd.cut(df[metric], bins=len(palette),
                                                 labels=[key for key in palette])
    # PLOTTING
    fig = go.Figure()


    fig.add_trace(
            go.Scatter(
                #df,
                x = df[metric], 
                y = [0.5 for i in range(df.shape[0])],
                mode='markers', 
                hoverinfo='none',
                #name = '',
                marker=dict(
                    size=12,
                    color=df[f'quantiles_{metric}'],  # by Sales Margin %
                ),
            ),
    )
        

    # Update X axis
    fig.update_xaxes(
        showline=False,
        showgrid=False,
        showticklabels=True,
        ticks='',
        tickangle=0,
        title_font_color='grey',
    )

    # Update Y axis
    fig.update_yaxes(
        showgrid=False,
        showline=False,
        showticklabels=False,
    )


    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        autosize=True,
        #height=20,
        margin=dict(l=0,
                    r=0,
                    b=20,
                    t=0,
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

def bar_segment_rfm(df,
                    class_rfm=None,
                    product=None,
                    country=None,
                    customer=None,
                    ):
    metrics = ['Recency', 'Frequency', 'Monetary']    
    currency_sign = get_currency_sign()

    df_total = filter_data(df, customer=customer, country=country, product_group=product)
    df_class = data_prepared(df_total, class_rfm,product,country,customer)[['Customer','Class']]
    df_total = df_total[['Current Date','Total Sales','Customer']].merge(df_class, on='Customer', how='left')
    if class_rfm:
        df_total = df_total[df_total['Class'] == class_rfm]
    
    # DATA
    df = filter_data(df, customer=customer, country=country, product_group=product)
    rfm_table = df.groupby(pd.Grouper(key='Customer')).agg(
                {'Total Sales': ['sum'], 'Total Sold Quantity': ['sum'],
                'DateTime':['min']}).reset_index()
    rfm_table.columns = ['Customer', 'Monetary', 'Frequency', 'Recency']
    rfm_table.sort_values(by=['Monetary','Frequency','Recency'], ascending=False).reset_index().drop(columns=['index']).head() 

    rfm_table['Recency'] = datetime.datetime.today() - rfm_table['Recency']
    rfm_table['Recency'] = pd.Series([x.days for x in rfm_table['Recency']])

    rfm_table['MonetaryRate'] = rate(rfm_table['Monetary'], 'Monetary')
    rfm_table['FrequencyRate'] = rate(rfm_table['Frequency'], 'Frequency')
    rfm_table['RecencyRate'] = rate(rfm_table['Recency']*(-1), 'Recency')

    rfm_table['RFMScore'] = rfm_table.apply(lambda x: f"{x['RecencyRate']}{x['FrequencyRate']}{x['MonetaryRate']}", axis=1)

    rfm_align = pd.read_csv('RFM.csv').drop([0,1,2,3,4])
    iterables = [[i for i in range(5,0,-1)],[i for i in range(5,0,-1)]]
    rfm_align.index = pd.MultiIndex.from_product(iterables, names=['Recency', 'Frequency'])
    rfm_align.drop(columns=['There are 125 possible combinations of profile.', 'Unnamed: 1'], axis=1, inplace=True)
    rfm_align.columns=['5','4','3','2','1']

    rfm_metrics = []
    for i in rfm_align.index:
        for j, el in enumerate(rfm_align.loc[i]):
            rfm_metrics.append([i[0], i[1], 5-j, el])

    rfm_metr = pd.DataFrame(rfm_metrics)
    rfm_metr.columns = ['Recency', 'Frequency', 'Monetary', 'Class']
    rfm_metr['RFMScore'] = rfm_metr.apply(lambda x: f"{x['Recency']}{x['Frequency']}{x['Monetary']}", axis=1)

    rfm_class = rfm_table.merge(rfm_metr[['Class','RFMScore']], on='RFMScore', how='left')

    df = rfm_class     
    if class_rfm:
        df = df[df['Class'] == class_rfm]  

    df['Class_order'] = df['Class'].apply(lambda x: customer_segments_order[x])

    #palette2 = {}
    #for i, c in zip(range(1, len(palette)+1), palette):
    #    palette2[i] = c
    #df['color'] = df['Class_order'].apply(lambda x: palette2[x])

    df_total['quantiles_Total Sales'] = pd.cut(df_total['Total Sales'], bins=len(palette),
                                                   labels=[key for key in palette])
    df['quantiles_recency'] = pd.cut(df['Recency'], bins=len(palette),
                                                 labels=[key for key in palette])
    df['quantiles_frequency'] = pd.cut(df['Frequency'], bins=len(palette),
                                                 labels=[key for key in palette])
    df['quantiles_monetary'] = pd.cut(df['Monetary'], bins=len(palette),
                                                 labels=[key for key in palette])
    df_total['quantiles_sales'] = pd.cut(df_total['Total Sales'], bins=len(palette),
                                                 labels=[key for key in palette])
    # PLOTTING
    fig = make_subplots(
        rows=len(df), cols=4,
        start_cell="top-left",
        column_titles=['Recency', 'Frequency', 'Monetary','Sales over time'],
        #column_widths=[0.75, 0.75, 0.75, 0.15],
        shared_xaxes=True,  # ! important - bars order
        shared_yaxes=True,
        specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}, {'type': 'scatter'}] for i in range(len(df))],
        vertical_spacing=0.01,
        horizontal_spacing=0.0,  # space between the columns
    )
    
    
    # Separate for each year
    #for i, metric in enumerate(metrics):
    for i in range(len(df)):  # fetch row by index
        row = df.iloc[i]
        item = row['Customer']
        rec = row['Recency']
        fre = row['Frequency']
        mon = row['Monetary']
        rfm_prof = row['RFMScore']
        total_sales = df_total[df_total['Customer'] == item]
        #color = row['color']

        #by_item = df[df['Class'] == item]
        #grouped_by_item = by_item.groupby(['Class', 'Customer']).agg({'Total Sales': ['sum']}).reset_index()
        #grouped_by_item.columns = ['Class', 'Customer', 'Total Sales']
        
        l = gradation[int(row['RFMScore'][0])]
        fig.add_trace(
            go.Bar(
                x = [rec],
                y = [f'{item}         {rfm_prof} '+ 15 * ' '], 
                name='',
                text = l,
                textposition='auto',
                texttemplate='%{x} d' + "<br>%{text}" + ' recency',
                orientation='h',
                hoverinfo='none',
                marker={'color': row['quantiles_recency'],
                        'line': {'color': row['quantiles_recency'], 'width': 1},
                       },
            ),
        row=i+1,
        col=1,
        )

        l = gradation[int(row['RFMScore'][1])]
        fig.add_trace(
                go.Bar(
                    x = [fre],
                    y = [f'{item}         {rfm_prof} ' + 15 * ' '],
                    name='',
                    text = l,
                    textposition='auto',
                    texttemplate='%{x}' + "<br>%{text}" + ' frequency',
                    orientation='h',
                    hoverinfo='none',
                    marker={'color': row['quantiles_frequency'],
                            'line': {'color': row['quantiles_frequency'], 'width': 1},
                           },
                ),
            row=i+1,
            col=2,
        )

        l = gradation[int(row['RFMScore'][2])]
        fig.add_trace(
                go.Bar(
                    x =[mon],
                    y = [f'{item}         {rfm_prof} ' + 15 * ' '],  
                    name='',
                    text = l,
                    textposition='auto',
                    texttemplate='%{x}'+ f' {currency_sign}' + "<br>%{text} "+ 'monetary',
                    orientation='h',
                    hoverinfo='none',
                    marker={'color': row['quantiles_monetary'],
                            'line': {'color': row['quantiles_monetary'], 'width': 1},
                           },
                ),
            row=i+1,
            col=3,
        )

        fig.add_trace(
                go.Scatter(
                    x = total_sales['Current Date'], 
                    #y = [f'{item}         {rfm_prof} ' + 15 * ' '],
                    y = [1 for i in range(total_sales.shape[0])],
                    name='',
                    mode='markers', 
                    marker={'color': total_sales['quantiles_sales'],
                            'size': 0.5 + total_sales['Total Sales'] / 100000,
                            'line': {'color': total_sales['quantiles_sales'], 'width': 1},
                           },
                ),
                row=i+1,
                col=4,
        )
    #fig.update_xaxes(
    #        col=1,
    #        #autorange='reversed',
    #        range=[1.3*df[metrics[0]].max(),0],
    #    )
    rang_rec = 1.2 * df['Recency'].max()
    rang_freq = 1.2 * df['Frequency'].max()
    rang_mon = 1.2 * df['Monetary'].max()

    for i in range(len(df)):
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            title_font={'color': 'grey',
                        'size': 10,},
            row=i+1, col=1,
        )

        fig.update_yaxes(
            showgrid=False,
            showline=False,
            showticklabels=True,
            row=i+1, col=1,
        )
        
        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            title_font={'color': 'grey',
                        'size': 10,},
            row=i+1, col=2,
        )

        fig.update_xaxes(
            zeroline=False,
            showline=False,
            showgrid=False,
            showticklabels=False,
            title_font={'color': 'grey',
                        'size': 10,},
            row=i+1, col=3,
        )

        fig.update_yaxes(
            showgrid=False,
            showline=False,
            showticklabels=False,
            row=i+1, col=2,
        )
        fig.update_xaxes(
            autorange='reversed',
            row=i+1, col=1,
        )



    # UPDATE LAYOUT
    fig.update_layout(
        paper_bgcolor='rgb(255,255,255)',  # white
        plot_bgcolor='rgb(255,255,255)',  # white
        showlegend=False,
        autosize=True,
        #barmode="relative",
        #width=600,
        #height=300,
        margin=dict(l=0,
                    r=0,
                    b=0,
                    t=0,
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

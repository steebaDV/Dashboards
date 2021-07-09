import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import datetime
import json
from funcs import font_family, augment_days, filter_data, get_currency_sign, get_palette

with open('params.json', 'r') as f:
	params = json.load(f)

currency_sign = get_currency_sign()


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

#import seaborn as sns
#green_red_palette = sns.diverging_palette(150, 10, n=len(customer_segments_desc.keys())).as_hex()  # palette
palette = get_palette()
palette = [palette[index] for index in range(1, len(palette) + 1)]

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


def get_bars_and_treemaps_rfm(df,
							customer=None,
							country=None,
							product_group=None,
							#max_bars=8,
							palette=palette):

	# Filtering Data
	df_filtered = filter_data(df, customer, country, product_group)

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

	grouped_df = df_filtered.groupby(['Class_order', 'Class', 'Class_desc', 'Class_rec']).agg(
		{'Total Sales': ['sum'], 'Active Customers #': ['nunique']}).reset_index()
	grouped_df.columns = ['Class_order', 'Class', 'Class_desc', 'Class_rec', 'Total Sales', 'Active Customers #']
	grouped_df['Total Sales %'] = round(grouped_df['Total Sales'] / grouped_df['Total Sales'].sum() * 100, 1)
	grouped_df['Active Customers %'] = round(grouped_df['Active Customers #'] / grouped_df['Active Customers #'].sum() * 100, 1)
	grouped_df.sort_values(by='Class_order', ascending=True, inplace=True, ignore_index=True)

	# BINNING AND COLOR   
	#palette2 = {}
	#for i, c in zip(range(1, len(palette)+1), palette):
	#	palette2[i] = c
	#grouped_df['color'] = grouped_df['Class_order'].apply(lambda x: palette2[x])


	#colored_class = grouped_df['Class_order'].unique().tolist()
	#colored_class.reverse()
	#palette2 = {}
	#for c, y in zip(palette, colored_class):
	#	palette2[y] = c
	#grouped_df['color'] = palette2 #colored_class.reverse()

	# Plotting
	fig = make_subplots(
		rows=len(grouped_df), cols=3,
		start_cell="top-left",
		column_titles=['Total Sales', 'Active Customers #', 'Customers <i>(sized and colored by Total Sales)</i>'],
		column_widths=[0.35, 0.35, 0.75],
		shared_xaxes=True,  # ! important - bars order
		shared_yaxes=True,
		specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'domain'}] for i in range(len(grouped_df))],
		horizontal_spacing=0.03,  # space between the columns
	)
	
	hovertext_desc = list(customer_segments_desc.values())
	hovertext_rec = list(customer_segments_rec.values())

	grouped_df['color'] = pd.cut(grouped_df['Class_order'], bins=len(palette),
                                                 labels=[key for key in palette])

	# Iterate DF and fetch one row at a time
	for i in range(len(grouped_df)):  # fetch row by index
		row = grouped_df.iloc[i]
		item = row['Class']
		total_sales = row['Total Sales']
		total_sales_perc = row['Total Sales %']
		active_customers = row['Active Customers #']
		active_customers_perc = row['Active Customers %']
		color = row['color']

		by_item = df_filtered[df_filtered['Class'] == item]
		grouped_by_item = by_item.groupby(['Class', 'Customer']).agg({'Total Sales': ['sum']}).reset_index()
		grouped_by_item.columns = ['Class', 'Customer', 'Total Sales']
		
		# Total Sales
		fig.add_trace(
			go.Bar(
				name='',
				x = [total_sales],  # 1 val
				y = [f'{item} ' + 15 * ' '],  # 1 val
				text = f'{currency_sign} {total_sales:,.0f}<br><i>{total_sales_perc}%</i>',
				# outside value formatting
				textposition='auto',
				marker={'color': color,
						'line': {'color': color, 'width': 1},
					   },
				orientation='h',
				hovertemplate=(f'{hovertext_desc[i]}<br><i>Recommendation:</i><br>{hovertext_rec[i]}' 
							   if hovertext_rec[i] != '' else f'{hovertext_desc[i]}'),
			),
			row=i+1, col=1,
		)
		
		# Active Customers #
		fig.add_trace(
			go.Bar(
				name='',
				x=[active_customers],  # 1 val
				y=[f'{item} ' + 15 * ' '],  # 1 val
				text = f'{active_customers}<br><i>{active_customers_perc}%</i>',
				# outside value formatting
				textposition='auto',
				marker={'color': color,
						'line': {'color': color, 'width': 1},
					   },
				orientation='h',
				hovertemplate=(f'{hovertext_desc[i]}<br><i>Recommendation:</i><br>{hovertext_rec[i]}' 
							   if hovertext_rec[i] != '' else f'{hovertext_desc[i]}'),
			),
			row=i+1, col=2,
		)

		# Treemap Total Sales by Customer
		fig.add_trace(
			go.Treemap(
				name='',
				# ! labels, parents and values are equal sized arrays !
				labels=grouped_by_item['Customer'],
				parents=[item for i in range(len(grouped_by_item))],  # item  or  ' '
				values=grouped_by_item['Total Sales'],  # tree size
				# text=[f'{currency_sign} {t:,.0f}' for t in list(grouped_by_item['Total Sales'])],
				textinfo='label+percent root',
				#marker={'color': color,
						#'line': {'color': color, 'width': 1},
				#	   },
				# hovertemplate='%{label}<br>%{text}'
			),
			row=i+1, col=3
		)

	# UPDATE AXES FOR EACH CHART
	for i in range(len(grouped_df)):
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

		fig.update_yaxes(
			showgrid=False,
			showline=False,
			showticklabels=False,
			row=i+1, col=2,
		)

	# UPDATE LAYOUT
	fig.update_layout(
		paper_bgcolor='white',
		plot_bgcolor='white',
		showlegend=False,
		treemapcolorway=palette,
		margin=dict(l=0,  # !!! SET EXPLICITLY AS PADDING !!!
					r=0,
					b=0,
					t=25,
					# pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
					),
	)

	# SET FONT
	fig.update_layout(
		autosize=True,
		font={
			'family': font_family,
			# 'color': 'black',
			# 'size': 12
		},
	)

	return fig

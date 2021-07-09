import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import calendar
from funcs import font_family, value_format, filter_data, filter_on_date, get_palette, kpis_prep, red_palette, blue_palette

palette = get_palette('dict')


def create_dual_axis_chart(df,
							dates=None,
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
	dates : str
		PDate filter (default None)
	client_type : str
		Client Type filter (default None)
	accident_nature : str
		Accident Nature filter (default None)
	accident_status : str
		Accident Status filter (default None)
	appeal_status : str
		Appeal Status filter (default None)
	palette: dict / list
		Color palette (default palette)
	datefield : datetime, optional
		Date field in the data (default 'Accident Occurrence Date')

	Returns
	-------
	fig 
		Created figure
	"""
	print('*'*100)

	dimensions_left = ['Nb of Victims', 'Total Work Interruption']
	dimensions_right = ['Serious Accidents %', 'Avg Work Interruption']
	dimensions = dimensions_left + dimensions_right

	if dates:
		df = filter_on_date(df, dates)
	df_filtered = filter_data(df, client_type, accident_nature, accident_status, appeal_status)

	df_filtered['Victim Age'] = df_filtered['Victim Birth Date'].apply(lambda x: datetime.now().year - x.year)
	df_filtered['Victim Age Range'] = df_filtered['Victim Age'].apply(lambda x: str(x//5*5)+'-'+str(x//5*5+5))

	fig = make_subplots(
		rows=2, cols=len(df['Accident Nature'].unique()),
		start_cell="top-left",
		shared_xaxes=True,
		shared_yaxes=True,
		specs=[[{"secondary_y": True} for column in range(df_filtered['Accident Nature'].nunique())] for row in range(2)],
		vertical_spacing=0.025,  # space between the rows
		horizontal_spacing=0.025,  # space between the columns
	)

	for index, nature in enumerate(df_filtered['Accident Nature'].unique()):  # columns
		df_filtered2 = df_filtered[df_filtered['Accident Nature'] == nature]
		df_groupby = pd.DataFrame(df_filtered2['Victim Age Range'].drop_duplicates().sort_values().reset_index(drop=True))
		for chart in dimensions:
			column_to_agg, agg = kpis_prep(df_filtered2, chart)
			df_stage = df_filtered2.groupby('Victim Age Range').agg({column_to_agg: [agg]}).reset_index()
			df_stage.columns = ['Victim Age Range', chart]
			df_stage[chart] = df_stage[chart].round(2)
			df_groupby = pd.merge(df_groupby, df_stage, how='left', on='Victim Age Range')

		# ADDING TRACES
		fig.add_trace(
			go.Bar(
				x=df_groupby['Victim Age Range'],
				y=df_groupby[dimensions_left[0]],
				name=nature,
				text=df_groupby[dimensions_left[0]],
				cliponaxis=False,
				textposition='outside',
				# marker_color=df_groupby[f'quantiles_{chart_type}'],
				marker_color=blue_palette[-2],
				orientation='v',
				hovertemplate='%{text}',
			),
			row=1, col=index+1,
		)

		fig.add_trace(
			go.Scatter(
				x=df_groupby['Victim Age Range'],
				y=df_groupby[dimensions_right[0]],
				name=nature,
				mode='lines+text',
				line_color=red_palette[-2],
				text=df_groupby[dimensions_right[0]],
				hovertemplate='%{text}',
			),
			row=1, col=index+1,
			secondary_y=True,
		)

		fig.add_trace(
			go.Scatter(
				x=df_groupby['Victim Age Range'],
				y=df_groupby[dimensions_left[1]],
				name=nature,
				mode='lines',
				fill='tozeroy',
				line_color='#E8E8E8',
				text=df_groupby[dimensions_left[1]],
				hovertemplate='%{text}',
			),
			row=2, col=index+1,
		)

		fig.add_trace(
			go.Scatter(
				x=df_groupby['Victim Age Range'],
				y=df_groupby[dimensions_right[1]],
				name=nature,
				mode='markers+text',
				line_color=blue_palette[-2],
				text=df_groupby[dimensions_right[1]],
				hovertemplate='%{text}',
			),
			row=2, col=index+1,
			secondary_y=True,
		)

		# UPDATING X AXES
		fig.update_xaxes(
			title_text=nature,
			row=1, col=index+1,
			side='top',
		)

	# UPDATING Y AXES
	fig.update_yaxes(
		title_text=dimensions_left[0],
		row=1, col=1,
		secondary_y=False,
	)

	fig.update_yaxes(
		title_text=dimensions_right[0],
		row=1, col=2,
		secondary_y=True,
	)

	fig.update_yaxes(
		title_text=dimensions_left[1],
		row=2, col=1,
		secondary_y=False,
	)

	fig.update_yaxes(
		title_text=dimensions_right[1],
		row=2, col=2,
		secondary_y=True,
	)



	# UPDATING LAYOUT
	fig.update_layout(
		paper_bgcolor='rgb(255,255,255)',  # white
		plot_bgcolor='rgb(255,255,255)',  # white
		showlegend=False,
		autosize=True,
		margin=dict(l=10,  # !!! SET EXPLICITLY AS PADDING !!!
					r=10,
					b=50,
					t=50,
					# pad=0 # Sets the amount of padding (in px) between the plotting area and the axis lines
					),
		font_family=font_family,
		title_text='Accident Nature / Victim Age Range',
		title_x=0.5,
	)

	print('*'*100)

	return fig

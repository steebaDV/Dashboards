import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import pandas as pd
from clickhouse_driver import Client
import dash_table

from dash_bootstrap_components.themes import LITERA
import plotly.graph_objects as go
import numpy as np
from funcs import font_family, set_favicon
import calendar
import json
import warnings
import flask

warnings.filterwarnings(action='ignore')  # 'once'

# TESTING
test = True

with open('config.json', 'r') as f:
    config_file = json.load(f)

dbconfig = config_file['dbconfig'][0]  # dict
db_host, user, password, port, database = dbconfig.values()

tablename = config_file['tablename']

themeSettings = config_file['themeSettings'][0]

logo_img, color, title, description, favicon, background_image, company_name = themeSettings.values()

headings_color = '#007AB9'

# TABS VISIBILITY
tabs_config = config_file['tabs']  # dict
tab_names = [tab['tabname'] for tab in tabs_config if tab['status'] is True]  # tab names to be displayed

tabs_list = [dbc.Tab(label=name, tab_id=name.lower()) for name in tab_names]  # dbc.Tab(label="Main", tab_id="main"),
# DF TO ANALYSE
if not test:
    client = Client(host=db_host,
                    user=user,
                    password=password,
                    port=port,
                    database=database)
else:
    # Test Code
    client = Client(host='54.227.137.142',
                    user='default',
                    password='',
                    port='9000',
                    database='superstore')
    print('TESTING!')

# MATVIEW
column_names_ch = client.execute(f'SHOW CREATE {tablename}')
string = column_names_ch[0][0]
lst = string.split('`')
column_names_duplicated = lst[1::2]
# MAINTAIN THE ORDER
column_names = list(dict.fromkeys(column_names_duplicated))

# DEL
# columns = client.execute((f'SHOW CREATE {tablename}'))
# string = columns[0][0]
# lst = string.split('`')
# column_names = [i for i in lst if lst.index(i) % 2 != 0]  # 14 columns in total
# column_names = column_names[:20]

df = pd.DataFrame(client.execute(f'select * from {tablename}'))
df.columns = column_names
print(column_names)

# SORT BY DATE
df.sort_values(by='DateTime', ascending=True, inplace=True)  # datetime64[ns]
app = dash.Dash(__name__, external_stylesheets=[LITERA], title=title)

# CHANGE CURRENCY SIGN
# df = change_currency_sign(df, currency_sign)

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

logo = html.Img(src=logo_img,  # app.get_asset_url('images/logo.png')
                style={'width': "234px",
                       'height': "80px",
                       'float': 'left',  # position text on the left
                       'margin': '0 30px',  # vertical, horizontal
                       # 'border': '3px solid green',

                       },
                # className='inline-image'
                )

header = html.Div(
    [
        html.H6(
            title,
            style={'position': 'relative',  # center in div
                   'margin-bottom': '0.2rem'
                   # center vertically
                   # 'border': '3px solid green',
                   },
        ),
        html.H4(id='title')

    ])


logo_and_header = dbc.FormGroup(  # in one row
    [
        html.Div(
            [
                logo, header
            ],
            className="p-5",
            style={'width': '60rem',
                   },

        )
    ],
    className='form-row',
    style={'padding-top': '3',
           # 'min-width': '500px',
           # 'width': '60rem',
           # 'padding-left': '50%',
           # 'padding-right': '10%',
           },
)

month = dbc.FormGroup(
    [
        dbc.Label("Current Month", html_for="dropdown"),
        dcc.Dropdown(
            id='current_month',
            value=10,
            options=[{'label': calendar.month_abbr[month_int], 'value': month_int} for month_int in
                     range(1, 13)],
        ),
    ],
    className='form-group col-md-6',
)

year = dbc.FormGroup(
    [
        dbc.Label("Current Year", html_for="dropdown"),
        dcc.Dropdown(
            id='current_year',
            value=2018,
            options=[
                {'label': str(year), 'value': year}
                for year in range(df['Current Year'].min(), df['Current Year'].max() + 1)
            ]
        ),
    ],
    className='form-group col-md-6',
)

year_and_month = dbc.FormGroup(
    [
        month, year
    ],
    className='form-row',
    style={'margin-bottom': '0.1rem'}
)

scope = dbc.FormGroup(
    [
        dbc.Label("Performance Scope", html_for="dropdown"),
        dcc.Dropdown(
            id='scope',
            value='month',
            options=[{'label': 'Current Month vs Previous Month',
                      'value': 'month'}]
        ),
    ],
)

# filters 2
direction = dbc.FormGroup(
    [
        dbc.Label("Call Direction", html_for="dropdown"),
        dcc.Dropdown(
            id='direction',
            value='*ALL*',
            options=[{'label': '*ALL*', 'value': '*ALL*'}] +
                    [{'label': direction, 'value': direction} for direction in np.unique(df['Call Direction'])]
        ),
    ],
)

reason = dbc.FormGroup(
    [
        dbc.Label("Dropped Reason", html_for="dropdown"),
        dcc.Dropdown(
            id='reason',
            value='*ALL*',
            options=[{'label': '*ALL*', 'value': '*ALL*'}] +
                    [{'label': reason, 'value': reason} for reason in np.unique(df['Dropped Reason'])]
        ),
    ],
    style={'margin-bottom': '1.1rem'}  # '1.98rem'
)

# filters 3
network = dbc.FormGroup(
    [
        dbc.Label("NetWork", html_for="dropdown"),
        dcc.Dropdown(
            id='network',
            value='*ALL*',
            options=[{'label': '*ALL*', 'value': '*ALL*'}] +
                    [{'label': network, 'value': network} for network in np.unique(df['Network'])]
        ),
    ],
)

phonetype = dbc.FormGroup(
    [
        dbc.Label("PhoneType", html_for="dropdown"),
        dcc.Dropdown(
            id='phonetype',
            value='*ALL*',
            options=[{'label': '*ALL*', 'value': '*ALL*'}] +
                    [{'label': phonetype, 'value': phonetype} for phonetype in np.unique(df['Phone Type'])]
        ),
    ],
    style={'margin-bottom': '1.1rem'}  # '1.98rem'
)

tabs = html.Div(
    [
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H6(html.I(id='vs'),  # [] children
                                style={'font-size': 14,
                                       'color': 'SteelBlue',
                                       # 'border': '1px solid red',
                                       # 'font-weight': 500,
                                       'margin-top': '-12px',
                                       'margin-bottom': '6px',
                                       'text-align': 'left',
                                       # 'color': headings_color,
                                       # 'margin-left': '0'px',
                                       # 'opacity': 0.4,
                                       },
                                ),
                        html.P(id="card-content"),
                        # style={'height': '50rem'}

                    ], id='background_image'
                ),
            ],
            style={
                'height': '36rem'
                # 'height': '120%',
            },
            id='main_card',
        ),
        dbc.Tabs(
            tabs_list,
            id="card-tabs",
            card=True,
            active_tab='home',
            className='tabs-below',
            style={'margin-top': '1px',
                   'margin-right': '1px',
                   'margin-left': '1px',
                   # place at the very bottom
                   'bottom': '20px',
                   # 'float': 'left', # next element to be placed on the left
                   },
        ),
        html.H6(f"{company_name.upper()} | {title.upper()} | CONFIDENTIAL INFORMATION | FOR INTERVAL USE ONLY",
                style={
                    'color': 'grey',
                    'font-size': 10,
                    # 'border': '1px solid green',
                    'font-weight': 400,
                    'margin-top': '2em',
                    'margin-left': '0.6rem',
                    'margin-bottom':'0.5rem',
                    # 'text-transform': 'uppercase', # ALL LETTERS
                    # 'opacity': 0.4,
                },
                ),

    ]
)
# Table 1
card_height_row1 = '21rem'
card_height_row2 = '10rem'
calls = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Calls", style={'color': 'SteelBlue',
                                        'margin-bottom': '3px', }
                        # style={'font-size': 13,
                        #        'color': headings_color,
                        #        'text-align': 'left',
                        #      # 'border': '1px solid green',
                        #        'font-weight': 'bold',
                        #        'margin-bottom': '-3px',
                        #        'font-family': 'Lato-Regular',
                        # },
                        ),
                dcc.Graph(id='avg_setup_time',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '45%',  # chart height
                              'width': '48%',
                              'float': 'right',
                          },

                          ),
                dcc.Graph(id='total_calls',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '45%',  # chart height
                              'width': '48%',

                          },

                          ),
                dcc.Graph(id='avg_conversation_time',
                          style={
                              # 'border': '1px solid red',
                              'height': '45%',
                              'width': '48%',
                              'float': 'right',
                          },
                          ),
                dcc.Graph(id='pie_chart',
                          style={
                              # 'border': '1px solid black',
                              'height': '45%',
                              'width': '48%',

                          },
                          ),

            ],
            # className='overflow-auto',
            # className='overflow-hidden',
            # display full width and height
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_row1,  # parent height
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
                # 'height':'50%',
                # 'float': 'left',
            },
        ),
    ],
)

dropped_calls = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Dropped Calls", style={'color': 'SteelBlue',
                                                'margin-bottom': '3px', }
                        # style={'font-size': 13,
                        #        'color': headings_color,
                        #        'text-align': 'left',
                        #      # 'border': '1px solid green',
                        #        'font-weight': 'bold',
                        #        'margin-bottom': '-3px',
                        #        'font-family': 'Lato-Regular',
                        # },
                        ),
                dcc.Graph(id='dropped_calls%',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '45%',  # chart height
                              'width': '48%',
                              'float': 'right',
                          },

                          ),
                dcc.Graph(id='dropped_calls',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '45%',  # chart height
                              'width': '48%',

                          },

                          ),
                dcc.Graph(id='dropped_bar_chart',
                          style={
                              # 'border': '1px solid black',
                              'height': '45%',
                              'width': '98%',

                          },
                          ),

            ],
            # className='overflow-auto',
            # className='overflow-hidden',
            # display full width and height
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_row1,  # parent height
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
                # 'height':'50%',
                # 'float': 'left',
            },
        ),
    ],
)

annotations_chart = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Total Calls By Phone Type", style={'color': 'SteelBlue',
                                                            'margin-bottom': '3px', }
                        # style={'font-size': 13,
                        #        'color': headings_color,
                        #        'text-align': 'left',
                        #      # 'border': '1px solid green',
                        #        'font-weight': 'bold',
                        #        'margin-bottom': '-3px',
                        #        'font-family': 'Lato-Regular',
                        # },
                        ),

                dcc.Graph(id='annotations_chart',
                          style={
                              # 'border': '1px solid black',
                              'height': '90%',
                              'width': '98%',

                          },
                          ),

            ],
            # className='overflow-auto',
            # className='overflow-hidden',
            # display full width and height
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_row2,  # parent height
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
                # 'height':'50%',
                # 'float': 'left',
            },
        ),
    ],
)

handovers = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6('Handovers', style={'color': 'SteelBlue',
                                            'margin-bottom': '3px', }
                        # style={'font-size': 13,
                        #        'color': headings_color,
                        #        'text-align': 'left',
                        #      # 'border': '1px solid green',
                        #        'font-weight': 'bold',
                        #        'margin-bottom': '-3px',
                        #        'font-family': 'Lato-Regular',
                        # },
                        ),
                dcc.Graph(id='avg_handovers',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '90%',  # chart height
                              'width': '48%',
                              'float': 'right',
                          },

                          ),
                dcc.Graph(id='total_handovers',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '90%',  # chart height
                              'width': '48%',

                          },

                          ),

            ],
            # className='overflow-auto',
            # className='overflow-hidden',
            # display full width and height
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_row2,  # parent height
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
                # 'height':'50%',
                # 'float': 'left',
            },
        ),
    ],
)

cell_towers = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Cell Towers",
                        style={'color': 'SteelBlue'}
                        # style={'font-size': 13,
                        #        'color': headings_color,
                        #        'text-align': 'left',
                        #      # 'border': '1px solid green',
                        #        'font-weight': 'bold',
                        #        'margin-bottom': '-3px',
                        #        'font-family': 'Lato-Regular',
                        # },
                        ),
                dcc.Graph(id='calls_per_cell_towers',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '18%',  # chart height
                              'width': '48%',
                              'float': 'right',
                          },

                          ),
                dcc.Graph(id='nb_of_cell_towers',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '18%',  # chart height
                              'width': '48%',

                          },

                          ),
                dcc.Graph(id='cell_towers_bar_chart',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '78%',  # chart height
                              'width': '98%',

                          }, )

            ],
            # className='overflow-auto',
            # className='overflow-hidden',
            # display full width and height
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': '32.3rem',  # parent height

                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
                # 'height':'50%',
                # 'float': 'left',
            },
        ),
    ],
)

tab1_row1 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    calls,

                ],
            ),
            dbc.Col(
                [
                    # html.H6("2 INDICATORS", className="card-title"),
                    dropped_calls,

                ],
            ),

        ],
        # style={'margin-bottom': '20px'},
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)

tab1_row2 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    annotations_chart,

                ],
            ),
            dbc.Col(
                [
                    # html.H6("2 INDICATORS", className="card-title"),
                    handovers,

                ]
            ),
        ]
        # style={'margin-bottom': '20px'},
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)
tab1 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    tab1_row1, tab1_row2

                ],
            ),
            dbc.Col(
                [
                    # html.H6("2 INDICATORS", className="card-title"),
                    cell_towers,

                ], width=4
            ),
        ],
        # style={'margin-bottom': '20px'},
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)

# Table 2
card_height_row1 = '15.5rem'
card_height_row2 = '1rem'
card_height_row3 = '15.5rem'

top = html.Div(
    [
        dbc.Label("Top:", html_for="dropdown",
                  style={
                      'margin-right': '0.5rem',
                      'font-family':font_family,
                      'float': 'left',
                      'width': '15%',
                      'font-size':14,
                  }
                  ),
        html.Div(
            dcc.Dropdown(
                id='top',
                value='Last Cell Tower',
                options=[
                    {'label': column, 'value': column} for column in [
                        'Last Cell Tower', 'Dropped Reason', 'Network', 'Phone Type', 'Call Direction']
                ],
                style={
                    'text-align': 'left',
                },
            ), style={'width': '9rem',
                      'font-family':font_family,
                      'font-size':12}
        ),
    ], style={'margin-top': '2rem', }, className="form-inline"
)

by = html.Div(
    [
        dbc.Label("By:", html_for="by_dropdown",
                  style={'margin-right': '0.5rem',
                  'font-family':font_family,
                  'font-size':14,
                  'width': '15%'}),
        html.Div(
            dcc.Dropdown(
                id='by',
                value='Total Calls',
                options=[
                    {'label': column, 'value': column} for column in [
                        'Total Calls', 'Dropped Calls', 'Dropped Calls %', 'Avg Setup Time'
                    ]
                ],
                style={'width': '9rem',
                       'text-align': 'left',
                       'font-family':font_family,
                       'font-size':12,
                               
                },
            ), style={'width': '65%'}, 
            )

    ], style={'margin-top': '2rem', }, className="form-inline"
)

tab2_row1 = dbc.Row([
    # dbc.Col([html.Div([top, by], style={'width': '250px'})], width=2),
    # dbc.Col([
    #     dbc.Container(top, className="form-inline", fluid=True),
    #     dbc.Container(by, className="form-inline")
    # ], width=2),
    dbc.Col([
        top, by

    ], width=2),
    dbc.Col([
        dcc.Graph(id='total_calls',
                  # responsive=True,
                  style={
                      # 'border': '1px solid green',
                      'height': '45%',  # chart height
                      'width': '95%',
                  },
                  ),
        dcc.Graph(id='total_calls_hist1',
                  # responsive=True,
                  style={
                      'height': '50%',  # chart height
                      'width': '95%',
                      'margin-top': '5px'
                  },
                  ),
    ]),
    dbc.Col([
        dcc.Graph(id='dropped_calls',
                  # responsive=True,
                  style={
                      'height': '45%',  # chart height
                      'width': '95%',
                  },
                  ),
        dcc.Graph(id='dropped_calls_hist1',
                  # responsive=True,
                  style={
                      # 'border': '1px solid green',
                      'height': '50%',  # chart height
                      'width': '95%',
                      'margin-top': '5px'
                  },
                  ),

    ]),
    dbc.Col([
        dcc.Graph(id='dropped_calls%',
                  # responsive=True,
                  style={
                      # 'border': '1px solid green',
                      'height': '45%',  # chart height
                      'width': '95%',
                  },
                  ),
        dcc.Graph(id='dropped_calls%_hist1',
                  # responsive=True,
                  style={
                      # 'border': '1px solid green',
                      'height': '50%',  # chart height
                      'width': '95%',
                      'margin-top': '5px'
                  },
                  ),

    ]),
    dbc.Col([
        dcc.Graph(id='avg_setup_time',
                  # responsive=True,
                  style={
                      # 'border': '1px solid green',
                      'height': '45%',  # chart height
                      'width': '95%',
                  },
                  ),
        dcc.Graph(id='avg_setup_time_hist1',
                  # responsive=True,
                  style={
                      # 'border': '1px solid green',
                      'height': '50%',  # chart height
                      'width': '95%',
                      'margin-top': '5px'
                  },
                  ),
    ]),
], style={'height': card_height_row1})

tab2_row2 = dbc.Row([
    dbc.Col([], width=2),
    dbc.Col([
        html.H6('TOTAL CALLS',
                style={'color': 'white',
                       'background': 'grey',
                       'text-align': 'center',
                       'margin-up': '15px'}
                ),

    ]),
    dbc.Col([
        html.H6('DROPPED CALLS',
                style={'color': 'white',
                       'background': 'grey',
                       'text-align': 'center',
                       'margin-up': '15px'}
                ),

    ]),
    dbc.Col([
        html.H6('DROPPED CALLS %',
                style={'color': 'white',
                       'background': 'grey',
                       'text-align': 'center',
                       'margin-up': '15px'}
                ),

    ]),
    dbc.Col([
        html.H6('AVG SETUP TIME',
                style={'color': 'white',
                       'background': 'grey',
                       'text-align': 'center',
                       'margin-up': '15px'}
                ),
    ]),
], style={'height': card_height_row2})

tab2_row3 = dbc.Row([
    dbc.Col([dcc.Graph(id='vertical_hist',
                       # responsive=True,
                       style={
                           # 'border': '1px solid green',
                           'height': '95%',  # chart height
                           'width': '100%',
                           #
                       },
                       ), ], width=2),
    dbc.Col([
        dcc.Graph(id='vertical_hists',
                  # responsive=True,
                  style={
                      # 'border': '1px solid green',
                      'height': '95%',  # chart height
                      'width': '100%',
                      #
                  },
                  ),

    ]),
], style={'height': card_height_row3})

tab2 = dbc.Card([
    dbc.CardBody([
        html.H6(id='performance_by',
                style={'color': 'SteelBlue'}
                ),
        tab2_row1, tab2_row2, tab2_row3
    ], style={
        'padding': '3px 5px 3px',  # top, right/left, bottom
        'height': '32.3rem',  # parent height

        # 'border': '2px solid green',
        # 'margin-bottom': '0.1rem',
        # 'height':'50%',
        # 'float': 'left',
    }, )
])

# TABLE 3
card_height_row1 = '32.3rem'

tab3_col1 = dbc.Card(
    [
        dbc.CardBody([
            html.H6("Total Calls",
                    style={'color': 'SteelBlue',
                           'margin-bottom': '3px',
                           }),
            dcc.Graph(id='total_calls_mtd_ytd',
                      style={
                          'height': '95%',  # chart height
                          'width': '95%',
                          #
                      }),
        ], style={
            'padding': '3px 5px 3px',  # top, right/left, bottom
            'height': card_height_row1,

        })
    ]
)

tab3_col2 = dbc.Card(
    [
        dbc.CardBody([
            html.H6("Dropped Calls",
                    style={'color': 'SteelBlue',
                           'margin-bottom': '3px',
                           }),
            dcc.Graph(id='dropped_calls_mtd_ytd',
                      style={
                          'height': '95%',  # chart height
                          'width': '95%',
                          #
                      }),
        ], style=
        {
            'padding': '3px 5px 3px',  # top, right/left, bottom
            'height': card_height_row1,

        })
    ]
)

tab3_col3 = dbc.Card(
    [
        dbc.CardBody([
            html.H6("Dropped Calls %",
                    style={'color': 'SteelBlue',
                           'margin-bottom': '3px',
                           }),
            dcc.Graph(id='dropped_calls_percent_mtd_ytd',
                      style={
                          'height': '95%',  # chart height
                          'width': '95%',
                          #
                      }),
        ], style=
        {
            'padding': '3px 5px 3px',  # top, right/left, bottom
            'height': card_height_row1,

        })
    ]
)

tab3_col4 = dbc.Card(
    [
        dbc.CardBody([
            html.H6("Avg Setup Time",
                    style={'color': 'SteelBlue',
                           'margin-bottom': '3px',
                           }),
            dcc.Graph(id='avg_setup_time_mtd_ytd',
                      style={
                          'height': '95%',  # chart height
                          'width': '95%',
                          #
                      }),
        ], style=
        {
            'padding': '3px 5px 3px',  # top, right/left, bottom
            'height': card_height_row1,

        })
    ]
)

tab3 = dbc.Row([
    html.Div(
        [
            html.H6("MONTH-TO-DATE",
                    style={
                        'writing-mode': 'vertical-rl',
                        'transform': 'rotate(-180deg)',
                        'height': '35%',
                        'text-align': 'center',
                        # 'border': '1px solid yellow',
                    }
                    ),
            html.H6("YEAR-TO-DATE",
                    style={
                        'writing-mode': 'vertical-rl',
                        'transform': 'rotate(-180deg)',
                        'height': '33%',  # vertical centering relatively charts
                        'text-align': 'center',
                        # 'border': '1px solid green',
                    }
                    ),
        ],
        style={'clear': 'right',
               'margin-left': '-1.5rem',  # from the left
               'margin-right': '-1.5rem',  # from the right

               }
    ),  # div
    dbc.Col(tab3_col1),
    dbc.Col(tab3_col2),
    dbc.Col(tab3_col3),
    dbc.Col(tab3_col4),
])

# TABLE 4
card_height_row1 = '14rem'
card_height_row2 = '14rem'

tab4_by = dbc.FormGroup(
    [
        html.Div([
            dbc.Label("By:", html_for="dropdown", style={'margin-right': '1rem',
                                                        'font-family':font_family}),
            dcc.Dropdown(
                id='column_to_group_by',
                value='Phone Type',
                options=[
                    {'label': column, 'value': column} for column in [
                        'Last Cell Tower', 'Dropped Reason', 'Network', 'Phone Type', 'Call Direction']
                ], 
                style={'float': 'right', 
                       'width': '8rem',
                       'text-align':'left',
                       'font-family':font_family}
            ),
        ], className="form-inline")
    ],
    className='form-group col-md-6',
)

tab4_show = dbc.FormGroup(
    [
        html.Div([
            dbc.Label("Show:", html_for="dropdown", style={'margin-right': '1rem',
                                                           'font-family':font_family}),
            dcc.Dropdown(
                id='kpi',
                value='Dropped Calls',
                options=[
                    {'label': column, 'value': column} for column in [
                        'Total Calls', 'Dropped Calls', 'Dropped Calls %', 'Avg Setup Time'
                    ]
                ], 
                style={'width': '10rem',
                       'text-align': 'left',
                       'font-family':font_family
                      },
            ),
        ], className="form-inline")

    ],
    className='form-group col-md-6',
)

tab4_filters = dbc.Row([
    dbc.Col(),
    dbc.Col(
        [
            dbc.CardBody(
                [
                    dbc.FormGroup(
                        [tab4_show, tab4_by],
                        className='form-row',
                        style={'margin-bottom': '0.1rem'}
                    )
                ],
                style={'font-size': '14px',
                       'margin-bottom': 0,
                       'margin-left': 3,
                       'padding-right': 0,
                       'height': '4rem',

                       # 'border': '1px solid green',

                       },
            ),
        ],
        width=5,  # col width
        style={
            # 'border': '1px solid red',
            'padding-right': 0,
        },
    ),
])


tab4_row1 = dbc.Row([
    dbc.Col(
        dbc.Card(
            [
                dbc.CardBody([
                    html.H6(children='Dropped Calls Trends',
                            id='adhoc_name1',
                            style={'color': 'SteelBlue',
                                   'margin-bottom': '3px',
                                   }),
                    dcc.Graph(id='trend_graph',
                              style={
                                  'height': '95%',  # chart height
                                  'width': '95%',
                                  'padding-bottom': '10px'
                                  #
                              }),
                ], style=
                {
                    'height': card_height_row1,
                    'padding': '3px 5px 3px',  # top, right/left, bottom

                })
            ]
        )
    ),
    dbc.Col(
        dbc.Card(
            [
                dbc.CardBody([
                    html.H6(children="Dropped Calls by Phone Type",
                            id='adhoc_name2',
                            style={'color': 'SteelBlue',
                                   'margin-bottom': '3px',
                                   }),
                    dcc.Graph(id='distribution_graph',
                              style={
                                  'height': '95%',  # chart height
                                  'width': '95%',
                                  'padding-bottom': '10px'
                                  #
                              }),
                ], style=
                {
                    'height': card_height_row1,
                    'padding': '3px 5px 3px',  # top, right/left, bottom

                })
            ]
        )
    )
], style={'margin-bottom': '20px'})

tab4_row2 = dbc.Row([
    dbc.Col(
        dbc.Card(
            [
                dbc.CardBody([
                    html.H6("Pareto Analysis",
                            style={'color': 'SteelBlue',
                                   'margin-bottom': '3px',
                                   }),
                    dcc.Graph(id='pareto_analysis',
                              style={
                                  'height': '95%',  # chart height
                                  'width': '95%',
                                  'padding-bottom': '10px',
                                  #
                              }),
                ], style=
                {
                    'height': card_height_row2,
                    'padding': '3px 5px 3px',  # top, right/left, bottom

                })
            ]
        )
    )
], style={'margin-bottom': '20px'})

tab4 = html.Div([
    tab4_filters, tab4_row1, tab4_row2
])

# TABLE 5
card_height_row1 = '32.3rem'

tab5_col1 = dbc.Card(
    [
        dbc.CardBody([
            html.H6("Dropped Calls",
                    style={'color': 'SteelBlue',
                           'margin-bottom': '3px',
                           }),
            dcc.Graph(id='dropped_calls',
                      style={
                          'height': '25%',  # chart height
                          'width': '95%',
                          #
                      }),
            dcc.Graph(id='dropped_bar_chart',
                      style={
                          'height': '25%',  # chart height
                          'width': '95%',
                          #
                      }),
            dcc.Graph(id='dropped_calls%',
                      style={
                          'height': '25%',  # chart height
                          'width': '95%',
                          #
                      }),
        ], style=
        {
            'padding': '3px 5px 3px',  # top, right/left, bottom
            'height': card_height_row1,

        })
    ]
)

tab5_col2 = dbc.Card(
    [
        dbc.CardBody([
            html.H6("Dropped Calls per Cell Tower",
                    style={'color': 'SteelBlue',
                           'margin-bottom': '3px',
                           }),
            dcc.Graph(id='dropped_calls_per_cell_tower_scatter',
                      style={
                          'height': '45%',  # chart height
                          'width': '95%',
                          #
                      }),
            dcc.Graph(id='dropped_calls_per_cell_tower_hist',
                      style={
                          'height': '45%',  # chart height
                          'width': '95%',
                          #
                      }),
        ], style=
        {
            'padding': '3px 5px 3px',  # top, right/left, bottom
            'height': card_height_row1,

        })
    ]
)

tab5_col3 = dbc.Card(
    [
        dbc.CardBody([
            html.H6("Hourly Statistics",
                    style={'color': 'SteelBlue',
                           'margin-bottom': '3px',
                           }),
            dcc.Graph(id='hourly_statistics',
                      style={
                          'height': '95%',  # chart height
                          'width': '95%',
                          #
                      }),
        ], style=
        {
            'padding': '3px 5px 3px',  # top, right/left, bottom
            'height': card_height_row1,

        })
    ]
)

tab5 = dbc.Row([
    dbc.Col(tab5_col1),
    dbc.Col(tab5_col2),
    dbc.Col(tab5_col3)
])

# TABLE 6
# 'margin-bottom': '20px'
card_height_row1 = '23rem'

tab6_split_by = dbc.FormGroup(
    [
        html.Div([
            dbc.Label("Split By:", html_for="dropdown", 
                      style={'margin-right': '1rem',
                             'font-family':font_family
                            }),
            dcc.Dropdown(
                id='split_by',
                value='Year x Month',
                options=[
                    {'label': column, 'value': column} for column in [
                        'Year x Month', 'Month x Week', 'Week x Hour', 'Week x Day of Week']
                ], style={'float': 'right',
                          'width': '10rem',
                          'text-align':'left',
                          'font-family':font_family}
            ),
        ], className="form-inline")
    ],
    className='form-group col-md-6',
)

#tab4_show = dbc.FormGroup(
#    [
#        html.Div([
#            dbc.Label("Show", html_for="dropdown", style={'float': 'left'}),
#            dcc.Dropdown(
#                id='kpi',
#                value='Dropped Calls',
#                options=[
#                    {'label': column, 'value': column} for column in [
#                        'Total Calls', 'Dropped Calls', 'Dropped Calls %', 'Avg Setup Time'
#                    ]
#                ], style={'float': 'right', 'width': '8rem'}
#            ),
#        ], className="form-inline")

#    ],
#    className='form-group col-md-6',
#)

tab6_filters = dbc.Row([
    dbc.Col(),
    dbc.Col(
        [
            dbc.CardBody(
                [
                    dbc.FormGroup(
                        [tab4_show, tab6_split_by],
                        className='form-row',
                        style={'margin-bottom': '0.1rem'}
                    )
                ],
                style={'font-size': '14px',
                       'margin-bottom': 0,
                       'padding-right': 0,
                       'height': '4rem',

                       # 'border': '1px solid green',

                       },
            ),
        ],
        width=5,  # col width
        style={
            # 'border': '1px solid red',
            'padding-right': 0,
        },
    ),
])

tab6 = html.Div(
    [
        tab6_filters,
        dbc.Card(
            [
                dbc.CardBody(
                    [

                        dcc.Graph(id='heatmap',
                                  style={
                                      'height': '95%',  # chart height
                                      'width': '95%',
                                      #
                                  }),

                    ], style={
                        'padding': '3px 5px 3px',  # top, right/left, bottom

                    })
            ])
    ])

app.layout = html.Div(
    [
        # Filters
        dbc.Container(
            [
                html.Hr(
                    style={'width': '100%'},
                ),
                # children - array
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.CardBody(
                                    [
                                        logo_and_header,

                                    ], style={'margin-top': '-35px'}
                                )
                            ],
                            # width=7,

                        ),  # header

                        dbc.Col(  # filters 1
                            [
                                dbc.CardBody(
                                    [
                                        year_and_month, scope
                                    ],
                                    style={'font-size': '14px',
                                           'margin-bottom': 0,
                                           'padding-right': 0,
                                           # 'border': '1px solid green',

                                           },
                                ),
                            ],
                            width=3,  # col width
                            style={
                                # 'border': '1px solid red',
                                'padding-right': 0,
                            },
                        ),

                        dbc.Col(  # filters 3
                            [
                                dbc.CardBody(
                                    [
                                        direction, reason
                                    ],
                                    style={
                                        'font-size': '14px',
                                        'margin-bottom': 0,
                                        'padding-right': 0,
                                        'padding-left': 0,
                                        # 'border': '1px solid black',
                                    },
                                ),
                            ],
                            width=2,
                            style={
                                # 'border': '1px solid red',
                                'padding-left': '0.5em',
                                'padding-right': 0,
                            },

                        ),
                        dbc.Col(  # filters 2
                            [
                                dbc.CardBody(
                                    [
                                        network, phonetype
                                    ],
                                    style={
                                        'font-size': '14px',
                                        'margin-bottom': 0,
                                        'padding-right': 0,
                                        'padding-left': 0,
                                        # 'border': '1px solid black',
                                    },
                                ),
                            ],
                            width=2,
                            style={
                                # 'border': '1px solid red',
                                'padding-left': '0.5em',
                            },

                        ),

                    ],
                    style={
                        #  'font-size': '14px',
                        'margin-bottom': 0,
                        'padding': '0px 0px 0px',
                        # 'border': '1px solid green',
                        'height': '12rem',
                        # 'max-height': '80%',
                    },
                ),
                html.Hr(
                    style={'width': '100%'},
                ),

            ],
            fluid=True,
            id='filters_pane',

        ),
        tabs,

    ],
    style={'font-family': font_family}
)

from graph import \
    get_indicator_plot, \
    get_bar_chart, \
    get_vertical_bar_chart, \
    prev, get_dropped_bar_chart, \
    get_pie_chart, \
    get_cell_towers_bar_chart, \
    get_annotations_chart, \
    get_top_kpi_trends, \
    get_heatmap


@app.callback(

    [
        Output("card-content", 'children'),
        Output("title", 'children'),
        Output("filters_pane", "style"),
        Output("main_card", "style"),
        Output("background_image", "style")
    ],
    [Input("card-tabs", 'active_tab')]
)
def filter_and_graph(active_tab):
    filters_pane_style = None
    main_card_style = {
        'height': '36rem'
    }
    background = None
    if active_tab == 'top perfomers':
        return tab1, 'Top Perfomers', filters_pane_style, main_card_style, background
    elif active_tab == 'cockpit':
        return tab2, 'Cockpit', filters_pane_style, main_card_style, background
    elif active_tab == 'top 4 kpis trends (mtd/ytd)':
        return tab3, 'Top 4 KPIs Trends (MTD/YTD)', filters_pane_style, main_card_style, background
    elif active_tab == 'adhoc analysis':
        return tab4, 'Adhoc Analysis', filters_pane_style, main_card_style, background
    elif active_tab == 'dropped calls':
        return tab5, 'Dropped Calls', filters_pane_style, main_card_style, background
    elif active_tab == 'seasonality analysis':
        return tab6, 'Seasonality Analysis', filters_pane_style, main_card_style, background
    elif active_tab == 'home':  # keep it last
        children = html.Div(  # content
            [
                html.H1(title, style={'color': headings_color}),
                html.Hr(className='raacom-hr'),
                html.H6(company_name, style={'font-size': '14px'}),
            ],
            style={'padding-top': '18%',
                   #'margiin-left':'0.1rem',
                   #`'margin-bottom':'0.1rem',
                   'text-align': 'left',
                   },
        )  # content
        filters_pane_style = {'display': 'none'}  # filters_pane
        main_card_style = {
            'height': '52rem'
        }
        background = {
            'background-image': f'url({background_image})',
            'background-size': '100%'
        }
        return children, '', filters_pane_style, main_card_style, background


@app.callback(

    Output("total_calls", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def total_calls(current_month, current_year, direction, reason, network, phonetype):
    fig = get_indicator_plot(df,
                             current_year=current_year,
                             current_month=current_month,  # 1..12
                             chart_type='Total Calls',
                             call_direction=direction,
                             dropped_reason=reason,
                             network=network,
                             phonetype=phonetype
                             )
    return fig


@app.callback(
    Output('performance_by', 'children'),
    [Input('top', 'value')],
)
def perfomance_by(top):
    return f'Perfomance by {top}'


@app.callback(
    Output('vs', 'children'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input("card-tabs", 'active_tab')
    ]
)
def vs(current_month, current_year, active_tab):
    if active_tab == 'Top Perfomers' or active_tab == 'Cockpit' or active_tab == 'Dropped Calls':
        prev_year, prev_month, current_year, current_month = prev(current_year, current_month)
        return f'{current_month}-{str(current_year)[-2:]} vs {prev_month}-{str(prev_year)[-2:]}'
    else:
        return ''


@app.callback(
    Output("dropped_calls", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def dropped_calls(current_month, current_year, direction, reason, network, phonetype):
    fig = get_indicator_plot(df,
                             current_year=current_year,
                             current_month=current_month,  # 1..12
                             chart_type='Dropped Calls',
                             call_direction=direction,
                             dropped_reason=reason,
                             network=network,
                             phonetype=phonetype
                             )
    return fig


@app.callback(
    Output("dropped_calls%", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def dropped_calls_percent(current_month, current_year, direction, reason, network, phonetype):
    fig = get_indicator_plot(df,
                             current_year=current_year,
                             current_month=current_month,  # 1..12
                             chart_type='Dropped Calls %',
                             call_direction=direction,
                             dropped_reason=reason,
                             network=network,
                             phonetype=phonetype
                             )
    return fig


@app.callback(
    Output("dropped_bar_chart", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def dropped_bar_chart(current_month, current_year, direction, reason, network, phonetype):
    fig = get_dropped_bar_chart(df,
                                current_year=current_year,
                                current_month=current_month,  # 1..12
                                call_direction=direction,
                                dropped_reason=reason,
                                network=network,
                                phonetype=phonetype
                                )
    return fig


@app.callback(
    Output("avg_setup_time", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def avg_setup_time(current_month, current_year, direction, reason, network, phonetype):
    fig = get_indicator_plot(df,
                             current_year=current_year,
                             current_month=current_month,  # 1..12
                             chart_type='Avg Setup Time',
                             call_direction=direction,
                             dropped_reason=reason,
                             network=network,
                             phonetype=phonetype
                             )
    return fig


@app.callback(
    Output("avg_conversation_time", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def avg_conversation_time(current_month, current_year, direction, reason, network, phonetype):
    fig = get_indicator_plot(df,
                             current_year=current_year,
                             current_month=current_month,  # 1..12
                             chart_type='Avg Conversation Time',
                             call_direction=direction,
                             dropped_reason=reason,
                             network=network,
                             phonetype=phonetype
                             )
    return fig


@app.callback(

    Output("avg_handovers", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def avg_handovers(current_month, current_year, direction, reason, network, phonetype):
    fig = get_indicator_plot(df,
                             current_year=current_year,
                             current_month=current_month,  # 1..12
                             chart_type='Avg Handovers',
                             call_direction=direction,
                             dropped_reason=reason,
                             network=network,
                             phonetype=phonetype
                             )
    return fig


@app.callback(

    Output("pie_chart", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def pie_chart(current_month, current_year, direction, reason, network, phonetype):
    fig = get_pie_chart(df,
                        current_year=current_year,
                        current_month=current_month,  # 1..12
                        call_direction=direction,
                        dropped_reason=reason,
                        network=network,
                        phonetype=phonetype
                        )
    return fig


@app.callback(

    Output("total_handovers", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def total_handovers(current_month, current_year, direction, reason, network, phonetype):
    fig = get_indicator_plot(df,
                             current_year=current_year,
                             current_month=current_month,  # 1..12
                             chart_type='Total Handovers',
                             call_direction=direction,
                             dropped_reason=reason,
                             network=network,
                             phonetype=phonetype
                             )
    return fig


@app.callback(

    Output("nb_of_cell_towers", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def avg_setup_time(current_month, current_year, direction, reason, network, phonetype):
    fig = get_indicator_plot(df,
                             current_year=current_year,
                             current_month=current_month,  # 1..12
                             chart_type='Nb of Cell Towers',
                             call_direction=direction,
                             dropped_reason=reason,
                             network=network,
                             phonetype=phonetype
                             )
    return fig


@app.callback(
    Output("calls_per_cell_towers", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def avg_setup_time(current_month, current_year, direction, reason, network, phonetype):
    fig = get_indicator_plot(df,
                             current_year=current_year,
                             current_month=current_month,  # 1..12
                             chart_type='Calls per Cell Tower',
                             call_direction=direction,
                             dropped_reason=reason,
                             network=network,
                             phonetype=phonetype
                             )
    return fig


@app.callback(
    Output('annotations_chart', 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def annotations_chart(current_month, current_year, direction, reason, network, phonetype):
    fig = get_annotations_chart(df,
                                current_year=current_year,
                                current_month=current_month,  # 1..12
                                call_direction=direction,
                                dropped_reason=reason,
                                network=network,
                                phonetype=phonetype
                                )
    return fig


@app.callback(
    Output("cell_towers_bar_chart", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def cell_towers_bar_chart(current_month, current_year, direction, reason, network, phonetype):
    fig = get_cell_towers_bar_chart(df,
                                    current_year=current_year,
                                    current_month=current_month,  # 1..12
                                    call_direction=direction,
                                    dropped_reason=reason,
                                    network=network,
                                    phonetype=phonetype
                                    )
    return fig


@app.callback(
    Output("total_calls_hist1", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def total_calls_hist(current_month, current_year, direction, reason, network, phonetype):
    fig = get_bar_chart(df,
                        current_year=current_year,
                        current_month=current_month,  # 1..12
                        chart_type='Total Calls Hist',
                        call_direction=direction,
                        dropped_reason=reason,
                        network=network,
                        phonetype=phonetype
                        )
    return fig


@app.callback(
    Output("dropped_calls_hist1", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def dropped_calls_hist(current_month, current_year, direction, reason, network, phonetype):
    fig = get_bar_chart(df,
                        current_year=current_year,
                        current_month=current_month,  # 1..12
                        chart_type='Dropped Calls Hist',
                        call_direction=direction,
                        dropped_reason=reason,
                        network=network,
                        phonetype=phonetype
                        )
    return fig


@app.callback(
    Output("dropped_calls%_hist1", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def dropped_calls_percent_hist(current_month, current_year, direction, reason, network, phonetype):
    fig = get_bar_chart(df,
                        current_year=current_year,
                        current_month=current_month,  # 1..12
                        chart_type='Dropped Calls % Hist',
                        call_direction=direction,
                        dropped_reason=reason,
                        network=network,
                        phonetype=phonetype
                        )
    return fig


@app.callback(
    Output("avg_setup_time_hist1", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def avg_setup_time_hist(current_month, current_year, direction, reason, network, phonetype):
    fig = get_bar_chart(df,
                        current_year=current_year,
                        current_month=current_month,  # 1..12
                        chart_type='Avg Setup Time Hist',
                        call_direction=direction,
                        dropped_reason=reason,
                        network=network,
                        phonetype=phonetype
                        )
    return fig


@app.callback(
    Output("vertical_hists", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
        Input('top', 'value'),
        Input('by', 'value'),
    ]
)
def vertical_hists(current_month, current_year, direction, reason, network, phonetype, top, by):
    fig = get_vertical_bar_chart(df,
                                 current_year=current_year,
                                 current_month=current_month,  # 1..12
                                 chart='right',
                                 call_direction=direction,
                                 dropped_reason=reason,
                                 network=network,
                                 phonetype=phonetype,
                                 top=top,
                                 by=by
                                 )
    return fig


@app.callback(
    Output("vertical_hist", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
        Input('top', 'value'),
        Input('by', 'value'),
    ]
)
def vertical_hists(current_month, current_year, direction, reason, network, phonetype, top, by):
    fig = get_vertical_bar_chart(df,
                                 current_year=current_year,
                                 current_month=current_month,  # 1..12
                                 chart='left',
                                 call_direction=direction,
                                 dropped_reason=reason,
                                 network=network,
                                 phonetype=phonetype,
                                 top=top,
                                 by=by
                                 )
    return fig


@app.callback(
    Output('total_calls_mtd_ytd', 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ])
def total_calls_mtd_ytd(current_month, current_year, direction, reason, network, phonetype):
    return get_top_kpi_trends(df,
                       month_int=current_month,
                       year=current_year,
                       chart='Total Calls',
                       call_direction=direction,
                       phone_type=phonetype,
                       network=network,
                       dropped_reason=reason)


@app.callback(
    Output('dropped_calls_mtd_ytd', 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ])
def dropped_calls_mtd_ytd(current_month, current_year, direction, reason, network, phonetype):
    return get_top_kpi_trends(df,
                       month_int=current_month,
                       year=current_year,
                       chart='Dropped Calls',
                       call_direction=direction,
                       phone_type=phonetype,
                       network=network,
                       dropped_reason=reason)


@app.callback(
    Output('dropped_calls_percent_mtd_ytd', 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),

        # Input('scope_dropdown', 'value'),
    ])
def dropped_calls_percent_mtd_ytd(current_month, current_year, direction, reason, network, phonetype):
        return get_top_kpi_trends(df,
                       month_int=current_month,
                       year=current_year,
                       chart='Dropped Calls %',
                       call_direction=direction,
                       phone_type=phonetype,
                       network=network,
                       dropped_reason=reason)


@app.callback(
    Output('avg_setup_time_mtd_ytd', 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),

        # Input('scope_dropdown', 'value'),
    ])
def avg_setup_time_mtd_ytd(current_month, current_year, direction, reason, network, phonetype):
        return get_top_kpi_trends(df,
                       month_int=current_month,
                       year=current_year,
                       chart='Avg Setup Time',
                       call_direction=direction,
                       phone_type=phonetype,
                       network=network,
                       dropped_reason=reason)


# ADHOC
from adhoc import get_trend_graph, get_distribution_graph, get_pareto_analysis


@app.callback(
    Output("trend_graph", 'figure'),
    [
        # Input('current_month', 'value'),
        # Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
        Input('column_to_group_by', 'value'),
        Input('kpi', 'value'),
    ]
)
def trend_graph(direction, reason, network, phonetype, column_to_group_by, kpi):
    fig = get_trend_graph(df,
                          kpi=kpi,
                          call_direction=direction,
                          reason=reason,
                          network=network,
                          phone_type=phonetype,
                          dates='last 17 months'
                          )
    return fig


@app.callback(
    Output("distribution_graph", 'figure'),
    [
        # Input('current_month', 'value'),
        # Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
        Input('column_to_group_by', 'value'),
        Input('kpi', 'value'),
    ]
)
def distribution_graph(direction, reason, network, phonetype, column_to_group_by, kpi):
    fig = get_distribution_graph(df,
                                 kpi=kpi,
                                 column_to_group_by=column_to_group_by,
                                 call_direction=direction,
                                 reason=reason,
                                 network=network,
                                 phone_type=phonetype,
                                 dates='last 17 months'
                                 )
    return fig


@app.callback(
    Output("pareto_analysis", 'figure'),
    [
        # Input('current_month', 'value'),
        # Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
        # Input('column_to_group_by', 'value'),
        Input('kpi', 'value'),
    ]
)
def pareto_analysis(direction, reason, network, phonetype, kpi):
    fig = get_pareto_analysis(df,
                              kpi=kpi,
                              call_direction=direction,
                              reason=reason,
                              network=network,
                              phone_type=phonetype,
                              dates='last 17 months'
                              )
    return fig

@app.callback(
    Output("adhoc_name1", 'children'),
    [
        Input('kpi', 'value'),
    ]
)
def update_adhoc_titles(kpi):
    return str(kpi) + ' Trends'

@app.callback(
    Output("adhoc_name2", 'children'),
    [
        Input('kpi', 'value'),
        Input('column_to_group_by', 'value'),
    ]
)
def update_adhoc_titles(kpi, by):
    return str(kpi) + ' by ' + str(by)


@app.callback(
    Output("heatmap", 'figure'),
    [
        # Input('current_month', 'value'),
        # Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
        Input('split_by', 'value'),
        Input('kpi', 'value'),
    ]
)
def heatmap(direction, reason, network, phonetype, split_by, kpi):
    fig = get_heatmap(df,
                      kpi=kpi,
                      dimension=split_by,
                      call_direction=direction,
                      reason=reason,
                      network=network,
                      phone_type=phonetype,
                      dates='last 17 months'
                      )
    return fig


from bar_dropped import \
    get_bar_charts_h, \
    get_hourly_statistics, \
    dropped_calls_tower


@app.callback(
    Output("hourly_statistics", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def hourly_statistics(current_month, current_year, direction, reason, network, phonetype):
    fig = get_hourly_statistics(
        month_int=current_month,
        year=current_year,
        df=df,
        call_direction=direction,
        dropped_reason=reason,
        network=network,
        phone_type=phonetype,
    )
    return fig


@app.callback(
    Output("dropped_calls_per_cell_tower_scatter", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def dropped_calls_per_cell_tower_scatter(current_month, current_year, direction, reason, network, phonetype):
    fig = dropped_calls_tower(
        month_int=current_month,
        year=current_year,
        df=df,
        call_direction=direction,
        dropped_reason=reason,
        network=network,
        phone_type=phonetype,
    )
    return fig


@app.callback(
    Output("dropped_calls_per_cell_tower_hist", 'figure'),
    [
        Input('current_month', 'value'),
        Input('current_year', 'value'),
        Input('direction', 'value'),
        Input('reason', 'value'),
        Input('network', 'value'),
        Input('phonetype', 'value'),
    ]
)
def dropped_calls_per_cell_tower_hist(current_month, current_year, direction, reason, network, phonetype):
    fig = get_bar_charts_h(
        month_int=current_month,
        year=current_year,
        df=df,
        max_bars=10,
        column_to_group_by='Phone Type',
        bar_charts=['Total Calls', 'Dropped Calls %', 'Dropped Calls'],
        call_direction=direction,
        dropped_reason=reason,
        network=network,
        phone_type=phonetype,
    )
    return fig


# -----------------------------------------------------------------------------------------------------------------------

set_favicon(favicon)

application = app.server
if not test:
    server = app.server

if __name__ == '__main__':
    if not test:
        # FOR ALIBABA CLOUD
        app.run_server(debug=False)
    else:
        # FOR AWS
        application.run(debug=True,
                        # host='0.0.0.0',
                        port=8080)

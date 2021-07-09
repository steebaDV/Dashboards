import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc
import pandas as pd
import calendar
from clickhouse_driver import Client
from dash.dependencies import Input, Output
from datetime import datetime
import json
import warnings

warnings.filterwarnings(action='ignore')  # 'once'
# BOOTSTRAP THEME
from dash_bootstrap_components.themes import LITERA
from funcs import font_family, set_favicon  # directory.file

# TESTING
test = True

# ------------------------------------------------------------------
# ----------Loading theme, connection and data information----------
# ------------------------------------------------------------------
# LOAD JSON
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
# indexes = list(range(len(tab_names)))

# SET tab_ids HERE
visible_tabs = [dbc.Tab(label=name, tab_id=name.lower()) for name in tab_names]  # dbc.Tab(label="Main", tab_id="main"),
# dbc.Tab(label="Sales", tab_id="tab-1")]


# DF TO ANALYSE
# if not test:
#     client = Client(host=db_host,
#                     user=user,
#                     password=password,
#                     port=port,
#                     database=database)
# else:
#     # Test Code
#     client = Client(host='54.227.137.142',
#                     user='default',
#                     password='',
#                     port='9000',
#                     database='superstore')
#     print('TESTING!')

# # SET COLUMNS NAMES
# df = pd.DataFrame(client.execute(f'select * from {tablename}'))

# try:
#     column_names_ch = client.execute(f'SHOW CREATE {tablename}')
#     string = column_names_ch[0][0]
#     lst = string.split('`')
#     column_names_duplicated = lst[1::2]
#     # MAINTAIN THE ORDER
#     column_names = list(dict.fromkeys(column_names_duplicated))
#     df.columns = column_names
#     #print(df.columns)
#     #print(df['Business Line'].unique())
# except Exception as e:
#     print('THE FOLLOWING EXCEPTION WAS RAISED DURING THE LUNCH:')
#     print(e)

# print(f'DF LEN: {len(df)}')

# SORT BY DATES
# df.sort_values(by='DateTime', ascending=True, inplace=True)
app = dash.Dash(__name__, external_stylesheets=[LITERA], title=title)  # set CSS and Bootstrap Theme

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

now = datetime.now()
date = now.strftime("%Y-%m-%d")

# DropDown menu values
if test:
    df = pd.read_csv('test_df.csv').drop(columns=['Unnamed: 0'])
    df.iloc[:1250, -1] = [0] * 1250  # fill several rows with zeros to test 'Work Interruption (days)'
    df['Victim Birth Date'] = df['Victim Birth Date'].astype('datetime64[M]')
    df['Accident Occurrence Date'] = df['Accident Occurrence Date'].astype('datetime64[M]')
    print(df.columns)
    # print(df.dtypes)
avbl_years = sorted(list(set([dat.year for dat in df['Accident Occurrence Date']])))
avbl_months = [calendar.month_name[month_int] for month_int in
               set([dat.month for dat in df['Accident Occurrence Date']])]
# avbl_countries = sorted(df['Country'].unique().tolist())
# avbl_products = sorted(df['Business Line'].unique().tolist())
# avbl_customers = sorted(df['Customer'].unique().tolist())

# ------------------------------------------------------------------
# ------------------------DASHBOARD LAYOUT--------------------------
# ------------------------------------------------------------------

# Logo & Header
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
                   'margin-bottom': '0.2rem',
                   'color': headings_color,
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

# ------------------------ FILTERS --------------------------

# TIME FILTERS
month = dbc.FormGroup(
    [
        dbc.Label("Current Month", html_for="dropdown"),
        dcc.Dropdown(
            id="month_dropdown",
            placeholder='Select month',  # instead of Select...
            value=12,
            # value=None,/
            # value='month', # default value
            # Example: month_names_enumerated = {name: num for num, name in enumerate(calendar.month_name) if num}
            options=[{'label': month, 'value': num} for num, month in enumerate(calendar.month_name) if
                     month in avbl_months],  # [{'label': 'July', 'value': 7}, ...]
        ),
    ],
    className='form-group col-md-6',
)

year = dbc.FormGroup(
    [
        dbc.Label("Current Year", html_for="year_dropdown"),
        dcc.Dropdown(
            id="year_dropdown",
            placeholder='(All)',  # 2020
            value=2020,  # 2010
            # value=None, # default value
            # value='year',
            options=[{'label': year, 'value': year} for year in avbl_years]
        ),
    ],
    className='form-group col-md-6',
)

year_and_month = dbc.FormGroup(
    [
        month, year
    ],
    className='form-row',
    style={'margin-bottom': '0.1rem'},
)

# Performance scope filter
scope = dbc.FormGroup(
    [
        dbc.Label("Performance Scope", html_for="dropdown"),
        dcc.Dropdown(
            id="scope_dropdown",
            placeholder='Select scope',
            value='Current Month vs Previous Month',
            # value=1,
            options=[
                # {"label": "Current Month vs Same Month, Previous Year", "value": 1},
                # {"label": "Current Month vs Previous Month", "value": 2},
                # {"label": "Year-to-Date: Current Year vs Previous Year", "value": 3},
                {"label": "Current Month vs Same Month, Previous Year",
                 "value": "Current Month vs Same Month, Previous Year"},
                {"label": "Current Month vs Previous Month", "value": "Current Month vs Previous Month"},
                {"label": "Year-to-Date: Current Year vs Previous Year",
                 "value": "Year-to-Date: Current Year vs Previous Year"},
            ],
            style={'font-size': 12, }
        ),
    ],
    id='performance-scope'
)

# Accident Occurance Date filter
date_dropdown = dbc.FormGroup(
    [
        dbc.Label("Accident Occurance Date", html_for="dropdown"),
        dcc.Dropdown(
            id="date_dropdown",
            placeholder='Select date',
            # value='Current Month vs Previous Month',
            value="Last 5 years",
            options=[
                {"label": "Last 5 years", "value": "Last 5 years"},
            ],
        ),
    ],
    id='accident-scope'
)

# Client-filter
client_type = dbc.FormGroup(
    [
        dbc.Label("Client Type", html_for="dropdown"),
        dcc.Dropdown(
            id='client_dropdown',
            # options=[
            #     {'label': '(All)', 'value': '(All)'},
            #     {'label': 'Private Sector', 'value': 'Private Sector'},
            #     {'label': 'Public Sector', 'value': 'Public Sector'},
            # ],
            options=[{'label': typ, 'value': typ} for typ in df['Client Type'].unique()],
            value=None,
            clearable=False,
            placeholder='(All)',
            multi=True,
        ),
    ],
)

# Accident-nature filter
accident_nature = dbc.FormGroup(
    [
        dbc.Label("Accident Nature", html_for="dropdown"),
        dcc.Dropdown(
            id='accident_nature_dropdown',
            value=None,
            options=[{'label': '(All)', 'value': None}] +
                    [{'label': accident_n, 'value': accident_n} for accident_n in df['Accident Nature'].unique()
                     ],
            clearable=False,
            placeholder='(All)',
            multi=True,
        ),
    ],
    style={'margin-bottom': '1.1rem'}  # '1.98rem'
)

# Accident-status filter
accident_status = dbc.FormGroup(
    [
        dbc.Label("Accident Status", html_for="dropdown"),
        dcc.Dropdown(
            id='accident_status_dropdown',
            value=None,
            options=[{'label': '(All)', 'value': None}] +
                    [{'label': accident_s, 'value': accident_s} for accident_s in df['Accident Status'].unique()
                     ],
            clearable=False,
            placeholder='(All)',
            multi=True,
        ),
    ],
    # style={'margin-bottom': '1.1rem'}  # '1.98rem'
)

# Appeal-status filter
appeal_status = dbc.FormGroup(
    [
        dbc.Label("Appeal Status", html_for="dropdown"),
        dcc.Dropdown(
            id='appeal_status_dropdown',
            value=None,
            options=[{'label': '(All)', 'value': None}] +
                    [{'label': appeal_s, 'value': appeal_s} for appeal_s in df['Appeal Status'].unique()
                     ],
            clearable=False,
            placeholder='(All)',
            multi=True,
        ),
    ],
    style={'margin-bottom': '1.1rem'}  # '1.98rem'
)

# Show, Top and By filters
kpis_lst = ['Nb of Accidents',
            'Nb of Work Accidents',
            'Work Accidents %',
            'Nb of Serious Accidents',
            'Serious Accidents %',
            'Nb of Accidents with Work Interruption',
            'Accidents with Work Interruption %',
            'Avg Work Interruption',
            'Total Work Interruption',
            'Nb of Victims',
            'Victim Age',
            'Nb of Deceases'
            ]

show_filter = dbc.FormGroup(
    [dbc.Label("Show:", html_for="show_dropdown", style={'margin-right': '1rem'}),
     dcc.Dropdown(
         id="show_dropdown",
         placeholder='Show',
         value='Nb of Accidents',
         options=[{'label': kpi, 'value': kpi} for kpi in kpis_lst],
         style={'width': '14rem',
                'text-align': 'left',
                },
     ),
     ],
    style={},
)

list_of_by = ['Accident Nature', 'Accident Circumstances', 'Work Accident Flag', 'Serious Accident Flag',
              'Accident Status', 'Client', 'Client Type', 'Victim Gender',
              'Victim Deceased Flag', 'Injury Location', 'Injury Nature',
              'Injury Status', 'Doctor', 'Appeal Status', 'Reject Reason'
              ]
list_of_by.sort()

by_filter = dbc.FormGroup(
    [dbc.Label("By:", html_for="by_dropdown", style={'margin-right': '1rem'}),
     dcc.Dropdown(
         id="by_dropdown",
         placeholder='By',
         value=df.columns[3],
         options=[{'label': val, 'value': val} for val in list_of_by],
         style={'width': '14rem',
                'text-align': 'left',
                'font-size': 14,
                },
     ),
     ],
    style={},
)

show_and_by_filters = dbc.Row(
    [
        dbc.Col(show_filter,
                width=3,
                className="form-inline justify-content-end",
                # style={'border': '1px solid yellow',
                # },
                ),
        dbc.Col(by_filter,
                width=3,
                className="form-inline justify-content-end",  #
                # style={'border': '1px solid green',
                # },
                ),
    ],
    justify="end",  # horizonlal alignment
    style={
        'font-size': '14px'
    }
)

# Injury-nature filter
injury_filter = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label("Injury nature:", html_for="injury_dropdown", style={'margin-right': '1rem'}),
                    dcc.Dropdown(
                        id="injury_dropdown",
                        placeholder='Choose',
                        value='',
                        options=[{'label': val, 'value': val} for val in df['Injury Nature'].unique()],
                        style={'width': '12rem',
                               'text-align': 'left',
                               'font-size': 14,
                               },
                    ),
                ],
            ),
            width=3,
            className="form-inline justify-content-end",
        ),
    ],
    justify="end",  # horizonlal alignment
    style={
        'font-size': '14px'
    }
)

# ------------------------ MARKUP --------------------------

main_card_height = '46rem'  # '46rem'

# Tabs
tabs = html.Div(
    [
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.Div(
                            [
                            ],
                            id='header_div',
                            style={
                                'height': '2.5rem',
                                'margin-top': '-0.7rem',  # min from the top
                                # 'border': '1px solid red',
                            },
                        ),
                        html.H6(
                            [
                            ],
                            id='header_scopes',
                            style={
                                'height': '2rem',
                                'margin-top': '-2rem',  # min from the top
                                # 'border': '1px solid red',
                            },
                        ),
                        html.P(id="card-content"),
                    ], id='background-image'
                ),
            ],
            style={
                'height': main_card_height,
                # 'border': '1px solid green',
            },
            id='main_card',

        ),
        html.H6(f"{company_name} | {title} | Copyright Sign | Date: {date} - Proprietary and Confidential",
                style={
                    'color': 'grey',
                    'font-size': 10,
                    # 'border': '1px solid green',
                    'font-weight': 400,
                    'margin-top': '2em',
                    'margin-left': '0em',
                    'text-transform': 'uppercase',  # ALL LETTERS
                    # 'opacity': 0.4,
                },
                ),
    ],
)

card_height_s = '20rem'  # '21rem'

# ----------------------------- 1 -------------------------------
# ------------------------ COCKPIT TAB --------------------------
# COCKPIT TAB - ROW 1
accidents_indicators = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("ACCIDENT OVERVIEW",
                        style={'font-size': 13,
                               'color': headings_color,
                               #        'text-align': 'left',
                               #      # 'border': '1px solid green',
                               #        'font-weight': 'bold',
                               'margin-bottom': '-3px',
                               #        'font-family': 'Lato-Regular',
                               },
                        ),
                # ------------- 1st row -------------
                dcc.Graph(id='Nb-of-accidents-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                              'width': '33%',
                              'float': 'left',
                          },

                          ),
                dcc.Graph(id='accidents-wwi-ppt-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                              'width': '33%',
                              'float': 'left',

                          },

                          ),
                dcc.Graph(id='average-wi-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                              'width': '33%',
                              'float': 'left',
                          },

                          ),
                # ------------- 2nd row -------------
                dcc.Graph(id='serious-accidents-ppt-indicator',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',
                              'width': '33%',
                              'float': 'left',
                          },
                          ),
                dcc.Graph(id='total-wi-indicator',
                          style={
                              # 'border': '1px solid black',
                              'height': '48%',
                              'width': '33%',
                              'float': 'right',

                          },
                          ),
                dcc.Graph(id='work-accidents-ppt-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                              'width': '33%',
                              'float': 'right',
                          },

                          ),

            ],
            # className='overflow-auto',
            # className='overflow-hidden',

            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,
            },
        ),
    ],
)

accidents_shares = dbc.Card(
    [
        dbc.CardBody(
            [

                html.H6("ACCIDENTS SHARES",
                        style={'font-size': 13,
                               'color': headings_color,
                               # 'margin-bottom':'-3px',
                               }
                        ),
                dcc.Graph(id='accidents-shares-bar-h-2',
                          style={
                              # 'border': '1px solid green',
                              'margin-top': '-3px',
                              'height': '93%',
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',
                'height': card_height_s,
            },
        ),
    ],
)

cockpit_row_1 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    accidents_indicators,

                ],
                width=8,
            ),
            dbc.Col(
                [
                    accidents_shares,
                ],
                width=4,
            ),
        ],
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)

# COCKPIT TAB  - ROW 2
map_s1 = dbc.Card(  # same in Country Analysis Tab
            [
                dbc.CardBody(
                    [
                        html.H6("ACCIDENTS PER STATUS",
                        style={'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-3px',
                               },
                        ),
                        dcc.Graph(id='bar-names-cockpit-aps',
                                  # responsive=True,
                                  style={
                                      # 'border': '1px solid green',
                                      'height': '90%',
                                      'float': 'left',
                                      'width': '18%',
                                  },
                                  ),
                        dcc.Graph(id='accidents-per-status-bar-h',
                                  # responsive=True,
                                  style={
                                      # 'border': '1px solid green',
                                      'height': '90%',
                                      'float': 'right',
                                      'width': '82%',
                                  },
                                  ),
                    ],
                    style={
                        'padding': '3px 5px 3px',  # top, right/left, bottom
                        'height': '10rem',
                        # 'border': '2px solid green',
                        # 'margin-bottom': '0.1rem',
                    },
                ),
            ],
        )

map_s2 = dbc.Card(  # same in Country Analysis Tab
            [
                dbc.CardBody(
                    [
                        html.H6("ACCIDENTS PER APPEAL STATUS",
                        style={'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-3px',
                               },
                        ),
                        dcc.Graph(id='bar-names-cockpit-apas',
                                  # responsive=True,
                                  style={
                                      # 'border': '1px solid green',
                                      'height': '90%',
                                      'float': 'left',
                                      'width': '18%',
                                  },
                                  ),
                        dcc.Graph(id='accidents-per-a-status-bar-h',
                                  # responsive=True,
                                  style={
                                      # 'border': '1px solid green',
                                      'height': '90%',
                                      'float': 'right',
                                      'width': '82%',
                                  },
                                  ),
                    ],
                    style={
                        'padding': '3px 5px 3px',  # top, right/left, bottom
                        'height': '10rem',
                        # 'border': '2px solid green',
                        # 'margin-bottom': '0.1rem',
                    },
                ),
            ],
        )

top_reject_reason = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOP REJECT REASON",
                        style={'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-3px',
                               },
                        ),
                dcc.Graph(id='top-reject-reason-bar-h-2',
                          style={
                              'height': '96%',
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',
                'height': card_height_s,
            },
        ),
    ],
)

cockpit_row_2 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    map_s1, map_s2
                ],
                width=8,
            ),
            dbc.Col(
                [
                    top_reject_reason,
                ],
                width=4,
            )
        ],
    ),
    # margin between the rows
    style={'margin-bottom': '20px',
           # 'margin-left': '5px',
           },
)

card_height_l = '41.4rem'  # '41.4rem'

# ----------------------------- 2 -------------------------------
# ----------------- INJURIES PER DOCTOR TAB ---------------------
injuries_per_doctor = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("INJURIES PER DOCTOR - Per injury nature, identify the typical Duration of Work Interruption \
                  by Doctor and compared to all other doctors",
                        id='injuries_per_doctor-title',
                        style={'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-2px',
                               },
                        ),
                dcc.Graph(id='injuries-per-doctor',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,  # parent height
                # 'border': '2px solid green',
            },
        ),
    ],
)

# ----------------------------- 3 -------------------------------
# ----------------- ACCIDENTS PER CLIENT TAB --------------------
accidents_per_client = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("ACCIDENTS PER CLIENT",
                        style={'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-2px',
                               },
                        ),
                dcc.Graph(id='accidents-per-client',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,  # parent height
                # 'border': '2px solid green',
            },
        ),
    ],
)

accidents_per_client_bar = dbc.Card(
    [
        dbc.CardBody(
            [
                dcc.Graph(id='accidents-per-client-bar',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,  # parent height
                # 'border': '2px solid green'
            },
        ),
    ],
)

accidents_per_client_tab = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    accidents_per_client,
                ],
                width=6,
            ),
            dbc.Col(
                [
                    accidents_per_client_bar,
                ],
                width=6,
            ),
        ],
    ),
    # margin between the rows
    style={'margin-bottom': '1px'},
)
# ----------------------------- 4 -------------------------------
# --------------- ACCIDENTS PER VICTIM AGE TAB ------------------
accidents_per_victim_age = html.Div(
    dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6("ACCIDENTS PER VICTIM AGE",
                            style={'font-size': 13,
                                   'color': headings_color,
                                   'margin-bottom': '-2px',
                                   },
                            ),
                    dcc.Graph(id='accidents_per_victim_age_main',
                              style={
                                  'height': '100%',  # chart height
                                  'width': '100%',
                                  'float': 'left',
                              },
                              ),
                    # dcc.Graph(id='accidents_per_victim_age_2',
                    #           style={
                    #               'height': '46%',  # chart height
                    #               'width': '33%',
                    #               'float': 'left',
                    #           },
                    #           ),
                    # dcc.Graph(id='accidents_per_victim_age_3',
                    #           style={
                    #               'height': '46%',  # chart height
                    #               'width': '33%',
                    #               'float': 'left',
                    #           },
                    #           ),
                    # dcc.Graph(id='accidents_per_victim_age_4',
                    #           style={
                    #               'height': '46%',  # chart height
                    #               'width': '33%',
                    #               'float': 'right',
                    #           },
                    #           ),
                    # dcc.Graph(id='accidents_per_victim_age_5',
                    #           style={
                    #               'height': '46%',  # chart height
                    #               'width': '33%',
                    #               'float': 'right',
                    #           },
                    #           ),
                    # dcc.Graph(id='accidents_per_victim_age_6',
                    #           style={
                    #               'height': '46%',  # chart height
                    #               'width': '33%',
                    #               'float': 'right',
                    #           },
                    #           ),
                ],
            ),
        ],
        # margin between the rows
        style={'margin-bottom': '1px',
               'height': card_height_l,
               },
    )
)
# ----------------------------- 5 -------------------------------
# ------------------- TOP KPIS TRENDS TAB -----------------------

kpi_nb_of_accidents = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Nb of Accidents",
                        style={'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-2px',
                               },
                        ),
                dcc.Graph(id='nb_of_accidents',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '98%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,  # parent height

            },
        ),
    ],
)

kpi_work_accidents = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Work Accidents %",
                        style={'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-2px',
                               },
                        ),
                dcc.Graph(id='kpi-work-accidents',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '98%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,  # parent height

            },
        ),
    ],
)

kpi_serious_accidents = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Serious Accidents %",
                        style={'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-2px',
                               },
                        ),
                dcc.Graph(id='kpi-serious-accidents',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '98%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,
            },
        ),
    ],
)

kpi_accidents_wwi = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Accidents with Work Interruption %",
                        style={'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-2px',
                               },
                        ),
                dcc.Graph(id='kpi-accidents-wwi',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '98%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,  # parent height

            },
        ),
    ],
)

top_kpis_trends_row = html.Div(
    dbc.Row(
        [
            html.Div(
                [
                    html.H6("MONTH-TO-DATE",
                            style={
                                'writing-mode': 'vertical-rl',
                                'transform': 'rotate(-180deg)',
                                'height': '40%',
                                'text-align': 'center',
                                'font-size': 13,
                                'color': headings_color,

                                # 'border': '1px solid yellow',
                            }
                            ),
                    html.H6("YEAR-TO-DATE",
                            style={
                                'writing-mode': 'vertical-rl',
                                'transform': 'rotate(-180deg)',
                                'height': '45%',  # vertical centering relatively charts
                                'text-align': 'center',
                                'font-size': 13,
                                'color': headings_color,
                                # 'border': '1px solid green',
                            }
                            ),
                ],
                style={'clear': 'both',
                       'margin-left': '-1.5rem',  # from the left
                       'margin-right': '0.3rem',
                       },
            ),  # div
            dbc.Col(
                [
                    kpi_nb_of_accidents,
                ],
                style={'margin-left': '-2rem',  # margin between headings and 1st card
                       # 'border': '1px solid green',
                       },
            ),
            dbc.Col(
                [
                    kpi_work_accidents,

                ],
                style={
                    # 'border': '1px solid green',
                },
            ),
            dbc.Col(
                [
                    kpi_serious_accidents,
                ],
                style={
                    # 'border': '1px solid green',
                },
            ),
            dbc.Col(
                [
                    kpi_accidents_wwi,
                ],
                style={
                    # 'border': '1px solid green',
                },
            ),

        ],
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)

# ----------------------------- 6 -------------------------------
# -------------------- TOP PERFORMERS TAB -----------------------
filters_dropdown = html.Div(
    [
        dbc.FormGroup(
            [
                dbc.Label("Top", html_for="top_dropdown",
                          style={
                              'font-family': font_family,
                              'font-size': 14, }
                          # style={'margin-right': '1rem'}
                          ),
                dcc.Dropdown(
                    id="top_dropdown",
                    placeholder='Accident Circumstances',
                    value='Accident Circumstances',  # default value
                    options=[{'label': dimension, 'value': dimension} for dimension in list_of_by],
                    style={'width': '10rem',
                           'text-align': 'left',
                           'font-family': font_family,
                           'font-size': 14,
                           },
                ),
            ],
            className='form-inline justify-content-between',  # start-end
        ),
        dbc.FormGroup(
            [
                dbc.Label("By", html_for="by_kpi", style={
                    'font-family': 'Lato-Regular',
                    'font-size': 14,
                }),
                dcc.Dropdown(
                    id="by_kpi",
                    placeholder='Choose KPI',
                    value='Nb of Accidents',  # default value
                    options=[{'label': kpi, 'value': kpi} for kpi in ['Nb of Accidents', 'Work Accidents %', 'Serious Accidents %', 'Accidents with Work Interruption %']],  #kpis_lst],
                    style={'width': '10rem',
                           'text-align': 'left',
                           'font-family': 'Lato-Regular',
                           'font-size': 14,
                           },
                ),
            ],
            className='form-inline justify-content-between',  # start-end
            style={'margin-bottom': '0px'
                   },

        ),
    ],  # Div
    style={
        # 'border': '1px solid green',
    }
)

nb_of_accidents_col = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6(" ",
                # ),
                dcc.Graph(id='nb-of-accidents-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                          },

                          ),
                dcc.Graph(id='nb-of-accidents-bar',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',

                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,
                # 'border': '2px solid green',
                # 'min-height': '50%',
            },
        ),
    ],
)

work_accidents_col = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6(" ",
                # ),
                dcc.Graph(id='work-accidents-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                          },

                          ),
                dcc.Graph(id='work-accidents-bar',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',

                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,
                # 'border': '2px solid green',
            },
        ),
    ],
)

serious_accidents_col = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6(" ",
                # ),
                dcc.Graph(id='serious-accidents-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                          },
                          ),
                dcc.Graph(id='serious-accidents-pct-bar',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',

                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,
                # 'border': '2px solid green',
                # 'min-height': '50%',
            },
        ),
    ],
)

accidents_wwi_col = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6(" ",
                # ),
                dcc.Graph(id='accidents-wwi-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                          },
                          ),
                dcc.Graph(id='accidents-wwi-bar',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,
                # 'border': '2px solid green',
                # 'min-height': '50%',
            },
        ),
    ],
)

top_performers_row_1 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    filters_dropdown,
                ],
                width=2,
                className='col align-self-end'  # move column content down
            ),
            dbc.Col(
                [
                    nb_of_accidents_col,
                ],
            ),
            dbc.Col(
                [
                    work_accidents_col,
                ],
            ),
            dbc.Col(
                [
                    serious_accidents_col,
                ],
            ),
            dbc.Col(
                [
                    accidents_wwi_col,
                ],
            ),
        ],
    ),
    style={'margin-bottom': '20px'},
)

top_performers_row_2 = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6("PERFORMANCE BY BRAND",
                # ),
                dcc.Graph(id='bar-names',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',
                              'float': 'left',
                              'width': '18%',
                          },
                          ),
                dcc.Graph(id='top-by-performers-bar-h',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',
                              'float': 'right',
                              'width': '82%',
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
            },
        ),
    ],
)

# ----------------------------- 7 -------------------------------
# -------------------- ADHOC ANALYSIS TAB -----------------------
total_work_trends = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6(
                    id='adhoc-trends-title',
                    style={'text-align': 'left',
                           'font-size': 13,
                           'color': headings_color,
                           'margin-bottom': '-2px',
                           },
                ),
                dcc.Graph(id='total-work-interruption-trends',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'text-align': 'left',
                              'height': '96%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
                # 'border': '2px solid green',
            },
        ),
    ],
)

total_work_by_ac = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6(id='adhoc-by-title',
                        style={'text-align': 'left',
                               'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-2px',
                               },
                        ),
                dcc.Graph(id='adhoc-distribution',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
                # 'border': '2px solid green'
            },
        ),
    ],
)

adhoc_analysis_row_1 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    total_work_trends,
                ],
                width=6,
            ),
            dbc.Col(
                [
                    total_work_by_ac,
                ],
                width=6,
            ),
        ],
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)

pareto_anaysis = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Pareto analysis",
                        style={'text-align': 'left',
                               'font-size': 13,
                               'color': headings_color,
                               'margin-bottom': '-2px',
                               },
                        ),
                dcc.Graph(id='pareto-analysis',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # 96% - default
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
            },
        ),
    ],
)

adhoc_analysis_row_2 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    pareto_anaysis,
                ],
                width=12  # full width
            ),
        ],
    ),
)

# -------------------- UPDATE LAYOUT -----------------------
app.layout = html.Div(
    [
        # List of tabs
        dbc.Container(
            [
                dbc.Tabs(
                    visible_tabs,
                    id="card-tabs",
                    card=True,
                    active_tab="home",
                    className='tabs-above',
                    style={'margin-top': '1px',
                           'font-size': 11,
                           'margin-right': '1px',
                           'margin-left': '1px',
                           'top': '20px',
                           'borderBottom': '1px solid #d6d6d6',
                           # place at the very bottom
                           # 'bottom': '2px',
                           # 'float': 'left', # next element to be placed on the left
                           },
                ),
            ],
            fluid=True,
        ),
        # Filters
        dbc.Container(
            [
                # children - array
                dbc.Row(
                    [
                        dbc.Col(  # header
                            [
                                dbc.CardBody(
                                    [
                                        logo_and_header

                                    ],
                                )
                            ],
                            width=6,
                        ),
                        dbc.Col(  # filters 1
                            [
                                # dbc.CardBody(
                                #     [
                                dbc.Row(  # Filters Row
                                    [
                                        dbc.Col(  # filters 1
                                            [
                                                dbc.CardBody(
                                                    [
                                                        # year_and_month, scope
                                                    ],
                                                    id='left_filters',
                                                ),
                                            ],
                                            width=6,
                                            style={
                                                'padding-right': 0,
                                                # 'border': '1px solid yellow',
                                            },
                                        ),
                                        dbc.Col(  # filters 2
                                            [
                                                dbc.CardBody(
                                                    [
                                                        client_type, accident_nature
                                                    ],
                                                    style={
                                                        'padding-left': 0,
                                                        # 'padding-right': 0,
                                                        # 'border': '2x solid red',
                                                    },
                                                ),

                                            ],
                                            width=3,
                                            style={
                                                'padding-left': 0,
                                                'padding-right': 0,
                                                # 'border': '1px solid yellow',
                                            },
                                        ),
                                        dbc.Col(  # filters 3
                                            [
                                                dbc.CardBody(
                                                    [
                                                        accident_status, appeal_status
                                                    ],
                                                    style={
                                                        'padding-left': 0,
                                                    },
                                                ),
                                            ],
                                            width=3,
                                            style={
                                                'padding-left': 0,
                                                'padding-right': 0,
                                            },
                                        ),
                                    ],
                                    # ),

                                    # year_and_month, scope
                                    # ],
                                    style={'font-size': '14px',
                                           'margin-bottom': 0,
                                           },
                                ),
                            ],
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

            ],
            fluid=True,
            id='filters_pane'
        ),

        # Content
        dbc.Container(
            [
                tabs,
            ],
            fluid=True,
        ),

    ],  # div bracket
    # id='web-page'
    # style={'font-family': font_family}  # main font - fonts.css
)


# CALLBACKS
# Multiple Outputs
# All Tab IDs:
# main
# cockpit


@app.callback(
    [Output("card-content", "children"),
     Output("title", "children"),
     Output("filters_pane", "style"),
     Output("main_card", "style"),
     Output("background-image", 'style')
     ],
    [Input("card-tabs", "active_tab")]
)
def update_tab_content(active_tab):
    # print(f'active_tab: {active_tab}')

    filters_pane_style = None
    main_card_style = {'height': main_card_height}  # default
    background = None

    if active_tab == 'cockpit':
        children = cockpit_row_1, cockpit_row_2
        return children, 'Cockpit', filters_pane_style, main_card_style, background

    elif active_tab == 'injuries per doctor':
        children = injuries_per_doctor
        return children, 'Injuries per Doctor', filters_pane_style, main_card_style, background

    elif active_tab == 'accidents per client':
        children = accidents_per_client_tab
        return children, 'Accidents per Client', filters_pane_style, main_card_style, background

    elif active_tab == 'accidents per victim age':
        children = accidents_per_victim_age
        return children, 'Accidents per Victim Age', filters_pane_style, main_card_style, background

    elif active_tab == 'top kpis trends':
        children = top_kpis_trends_row
        return children, 'Top KPIs Trends', filters_pane_style, main_card_style, background

    elif active_tab == 'top performers':
        children = top_performers_row_1, top_performers_row_2
        return children, 'Top Performers', filters_pane_style, main_card_style, background

    elif active_tab == 'adhoc analysis':
        children = adhoc_analysis_row_1, adhoc_analysis_row_2
        return children, 'Adhoc Analysis', filters_pane_style, main_card_style, background

    elif active_tab == 'home':  # keep it last
        children = html.Div(  # content
            [
                dbc.Col([
                    dbc.CardBody(
                        [
                            logo
                        ],
                        style={'margin-left': '-1rem',
                               'margin-top': '-2rem',
                               }
                    )
                ],
                    width=2,
                    style={'height': '26rem',
                           'float': 'left',
                           }
                ),
                dbc.Col([
                    html.H1(title, style={'color': headings_color, 'font-size': '32px'}),
                    html.Hr(className='raacom-hr'),
                    html.H6(company_name, style={'font-size': '16px'}),
                    html.H6('Key Metrics', style={'font-size': '14px',
                                                  'margin-top': '2rem',
                                                  'color': headings_color,
                                                  }),
                    *[html.Li(el, style={'font-size': '13px'}) for el in kpis_lst],
                ],
                    width=10,
                )
            ],
            style={'padding-top': '5%',
                   'text-align': 'left',
                   # 'border': '2px solid green',
                   },
        ),  # content
        filters_pane_style = {'display': 'none'}  # filters_pane
        main_card_style = {
            # 'border': '2px solid green',
            'margin-top': '20px',
            'height': '56.75rem',  # main tab

        }
        background = {
            'background-image': f'url({background_image})',
            'background-size': '100%'
        }
        return children, '', filters_pane_style, main_card_style, background


# UPDATE LEFT FILTERS OUTPUT
@app.callback(
    Output("left_filters", "children"),
    [Input("card-tabs", "active_tab")],
)
def update_left_filters(active_tab):
    if active_tab in ['cockpit', 'top performers']:
        year_and_month.style['visibility'] = 'visible'
        return (year_and_month, scope)

    elif active_tab in ['top kpis trends']:
        year_and_month.style['visibility'] = 'visible'
        return year_and_month

    elif active_tab in ['adhoc analysis', 'injuries per doctor', 'accidents per client', 'accidents per victim age']:
        year_and_month.style['visibility'] = 'hidden'
        return (year_and_month, date_dropdown)

    else:
        year_and_month.style['visibility'] = 'hidden'
        return year_and_month


@app.callback(
    Output("header_div", "children"),  # div
    [Input("card-tabs", "active_tab"),
     ]
)
def update_header_div(active_tab):
    if active_tab in ['injuries per doctor']:
        children = injury_filter

    elif active_tab in ['adhoc analysis']:  # show and by
        by_filter.style['visibility'] = 'visible'
        children = show_and_by_filters

    else:
        children = []

    return children


# UPDATE HEADINGS - REPORTING PERIOD/ RFM OR FILTERS
# !!! DEPENDS ON update_left_filters !!!
@app.callback(
    Output("header_scopes", "children"),  # div
    [Input("card-tabs", "active_tab"),
     Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     ]
)
def update_header_div(active_tab, month=None, year=None, scope=None):
    print(f'now active: {active_tab}')
    # print(dash.callback_context.triggered, '<-------')
    if active_tab in ['cockpit', 'top performers']:
        # Current Month VS Previous Month
        month_start = month
        year_start = year

        if scope == "Current Month vs Same Month, Previous Year":  # 1
            month_end = month
            year_end = year - 1
        elif scope == "Current Month vs Previous Month":  # 2
            month_end = month - 1
            year_end = year
        elif scope == "Year-to-Date: Current Year vs Previous Year":  # 3
            month_end = month
            year_end = year - 1
        else:
            month_end = month
            year_end = year - 1

        current_month_abbr = calendar.month_abbr[month_start]
        previous_month_abbr = calendar.month_abbr[month_end]

        # Convert to a string
        year_start = str(year_start)[-2:]
        # month_abbr = calendar.month_abbr[month]
        # Convert to a string
        year_end = str(year_end)[-2:]
        previous_year = str(month_end)[-2:]

        reporting_period = [html.H6(
            [f'{current_month_abbr}-{year_start} vs {previous_month_abbr}-{year_end}'],
            style={'font-size': 14,
                   # 'margin-top': '1rem',
                   # 'margin-bottom': '6px',
                   'text-align': 'left',
                   'color': headings_color,
                   'padding-top': '0.5rem',  # vertical alignment
                   },
        )
        ]
        children = reporting_period
        return children


# ------------------------ ADHOC ANALYSIS CALLBACKS -----------------------
from adhoc import trends_function, distribution_function, pareto_analysis


@app.callback(
    Output('total-work-interruption-trends', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('show_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_total_sales_trend(dates, kpi,
                             client_type=None,
                             accident_nature=None,
                             accident_status=None,
                             appeal_status=None
                             ):
    # print('total-sales-indicator Input:')
    return trends_function(df,
                           kpi=kpi,
                           dates=dates,
                           client_type=client_type,
                           accident_nature=accident_nature,
                           accident_status=accident_status,
                           appeal_status=appeal_status
                           )


@app.callback(
    Output('adhoc-distribution', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('show_dropdown', 'value'),
     Input('by_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_adhoc_distribution(dates, kpi, by,
                              client_type=None,
                              accident_nature=None,
                              accident_status=None,
                              appeal_status=None
                              ):
    # print('sales-per-customer-indicator Input:')
    return distribution_function(df,
                                 kpi=kpi,
                                 column_to_group_by=by,
                                 max_bars=None,
                                 dates=dates,
                                 client_type=client_type,
                                 accident_nature=accident_nature,
                                 accident_status=accident_status,
                                 appeal_status=appeal_status,
                                 )


@app.callback(
    Output('adhoc-trends-title', 'children'),
    [Input('show_dropdown', 'value')])
def update_adhoc_title_1(kpi):
    # print('sales-per-customer-indicator Input:')
    return kpi + ' Trends'


@app.callback(
    Output('adhoc-by-title', 'children'),
    [Input('show_dropdown', 'value'),
     Input('by_dropdown', 'value'),
     ])
def update_adhoc_title_2(kpi, by):
    # print('sales-per-customer-indicator Input:')
    return kpi + ' by ' + by


@app.callback(
    Output('pareto-analysis', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('show_dropdown', 'value'),
     Input('by_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_pareto_analysis(dates, kpi, by,
                           client_type=None,
                           accident_nature=None,
                           accident_status=None,
                           appeal_status=None
                           ):
    # print('sales-per-customer-indicator Input:')
    return pareto_analysis(df,
                           kpi=kpi,
                           column_to_group_by=by,
                           max_bars=None,
                           dates=dates,
                           client_type=client_type,
                           accident_nature=accident_nature,
                           accident_status=accident_status,
                           appeal_status=appeal_status,
                           )


# ------------------------ TOP PERFORMERS CALLBACKS -----------------------
from top_performers_tab import get_indicator_plot

@app.callback(
    Output('nb-of-accidents-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                              current_year=year,
                              current_month=month,
                              chart_type='Nb of Accidents',
                              performance_scope=scope,
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('work-accidents-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                              current_year=year,
                              current_month=month,
                              chart_type='Work Accidents %',
                              performance_scope=scope,
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('serious-accidents-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                              current_year=year,
                              current_month=month,
                              chart_type='Serious Accidents %',
                              performance_scope=scope,
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('accidents-wwi-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                               current_year=year,
                               current_month=month,
                               chart_type='Accidents with Work Interruption %',
                               performance_scope=scope,
                               client_type=client_type,
                               accident_nature=accident_nature,
                               accident_status=accident_status,
                               appeal_status=appeal_status)


from top_performers_tab import get_bar_chart_and_line

@app.callback(
    Output('nb-of-accidents-bar', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_bar_chart_and_line(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_bar_chart_and_line(df,
                                  current_year=year,
                                  current_month=month,
                                  chart_type='Nb of Accidents',
                                  performance_scope=scope,
                                  client_type=client_type,
                                  accident_nature=accident_nature,
                                  accident_status=accident_status,
                                  appeal_status=appeal_status)

@app.callback(
    Output('work-accidents-bar', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_bar_chart_and_line(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_bar_chart_and_line(df,
                                  current_year=year,
                                  current_month=month,
                                  chart_type='Work Accidents %',
                                  performance_scope=scope,
                                  client_type=client_type,
                                  accident_nature=accident_nature,
                                  accident_status=accident_status,
                                  appeal_status=appeal_status)

@app.callback(
    Output('serious-accidents-pct-bar', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_bar_chart_and_line(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_bar_chart_and_line(df,
                                  current_year=year,
                                  current_month=month,
                                  chart_type='Serious Accidents %',
                                  performance_scope=scope,
                                  client_type=client_type,
                                  accident_nature=accident_nature,
                                  accident_status=accident_status,
                                  appeal_status=appeal_status)

@app.callback(
    Output('accidents-wwi-bar', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_bar_chart_and_line(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_bar_chart_and_line(df,
                                  current_year=year,
                                  current_month=month,
                                  chart_type='Accidents with Work Interruption %',
                                  performance_scope=scope,
                                  client_type=client_type,
                                  accident_nature=accident_nature,
                                  accident_status=accident_status,
                                  appeal_status=appeal_status)


from top_performers_tab import get_horizontal_bar_chart

@app.callback(
    Output('bar-names', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('top_dropdown', 'value'),
     Input('by_kpi', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart(year, month, scope, top, by, client_type, accident_nature, accident_status,
                                appeal_status):
    return get_horizontal_bar_chart(df,
                                    current_year=year,
                                    current_month=month,
                                    chart='left',
                                    performance_scope=scope,
                                    top=top,
                                    by=by,
                                    client_type=client_type,
                                    accident_nature=accident_nature,
                                    accident_status=accident_status,
                                    appeal_status=appeal_status)

@app.callback(
    Output('top-by-performers-bar-h', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('top_dropdown', 'value'),
     Input('by_kpi', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart(year, month, scope, top, by, client_type, accident_nature, accident_status,
                                appeal_status):
    return get_horizontal_bar_chart(df,
                                    current_year=year,
                                    current_month=month,
                                    chart='right',
                                    performance_scope=scope,
                                    top=top,
                                    by=by,
                                    client_type=client_type,
                                    accident_nature=accident_nature,
                                    accident_status=accident_status,
                                    appeal_status=appeal_status)


# ------------------------ ACCIDENTS PER VICTIM AGE TAB ------------------
from accidents_per_victim_age import create_dual_axis_chart

@app.callback(
    Output('accidents_per_victim_age_main', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_dual_axis_chart(dates, client_type, accident_nature, accident_status, appeal_status):
    return create_dual_axis_chart(df,
                                  dates=dates,
                                  client_type=client_type,
                                  accident_nature=accident_nature,
                                  accident_status=accident_status,
                                  appeal_status=appeal_status)


#----------------------------- COCKPIT CALLBACKS --------------------------
@app.callback(
    Output('Nb-of-accidents-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                              current_year=year,
                              current_month=month,
                              chart_type='Nb of Accidents',
                              performance_scope=scope,
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('serious-accidents-ppt-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                              current_year=year,
                              current_month=month,
                              chart_type='Serious Accidents %',
                              performance_scope=scope,
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('accidents-wwi-ppt-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                              current_year=year,
                              current_month=month,
                              chart_type='Accidents with Work Interruption %',
                              performance_scope=scope,
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('work-accidents-ppt-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                              current_year=year,
                              current_month=month,
                              chart_type='Work Accidents %',
                              performance_scope=scope,
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('average-wi-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                              current_year=year,
                              current_month=month,
                              chart_type='Avg Work Interruption',
                              performance_scope=scope,
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('total-wi-indicator', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_indicator_plot(year, month, scope, client_type, accident_nature, accident_status, appeal_status):
    return get_indicator_plot(df,
                              current_year=year,
                              current_month=month,
                              chart_type='Total Work Interruption',
                              performance_scope=scope,
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

from cockpit import get_horizontal_bar_chart_2

@app.callback(
    Output('bar-names-cockpit-aps', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart_2(year, month, scope, client_type, accident_nature, accident_status,
                                appeal_status):
    return get_horizontal_bar_chart_2(df,
                                    current_year=year,
                                    current_month=month,
                                    chart='left',
                                    performance_scope=scope,
                                    top='Accident Status',
                                    client_type=client_type,
                                    accident_nature=accident_nature,
                                    accident_status=accident_status,
                                    appeal_status=appeal_status)

@app.callback(
    Output('accidents-per-status-bar-h', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart_2(year, month, scope, client_type, accident_nature, accident_status,
                                appeal_status):
    return get_horizontal_bar_chart_2(df,
                                    current_year=year,
                                    current_month=month,
                                    chart='right',
                                    performance_scope=scope,
                                    top='Accident Status',
                                    client_type=client_type,
                                    accident_nature=accident_nature,
                                    accident_status=accident_status,
                                    appeal_status=appeal_status)

@app.callback(
    Output('bar-names-cockpit-apas', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart_2(year, month, scope, client_type, accident_nature, accident_status,
                                appeal_status):
    return get_horizontal_bar_chart_2(df,
                                    current_year=year,
                                    current_month=month,
                                    chart='left',
                                    performance_scope=scope,
                                    top='Appeal Status',
                                    client_type=client_type,
                                    accident_nature=accident_nature,
                                    accident_status=accident_status,
                                    appeal_status=appeal_status)

@app.callback(
    Output('accidents-per-a-status-bar-h', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart_2(year, month, scope, client_type, accident_nature, accident_status,
                                appeal_status):
    return get_horizontal_bar_chart_2(df,
                                    current_year=year,
                                    current_month=month,
                                    chart='right',
                                    performance_scope=scope,
                                    top='Appeal Status',
                                    client_type=client_type,
                                    accident_nature=accident_nature,
                                    accident_status=accident_status,
                                    appeal_status=appeal_status)

from cockpit import get_bar_chart_uni

@app.callback(
    Output('top-reject-reason-bar-h-2', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_bar_chart_uni(year, month, scope, client_type, accident_nature, accident_status,
                                appeal_status):
    return get_bar_chart_uni(df,
                        current_year=year,
                        current_month=month,
                        performance_scope=scope,
                        chart='Reject Reason',
                        client_type=client_type,
                        accident_nature=accident_nature,
                        accident_status=accident_status,
                        appeal_status=appeal_status)


# ------------------------ TOP KPI TRENDS CALLBACKS -----------------------

from top_kpis_trends import get_top_kpi_trends

@app.callback(
    Output('nb_of_accidents', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart(year, month, client_type, accident_nature, accident_status, appeal_status):
    return get_top_kpi_trends(df=df, month_int=month, year=year, chart='Nb of Accidents',
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('kpi-work-accidents', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart(year, month, client_type, accident_nature, accident_status, appeal_status):
    return get_top_kpi_trends(df=df, month_int=month, year=year, chart='Work Accidents %',
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('kpi-serious-accidents', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart(year, month, client_type, accident_nature, accident_status, appeal_status):
    return get_top_kpi_trends(df=df, month_int=month, year=year, chart='Serious Accidents %',
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)

@app.callback(
    Output('kpi-accidents-wwi', 'figure'),
    [Input('year_dropdown', 'value'),
     Input('month_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def update_horizontal_bar_chart(year, month, client_type, accident_nature, accident_status, appeal_status):
    return get_top_kpi_trends(df=df, month_int=month, year=year, chart='Accidents with Work Interruption %',
                              client_type=client_type,
                              accident_nature=accident_nature,
                              accident_status=accident_status,
                              appeal_status=appeal_status)


# ------------------------ Accidents per Client CALLBACKS -----------------------

from accidents_per_client import get_accidents_per_client_bar, get_accidents_per_client


@app.callback(
    Output('accidents-per-client-bar', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def accidents_per_client_bar(
        dates,
        client_type=None,
        accident_nature=None,
        accident_status=None,
        appeal_status=None
):
    return get_accidents_per_client_bar(df,
                                        dates=dates,
                                        client_type=client_type,
                                        accident_nature=accident_nature,
                                        accident_status=accident_status,
                                        appeal_status=appeal_status
                                        )


@app.callback(
    Output('accidents-per-client', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('client_dropdown', 'value'),
     Input('accident_nature_dropdown', 'value'),
     Input('accident_status_dropdown', 'value'),
     Input('appeal_status_dropdown', 'value'),
     ])
def accidents_per_client(
        dates,
        client_type=None,
        accident_nature=None,
        accident_status=None,
        appeal_status=None
):
    return get_accidents_per_client(df,
                                    dates=dates,
                                    client_type=client_type,
                                    accident_nature=accident_nature,
                                    accident_status=accident_status,
                                    appeal_status=appeal_status
                                    )


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
                        )
        print('Its testing time!')

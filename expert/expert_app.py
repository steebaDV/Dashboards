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
# ADDITION for coloring
import seaborn as sns

diverging_palette = sns.color_palette('coolwarm', 10).as_hex()

# BOOTSTRAP THEME
from dash_bootstrap_components.themes import LITERA
from funcs import font_family, set_favicon  # directory.file

# TESTING
test = True

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

# SET COLUMNS NAMES
df = pd.DataFrame(client.execute(f'select * from {tablename}'))

try:
    column_names_ch = client.execute(f'SHOW CREATE {tablename}')
    string = column_names_ch[0][0]
    lst = string.split('`')
    column_names_duplicated = lst[1::2]
    # MAINTAIN THE ORDER
    column_names = list(dict.fromkeys(column_names_duplicated))
    df.columns = column_names
    print(df.columns)
    #print(df['Business Line'].unique())
except Exception as e:
    print('THE FOLLOWING EXCEPTION WAS RAISED DURING THE LUNCH:')
    print(e)

# --- ---
# df.drop_duplicates(subset=["Date", "State", "Product"], keep='first', inplace=True)
print(f'DF LEN: {len(df)}')

# SORT BY DATES
df.sort_values(by='DateTime', ascending=True, inplace=True)
app = dash.Dash(__name__, external_stylesheets=[LITERA], title=title)  # set CSS and Bootstrap Theme

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

now = datetime.now()
date = now.strftime("%Y-%m-%d")

# DropDown menu values
avbl_months = [calendar.month_name[month_int] for month_int in df['DateTime'].dt.month.unique().tolist()]
avbl_years = sorted(df['DateTime'].dt.year.unique().tolist())
avbl_countries = sorted(df['Country'].unique().tolist())
avbl_products = sorted(df['Business Line'].unique().tolist())
avbl_customers = sorted(df['Customer'].unique().tolist())
#filter_4_lst = [1]  # sorted(df['Brand'].unique().tolist())

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

# Filters
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
            value=2010,
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
    style={'margin-bottom': '0.1rem'}
)

scope = dbc.FormGroup(
    [
        dbc.Label("Performance Scope", html_for="scope_dropdown"),
        dcc.Dropdown(
            id="scope_dropdown",
            placeholder='Select scope',
            # value='Current Month vs Previous Month',
            value=1,
            options=[
                {"label": "Current Month vs Same Month, Previous Year", "value": 1},
                {"label": "Current Month vs Same Month, Previous Year", "value": 2},
                {"label": "Current Month: Actual vs Target", "value": 3},
                {"label": "Year-to-Date: Current Year vs Previous Year", "value": 4},
                {"label": "Year-to-Date: Actual vs Target", "value": 5},
            ],
        ),
    ],
    id='performance-scope'
)

date_dropdown = dbc.FormGroup(  # to be
    [
        dbc.Label("Order Date", html_for="date_dropdown"),
        dcc.Dropdown(
            id="date_dropdown",
            placeholder='Select Date',
            value='last 17 months',
            options=[
                {"label": "Last 17 months", "value": 'last 17 months'},
            ],
        ),
    ],
)

# filters 2
states = dbc.FormGroup(
    [
        dbc.Label("Country", html_for="country_dropdown", style={'font-family':font_family}),
        dcc.Dropdown(
            id="country_dropdown",
            placeholder='(All)',
            value=None,
            # value='customer',
            options=[{"label": country, "value": country} for country in avbl_countries],
        ),
    ],
)

product_dropdown = dbc.FormGroup(
    [
        dbc.Label("Product Group", html_for="product_dropdown"),
        dcc.Dropdown(
            id="product_dropdown",
            placeholder='(All)',  # Germany
            value=None,  # default value
            # value='country',
            options=[{"label": product, "value": product} for product in avbl_products]

        ),
    ],
    style={'margin-bottom': '1.1rem'}  # '1.98rem'
)

#filter_4 = dbc.FormGroup(
#    [
#        dbc.Label("Filter 4", html_for="filter_4_dropdown"),
#        dcc.Dropdown(
#            id="filter_4_dropdown",
#            placeholder='(All)',
#            value=None,  # default value
#            options=[{"label": 'None', "value": None} for i in filter_4_lst]
#        ),
#    ],
#    style={'margin-bottom': '1.1rem',  # '1.98rem'
#           }
#)

customer_dropdown = dbc.FormGroup(
    [
        dbc.Label("Customer", html_for="customer_dropdown"),
        dcc.Dropdown(
            id="customer_dropdown",
            placeholder='(All)',
            value=None,  # default value
            options=[{"label": customer, "value": customer} for customer in avbl_customers]

        ),
    ],
    style={'margin-bottom': '1.1rem',
           }  # '1.98rem'
)

main_card_height = '46rem'  # '46rem'

# Tabs
tabs = html.Div(
    [
        dbc.Card(
            [
                # dbc.CardBody(
                #     [
                #         #children
                #     ],
                #     id='page_content'
                # ),

                dbc.CardBody(
                    [
                        html.Div(
                            [
                                # html.H6(# [] children
                                # # style = # change style in reporting-period callback
                                # id='reporting-period',
                                # ),
                            ],
                            id='header_div',
                            style={
                                'height': '3rem',
                                'margin-top': '-0.5rem',  # min from the top
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
        dbc.Tabs(
            visible_tabs,
            id="card-tabs",
            card=True,
            active_tab="main",
            className='tabs-below',
            style={'margin-top': '1px',
                   'font-size': 11,
                   'margin-right': '1px',
                   'margin-left': '1px',
                   # place at the very bottom
                   'bottom': '20px',
                   # 'float': 'left', # next element to be placed on the left
                   },
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

# COCKPIT TAB - ROW 1
sales_indicators = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("What are our sales results?",
                        # style={'font-size': 13,
                        #        'color': headings_color,
                        #        'text-align': 'left',
                        #      # 'border': '1px solid green',
                        #        'font-weight': 'bold',
                        #        'margin-bottom': '-3px',
                        #        'font-family': 'Lato-Regular',
                        # },
                        ),
                dcc.Graph(id='total-sales-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                              'width': '48%',
                              'float': 'left',
                          },

                          ),
                dcc.Graph(id='sales-per-customer-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                              'width': '48%',
                              'float': 'right',

                          },

                          ),
                dcc.Graph(id='total-sold-quantity-indicator',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',
                              'width': '48%',
                              'float': 'left',
                          },
                          ),
                dcc.Graph(id='average-selling-price-indicator',
                          style={
                              # 'border': '1px solid black',
                              'height': '48%',
                              'width': '48%',
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

profitability = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("What is our porfitability?",
                        ),
                dcc.Graph(id='sales-margin-pct-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                          },

                          ),
                dcc.Graph(id='total-sales-margin-indicator',
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

top_products = dbc.Card(
    [
        dbc.CardBody(
            [

                html.H6("Which Product Groups generate the most sales?",
                        ),
                dcc.Graph(id='top-products-bar-h-2',
                          style={
                              # 'border': '1px solid green',
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

cockpit_row_1 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    sales_indicators,

                ],
                width=4,
            ),
            dbc.Col(
                [
                    profitability,
                ],
                width=2,
            ),
            dbc.Col(
                [
                    top_products,
                ],
                width=6,
            ),
        ],
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)

# COCKPIT TAB  - ROW 2
map_s = dbc.Card(  # same in Country Analysis Tab
    [
        dbc.CardBody(
            [
                html.H6("How much do we sell across countires?",
                        style={
                            'margin-bottom': '2px',
                        },
                        ),
                dcc.Graph(id='map-s',
                          style={
                              'height': '94%',  # chart height
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
            },
        ),
    ],
)

customers_indicators = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("How many customers do we have?",
                        ),
                dcc.Graph(id='active-customers-indicator',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',  # chart height
                          },

                          ),
                dcc.Graph(id='new-customers-indicator',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',

                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,
            },
        ),
    ],
)

top_customers_2 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Who are our Top Customers?",
                        ),
                dcc.Graph(id='top-customers-bar-h-2',
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
                    map_s,
                ],
                width=4,
            ),
            dbc.Col(
                [
                    customers_indicators,
                ],
                width=2,
            ),
            dbc.Col(
                [
                    top_customers_2,
                ],
                width=6,
            )
        ],
    ),
    # margin between the rows
    style={'margin-bottom': '20px',
           # 'margin-left': '5px',
           },
)

card_height_l = '41.4rem'  # '41.4rem'

# RFM ANALYSIS TAB
# 1 chart
rfm_analysis_row = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6(
                    "How is our customer base segmented? What are the recommended marketing actions to address each customer segment?",
                    style={
                        'margin-bottom': '0px',
                    },
                ),
                dcc.Graph(id='rfm-analysis',
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',
                          },

                          ),
            ],
            # className='card-medium',
            style={
                'padding': '3px 5px 10px',
                'height': card_height_l,
            },
        ),
    ],
)

# RFM CUSTOMER BASE TAB
rfm_customer_base_row = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6(
                    "Which customers constitute each of our RFM Segments? (one circle per cutomer, sized by Total Sales)",
                    style={
                        'margin-bottom': '0px',
                    },
                ),
                html.Div(id='rfm-customer-base',
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',
                          },

                          ),
            ],
            style={
                'padding': '3px 5px 10px',
                'height': card_height_l,
            },
        ),
    ],
)

# RFM SEGMENT
segment_card = dbc.Card(
    [
        dbc.CardBody(
            [
              dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H6("Segment",
                                    style={
                                           'padding': '4px 5px 3px',
                                           'margin-bottom':'2rem,'
                                    }
                            ),
                            html.H6("Description",
                                    style={
                                           'padding': '3px 5px 3px',
                                           'margin-top':'2.6rem',
                                    }
                            ),
                            html.H6("Advice",
                                    style={
                                           'padding': '3px 5px 3px',
                                           'margin-top':'4rem',
                                    }
                            ),
                        ],
                        width=3,
                        style={'padding': '4px 5px 3px',
                               'margin-left':'1.5rem',
                              }
                    ),
                    dbc.Col(
                        [
                            html.P(children='Potential Loyalist',
                                    id='Segment_RFM',
                                    style={
                                           'padding': '3px 5px 3px',
                                           'margin-left':'1.5rem',
                                           'margin-bottom':'2rem',
                                           'font-size':18,
                                           'font-family':font_family,
                                           'text-align':'left',
                                    }
                            ),
                            html.P(children=customer_segments_desc['Potential Loyalist'],
                                    id='Description_RFM',
                                    style={'font-size':14,
                                           'font-family':font_family,
                                           'text-align':'left',
                                    }
                                  ),
                            html.H6(children=customer_segments_rec['Potential Loyalist'],
                                    id='Advice_RFM',
                                    style={'font-size':14,
                                           'font-family':font_family,
                                           'text-align':'left',
                                           'margin-top':'3rem',
                                    }
                                  ),
                        ],
                        width=8,
                        style={'padding': '3px 5px 3px',
                              }
                    ),
                    
                ]
              ),

            ],
            style={
                'padding': '3px 5px 3px',
                'height': card_height_s,
            },
        ),
    ],
    style={'margin-bottom': '20px'},  # spacing
)

customers_rmf_s = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Customers by R.F.M. (one circle per Customer) ",
                          style={
                              'margin-bottom': '0.5rem',
                                },
                        ),
                #dbc.Col( 
                #  [
                    html.P("Recency", style={'text-align':'left',
                                             #'margin-left':'1rem',
                                             'background-color':'grey',
                                            }
                          ),
                    dcc.Graph(id='customers-rmf-s-r',
                              style={
                                  'height': '18%',
                                  #'margin-bottom':'0.5rem',
                              },
                              ),
                    html.P("Frequency", style={'text-align':'left',
                                             #'margin-left':'1rem',
                                             'background-color':'grey',
                                            }
                          ),
                    dcc.Graph(id='customers-rmf-s-f',
                              style={
                                  'height': '18%',
                              },
                              ),
                    html.P("Monetary", style={'text-align':'left',
                                             #'margin-left':'1rem',
                                             'background-color':'gray',
                                            }
                          ),
                    dcc.Graph(id='customers-rmf-s-m',
                              style={
                                  'height': '18%',
                              },
                              ),
                 # ]
                #),
            ],
            style={
                'padding': '3px 5px 3px',
                'height': card_height_s,
            },
        ),
    ],
)

customers_rmf_l = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("Which customers belong to this RFM segment?",
                        style={
                              'margin-bottom': '1rem',
                          },
                        ),
                dbc.Row([
                  html.P("CUSTOMER   |   RFM Profile", 
                          style={'text-align':'left',
                                'font-size':'10px',
                            },
                          ),
                  html.P("RECENCY", 
                          style={'font-size':'16px',
                                 'margin-left':'2.8rem',
                                 #'background-color':'grey',
                            },
                          ),
                  html.P("FREQUENCY", 
                          style={'font-size':'16px',
                                 'margin-left':'6.8rem',
                                 #'background-color':'grey',
                            },
                          ),
                  html.P("MONETARY", 
                          style={'font-size':'16px',
                                 'margin-left':'5.8rem',
                                 #'background-color':'grey',
                            },
                          ),
                  html.P("Sales over time", 
                          style={'font-size':'16px',
                                 'margin-left':'6rem',
                                 #'background-color':'grey',
                            },
                          ),
                  ], style={'margin-bottom': '0.5rem',
                            'margin-left':'0.3rem',
                  }
                  ),
                    dcc.Graph(id='customers-rmf-l',
                              style={
                                  #'margin-left':'1rem',
                                  #'padding': '3px 5px 3px',
                                  #'height': '20%',
                                  #'width':'50%',
                              },
                              ),

            ],
            style={
                'padding': '3px 5px 3px',
                'height': card_height_l,
            },
        ),
    ],
)

rfm_segment_row = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    segment_card, customers_rmf_s
                ],
                width=4,
            ),
            dbc.Col(
                [
                    customers_rmf_l,
                ],
                width=8,
            ),
        ]
    ),
    # style={'margin-bottom': '20px'},
)

# TOP PERFORMERS TAB (5)
filters_dropdown = html.Div(
    [
        dbc.FormGroup(
            [
                dbc.Label("Top", html_for="top_dropdown",
                          style={
                           'font-family': 'Lato-Regular',
                           'font-size':14,}
                          # style={'margin-right': '1rem'}
                          ),
                dcc.Dropdown(
                    id="top_dropdown",
                    placeholder='Country',
                    value='Country',  # default value
                    options=[
                        {"label": 'Country', "value": 'Country'},
                    ],
                    style={'width': '10rem',
                           'text-align': 'left',
                           'font-family': 'Lato-Regular',
                           'font-size':14,
                           },
                ),
            ],
            className='form-inline justify-content-between',  # start-end
        ),
        dbc.FormGroup(
            [
                dbc.Label("By", html_for="by_kpi", style={
                           'font-family': 'Lato-Regular',
                           'font-size':14,
                  }),
                dcc.Dropdown(
                    id="by_kpi",
                    placeholder='Country',
                    value='Total Sales',  # default value
                    options=[
                        {"label": 'Total Sales', "value": 'Total Sales'},

                    ],
                    style={'width': '10rem',
                           'text-align': 'left',
                           'font-family': 'Lato-Regular',
                           'font-size':14,
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

total_sales_col = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6(" ",
                # ),
                dcc.Graph(id='total-sales-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                          },

                          ),
                dcc.Graph(id='total-sales-bar',
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

active_customers_col = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6(" ",
                # ),
                dcc.Graph(id='active-customers-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                          },

                          ),
                dcc.Graph(id='active-customers-bar',
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

sales_margin_pct_col = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6(" ",
                # ),
                dcc.Graph(id='sales-margin-pct-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                          },
                          ),
                dcc.Graph(id='sales-margin-pct-bar',
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

total_sales_margin_col = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6(" ",
                # ),
                dcc.Graph(id='total-sales-margin-indicator',
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                          },
                          ),
                dcc.Graph(id='total-sales-margin-bar',
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
                    total_sales_col,
                ],
            ),
            dbc.Col(
                [
                    active_customers_col,
                ],
            ),
            dbc.Col(
                [
                    sales_margin_pct_col,
                ],
            ),
            dbc.Col(
                [
                    total_sales_margin_col,
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

# PRODUCT PERFORMANCE TAB
best_selling_products = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("What are our best selling Products?",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                dcc.Graph(id='best-selling-products-bar-h',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',
                          },

                          ),
            ],
            style={
                'padding': '3px 5px 10px',
                'height': card_height_l,
            },
        ),
    ],
)

product_base_bubbles = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6(
                    "What does our Product base look like? (one circle per Product: sized by Total Sales, colored by Total Sales vs Reference Period",
                    style={
                        'margin-bottom': '0px',
                    },
                ),
                dcc.Graph(id='product-base-bubble-chart',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',  # !!! KEY ARGUMENT FOR SCALING !!!
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 10px',
                'height': card_height_l,
            },
        ),
    ],
)

product_performance_row = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    best_selling_products,
                ],
                width=8,
            ),
            dbc.Col(
                [
                    product_base_bubbles,
                ],
                width=4,
            ),
        ]
    ),
)

# CUSTOMER INSIGHT TAB
customer_performance = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.CardBody(
                            [
                                html.H6("How many active customers do we have?",
                                        style={
                                            'margin-bottom': '-2px',
                                        }
                                        ),
                                dcc.Graph(id='active-customers-indicator',
                                          style={
                                              # 'border': '1px solid green',
                                              # 'padding': '0px 0px 0px',
                                              'height': '48%',
                                          },
                                          ),
                                dcc.Graph(id='new-customers-indicator',
                                          style={
                                              # 'border': '1px solid green',
                                              # 'padding': '0px 0px 0px',
                                              'height': '48%',
                                          },
                                          ),
                            ],
                            style={
                                'padding': '3px 5px 3px',
                                'height': card_height_s,
                            },
                        ),
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        dbc.CardBody(
                            [
                                # html.H6("CUSTOMER PERFORMANCE", className="card-title"),
                                dcc.Graph(id='active-and-new-customers',
                                          style={
                                              # 'border': '1px solid green',
                                              # 'padding': '0px 0px 0px',
                                              'height': '100%',  # !!! KEY ARGUMENT FOR SCALING !!!
                                          },

                                          ),
                            ],
                            # className='col-sm-2',
                            style={
                                'padding': '10px 10px 5px',
                                'height': card_height_s,
                            },
                        ),
                    ],
                    # width=8,
                ),
            ],
        ),
    ],
    style={

        'margin-bottom': '20px',
    },
)

top_customers_3 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("What are our Top Customers? What is our level of Profitability with them?",
                        ),
                dcc.Graph(id='top-customers-bar-h-3',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',
                'height': card_height_s,
            }
        ),
    ],

)

customer_base_bubbles = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6(
                    "What does our Customer base look like? (one circle per Customer: sized by Total Sales, colored by Total Sales vs Reference Period)",
                    style={
                        'margin-bottom': '0px',
                    },
                ),
                dcc.Graph(id='customer-base-bubble-chart',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',  # !!! KEY ARGUMENT FOR SCALING !!!
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 10px',
                'height': card_height_l,
            },
        ),
    ],

)

customer_insight_row = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    customer_performance, top_customers_3
                ],
                width=8,
            ),
            dbc.Col(
                [
                    customer_base_bubbles,
                ],
                width=4,
            ),
        ]
    ),
)

# CUSTOMER LTV TAB - different element heights
customer_ltv_table = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("What is our customer Lifetime Value? What is our Customer Churn Rate?",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                html.P(id='customer-ltv-table',
                       style={
                           # 'border': '1px solid green',
                           'height': '96%',
                       },

                       ),
            ],
            style={
                'padding': '3px 5px 10px',
                'height': '30rem',
            },
        ),
    ],
    style={'margin-bottom': '20px', }
)

customer_ltv_descr = dbc.Card(
    [
        dbc.CardBody(
            [

            ],
            # className='card-medium',
            style={
                'padding': '3px 5px 10px',
                'height': '10rem',
                'background-image': f'url(assets/images/Description.png)',
                # 'background-size': '100%',
                'background-repeat': 'no-repeat',
                'background-height': '100%'

                # 'top': '50%',
            },
        ),
    ],
)

customer_ltv_chart_1 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("What is our Customer Lifetime value? (by cohort)",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                dcc.Graph(id='customer-ltv-1',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 10px',
                'height': '18.6rem',
            },
        ),
    ],
    style={'margin-bottom': '20px'},
)

customer_ltv_chart_2 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("What is our Customer Lifetime value?",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                dcc.Graph(id='customer-ltv-2',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 10px',
                'height': '10rem',
            },
        ),
    ],
    style={'margin-bottom': '20px'},
)

customer_churn_rate = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("What is our Customer Churn Rate?",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                dcc.Graph(id='customer-ltv-3',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 10px',
                'height': '10rem',
            },
        ),
    ],
)

customer_ltv_row = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    customer_ltv_table,
                    customer_ltv_descr
                ],
                width=8,
            ),
            dbc.Col(
                [
                    customer_ltv_chart_1,  # set margin-bottom for spacing
                    customer_ltv_chart_2,
                    customer_churn_rate,
                ],
                width=4,
            ),
        ],
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)

# PVM - SALES BRIDGE TAB
p_v_m_waterfall_chart = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("What influences the variation of Total Sales: Price, Volume, Mix?",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                dcc.Graph(id='p-v-m-waterfall-main',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',
                          },

                          ),
            ],
            style={
                'padding': '3px 5px 10px',
                'height': card_height_l,
            },
        ),
    ],
)

p_v_m_waterfall_charts_grouped = dbc.Card(
  [
    dbc.CardBody(
      [
        # html.H6("By Country, what influences the variation of Total Sales: Price, Volume, Mix?",
        html.H6("What influences the variation of Total Sales: Price, Volume, Mix? By:",
            style={
                 'margin-bottom': '0px',
            },
        ),
        dcc.Dropdown(
          id="waterfall_group_dropdown",
          placeholder='Country',
          value='Country',
          options=[
            {'label': 'Country', 'value': 'Country'},
            {'label': 'Date', 'value': 'Date'},
            {'label': 'Customer', 'value': 'Customer'},
            {'label': 'Product Group', 'value': 'Product Group'},
          ],
          style={'width': '8rem',
               'text-align': 'left',
               'font-size': '14px',
               'margin-top': '1rem',
               'font-family':font_family,
          },
        ),

        # dcc.Graph(id='p-v-m-waterfall-1',
        dcc.Graph(id='p-v-m-waterfall-grouped',
              style={
                # 'border': '1px solid green',
                # 'padding': '0px 0px 0px',
                # 'height': '30%',
                'height': '88%',
                'overflowY': 'scroll',
              },
        ),
        # dcc.Graph(id='p-v-m-waterfall-2',
        #           style={
        #               # 'border': '1px solid green',
        #               # 'padding': '0px 0px 0px',
        #               'height': '30%',
        #           },

        # ),
        # dcc.Graph(id='p-v-m-waterfall-3',
        #           style={
        #               # 'border': '1px solid green',
        #               # 'padding': '0px 0px 0px',
        #               'height': '30%',
        #           },
        # ),
      ],
      style={
        'padding': '3px 5px 10px',
        'height': card_height_l,
      },
    ),
  ],
)

p_v_m_analysis_row = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    p_v_m_waterfall_chart,
                ],
                width=6,
            ),
            dbc.Col(
                [
                    p_v_m_waterfall_charts_grouped
                    ,
                ],
                width=6,
            ),
        ]
    ),
)

# ADHOC ANALYSIS TAB
total_sales_trends = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES TRENDS",
                        ),
                dcc.Graph(id='total-sales-trends',
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
                # 'border': '2px solid green',
            },
        ),
    ],
)

total_sales_by_brand = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES BY BRAND",
                        ),
                dcc.Graph(id='total-sales-by-brand',
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
                    total_sales_trends,
                ],
                width=6,
            ),
            dbc.Col(
                [
                    total_sales_by_brand,
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
                html.H6("PARETO ANALYSIS",
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

# COUNTRY ANALYSIS TAB
map_l = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES PER COUNTRY",
                        ),
                dcc.Graph(id='map-l',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',  # !!! KEY ARGUMENT FOR SCALING !!!
                          },
                          ),

            ],
            style={
                'padding': '3px 5px 3px',
                'height': card_height_l,
            },
        ),
    ],
)

analysis_by_country_chart = dbc.Card(
    [
        dbc.CardBody(
            [
                # html.H6("TOTAL SALES PER COUNTRY",
                # ),
                dcc.Graph(id='total-sales-per-country',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '60%',
                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',
                'height': card_height_l,
            }
        ),
    ],
)

country_analysis_row = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    map_l,
                ],
                width=7,
            ),
            dbc.Col(
                [
                    analysis_by_country_chart
                ],
                width=5,
            ),
        ]
    ),
    # style={'margin-bottom': '20px'},
)

# TOP KPIS TAB
kpi_total_sales = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES",
                        ),

                dcc.Graph(id='total_sales-MTD',  # 2 chart merged with subplots
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

            },
        ),
    ],
)

kpi_active_customers = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("ACTIVE CUSTOMERS #",
                        ),

                dcc.Graph(id='kpi-active-customers',
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

            },
        ),
    ],
)

kpi_sales_margin_pct = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("SALES MARGIN %",
                        ),

                dcc.Graph(id='kpi-sales-margin-pct',
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # chart height
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

kpi_total_sales_margin = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES MARGIN",
                        ),

                dcc.Graph(id='kpi-total-sales-margin',
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
                style={'clear': 'both',
                       'margin-left': '-1.5rem',  # from the left
                       },
            ),  # div
            dbc.Col(
                [
                    kpi_total_sales,
                ],
                style={'margin-left': '-2rem',  # margin between headings and 1st card
                       # 'border': '1px solid green',
                       },
            ),
            dbc.Col(
                [
                    kpi_active_customers,

                ],
                style={
                    # 'border': '1px solid green',
                },
            ),
            dbc.Col(
                [
                    kpi_sales_margin_pct,
                ],
                style={
                    # 'border': '1px solid green',
                },
            ),
            dbc.Col(
                [
                    kpi_total_sales_margin,
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

app.layout = html.Div(
    [
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
                                        logo_and_header,

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
                                                        states, product_dropdown
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
                                                        customer_dropdown#, filter_4
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
    style={'font-family': font_family}  # main font - fonts.css
)


# CALLBACKS
# Multiple Outputs
# All Tab IDs:
# main
# cockpit
# rfm analysis
# rfm customer base
# rfm segment
# top performers
# product performance
# customer insight
# customer ltv
# p/ v/ m analysis
# adhoc analysis
# country analysis
# top kpis trends


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
    elif active_tab == 'rfm analysis':
        children = rfm_analysis_row
        return children, 'RFM Analysis (Customer Segmentation): Segment Detail', filters_pane_style, main_card_style, background
    elif active_tab == 'rfm customer base':
        children = rfm_customer_base_row
        return children, 'RFM Analysis (Customer Segmentation): Customer Base', filters_pane_style, main_card_style, background
    elif active_tab == 'rfm segment':
        children = rfm_segment_row
        return children, 'RFM Analysis (Customer Segmentation)', filters_pane_style, main_card_style, background
    elif active_tab == 'top performers':
        children = top_performers_row_1, top_performers_row_2
        return children, 'Top Performers', filters_pane_style, main_card_style, background
    elif active_tab == 'product performance':
        children = product_performance_row
        return children, 'Product Performance', filters_pane_style, main_card_style, background
    elif active_tab == 'customer insight':
        children = customer_insight_row
        return children, 'Customer Insight', filters_pane_style, main_card_style, background
    elif active_tab == 'customer ltv':
        children = customer_ltv_row
        return children, 'Customer Lifetime Value & Churn Rate', filters_pane_style, main_card_style, background
    elif active_tab == 'p/ v/ m analysis':
        children = p_v_m_analysis_row
        return children, 'Price/Volume/Mix Analysis - Sales Bridge', filters_pane_style, main_card_style, background
    elif active_tab == 'adhoc analysis':
        children = adhoc_analysis_row_1, adhoc_analysis_row_2
        return children, 'Adhoc Analysis', filters_pane_style, main_card_style, background
    elif active_tab == 'country analysis':
        children = country_analysis_row
        return children, 'Country Analysis', filters_pane_style, main_card_style, background
    elif active_tab == 'top kpis trends':
        children = top_kpis_trends_row
        return children, 'Top KPIs Trends', filters_pane_style, main_card_style, background

    elif active_tab == 'main':  # keep it last
        children = html.Div(  # content
            [
                html.H1(title, style={'color': headings_color}),
                html.Hr(className='raacom-hr'),
                html.H6(company_name, style={'font-size': '14px'}),
            ],
            style={'padding-top': '18%',
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
    if active_tab in ['cockpit', 'top performers', 'product performance', 'customer insight', 'p/ v/ m analysis']:
        year_and_month.style['visibility'] = 'visible'
        return year_and_month, scope

    elif active_tab in ['top kpis trends']:
        year_and_month.style['visibility'] = 'visible'
        return year_and_month

    elif active_tab in ['adhoc analysis', 'country analysis']:
        year_and_month.style['visibility'] = 'hidden'
        return year_and_month, date_dropdown

    else:  # rfm analysis, rfm customer base, rfm segment, customer ltv
        year_and_month.style['visibility'] = 'hidden'
        return year_and_month


# RFM FILTER

rfm_segment_filter = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label("RFM Segment:", html_for="rfm_segment_dropdown", style={'margin-right': '0.5rem'}),
                    dcc.Dropdown(
                        id="rfm_segment_dropdown",
                        placeholder='Potential Loyalist',
                        value='Loyal',
                        options=[{'label': val, 'value': val} for val in customer_segments_desc],
                        style={'width': '12rem',
                               'text-align': 'left',
                               },
                    ),
                ],
            ),
            width=2,
            className="form-inline justify-content-end",
            # style={'border': '1px solid green',
            # },
        ),
    ],
    justify="start",  # horizonlal alignment
    style={
        'margin-left':'5.7rem',
        'font-size': '14px'
    }
)

# LTV FILTER
ltv_filter = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label("LTV on:", html_for="ltv_filter_dropdown", style={'margin-right': '1rem'}),
                    dcc.Dropdown(
                        id="ltv_filter_dropdown",
                        placeholder='Total Sales',
                        value='Total Sales',
                        options=[{'label': 'Total Sales', 'value': 'Total Sales'}],
                        style={'width': '10rem',
                               'text-align': 'left',
                               },
                    ),
                ],
            ),
            width=2,
            className="form-inline justify-content-end",
            # style={'border': '1px solid green',
            # },
        ),
    ],
    justify="end",  # horizonlal alignment
    style={
        'font-size': '14px'
    }
)

# SHOW AND BY FILTERS
kpis_lst = ['Total Sales',
            'Sales per Customer',
            'Average Inventory Amount',
            'Total On-hand Amount',
            'Average Selling Price',
            'Average On-hand Price']

show_filter = dbc.FormGroup(
    [dbc.Label("Show:", html_for="show_dropdown", style={'margin-right': '2rem'}),
     dcc.Dropdown(
         id="show_dropdown",
         placeholder='Show',
         value='Total Sales',
         options=[{'label': kpi, 'value': kpi} for kpi in kpis_lst],
         style={'width': '14rem',
                'text-align': 'left',
                },
     ),
     ],
    style={},
)

by_filter = dbc.FormGroup(
    [dbc.Label("By:", html_for="by_dropdown", style={'margin-right': '2rem'}),
     dcc.Dropdown(
         id="by_dropdown",
         placeholder='By',
         value='Country',
         options=[{'label': 'Country', 'value': 'Country'}],
         style={'width': '10rem',
                'text-align': 'left',
                'font-size':14,
                },
     ),
     ],
    style={},
)

show_and_by_filters = dbc.Row(
    [
        dbc.Col(show_filter,
                width=2,
                className="form-inline justify-content-end",
                # style={'border': '1px solid yellow',
                # },
                ),
        dbc.Col(by_filter,
                width=2,
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


# main
# cockpit
# rfm analysis
# rfm customer base
# rfm segment
# top performers
# product performance
# customer insight
# customer ltv
# p/ v/ m analysis
# adhoc analysis
# country analysis
# top kpis trends

# UPDATE HEADINGS - REPORTING PERIOD/ RFM OR FILTERS
# !!! DEPENDS ON update_left_filters !!!
@app.callback(
    Output("header_div", "children"),  # div
    [Input("card-tabs", "active_tab"),
     Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     ]
)
def update_header_div(active_tab, month=None, year=None):
    # print(f'now active: {active_tab}')
    if active_tab in ['cockpit', 'top performers', 'product performance', 'customer insight', 'p/ v/ m analysis']:
        # Current Month VS Previous Month
        current_month = month
        previous_month = current_month - 1
        previous_year = year - 1
        current_month_abbr = calendar.month_abbr[current_month]
        previous_month_abbr = calendar.month_abbr[previous_month]
        # Convert to a string
        year = str(year)[-2:]
        month_abbr = calendar.month_abbr[month]
        # Convert to a string
        year = str(year)[-2:]
        previous_year = str(previous_year)[-2:]

        reporting_period = [html.H6(
            [f'{current_month_abbr}-{year} vs {current_month_abbr}-{previous_year}'],
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

    elif active_tab in ['rfm analysis', 'rfm customer base']:
        rfm_descr = f'''
RFM stands for Recency, Frequency and Monetary value, each corresponding to some customer trait. These RFM metrics are important
indicators of a customer's behavior because frequency and monetary value affects a customer's lifetime value, and recency affects retention, a measure of engagement.
'''
        rfm_descr = [html.H6(
            [rfm_descr],
            style={'font-size': '12px',
                   'text-align': 'left',
                   'color': '#C0C0C0',
                   'padding-top': '0.5rem',  # vertical alignment
                   },
        )
        ]
        children = rfm_descr

    elif active_tab in ['rfm segment']:
        children = rfm_segment_filter

    elif active_tab in ['customer ltv']:
        children = ltv_filter

    elif active_tab in ['adhoc analysis']:  # show and by
        by_filter.style['visibility'] = 'visible'
        children = show_and_by_filters

    elif active_tab in ['country analysis']:  # by
        by_filter.style['visibility'] = 'hidden'
        children = show_and_by_filters

    else:
        children = []

    return children


# TAB 1 - COCKPIT
from funcs import blue_palette, orange_palette, grey_palette
# Indicators
from indicators import get_indicator_plot


@app.callback(
    Output('total-sales-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_total_sales_indicator(month, year, country, customer, product):
    # print('total-sales-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Total Sales', country, customer, product)


@app.callback(
    Output('sales-per-customer-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_sales_per_customer_indicator(month, year, country, customer, product=None):
    # print('sales-per-customer-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Sales per Customer', country, customer, product)


@app.callback(
    Output('total-sold-quantity-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_total_sold_quantity_indicator(month, year, country, customer, product):
    # print('total-sold-quantity-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Total Sold Quantity', country, customer, product)


@app.callback(
    Output('average-selling-price-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_average_selling_price_indicator(month, year, country, customer, product):
    # print('average-selling-price-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Average Selling Price', country, customer, product)


@app.callback(
    Output('sales-margin-pct-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_sales_margin_pct_indicator(month, year, country, customer, product):
    # print('sales-margin-pct-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Sales Margin %', country, customer, product)


@app.callback(
    Output('total-sales-margin-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_total_sales_margin_indicator(month, year, country, customer, product):
    # print('total-sales-margin-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Total Sales Margin', country, customer, product)


@app.callback(
    Output('active-customers-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_active_customers_indicator(month, year, country, customer, product):
    # print('active-customers-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Active Customers', country, customer, product)


@app.callback(
    Output('new-customers-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_new_customers_indicator(month, year, country, customer, product):
    # print('new-customers-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'New Customers', country, customer, product)


# Map
from map import get_map


@app.callback(
    Output('map-s', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_map_s(month, year, country, customer, product):
    # print('map-s Input:')
    return get_map(df, kpi='Total Sales',
                   month_int=month,
                   year=year,
                   country=country,
                   customer=customer,
                   product=product,
                   )


# Horizontal Bars
from horizontal_bar_charts import get_bar_charts_h


@app.callback(
    Output('top-products-bar-h-2', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     ])
def update_top_products_bar_h_2(month, year, country, customer, product, scope):
    # print('top-products-bar-h-2 Input:')
    return get_bar_charts_h(month_int=month, year=year, df=df,
                            column_to_group_by='Business Line',
                            max_bars=7,
                            bar_charts=['Total Sales', 'Sales Margin %'],
                            country=country, customer=customer,
                            product_group=product,
                            scope=scope
                            )


@app.callback(
    Output('top-customers-bar-h-2', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     Input('scope_dropdown', 'value'),
     ])
def update_top_customers_bar_h_2(month, year, country, customer, product, scope):
    # print('top-customers-bar-h-2 Input:')
    return get_bar_charts_h(month_int=month, year=year, df=df,
                            column_to_group_by='Customer',
                            max_bars=7,
                            bar_charts=['Total Sales', 'Sales Margin %'],
                            country=country, customer=customer,
                            product_group=product,
                            scope=scope
                            )


# TAB 2 - RFM ANALYSIS
from rfm_analysis import rate, get_bars_and_treemaps_rfm

@app.callback(
    Output('rfm-analysis', 'figure'),
    [Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_rfm_analysis(country, customer, product):
    return get_bars_and_treemaps_rfm(df=df,
                                    customer=customer,
                                    country=country,
                                    product_group=product)


# TAB 3 - RFM CUSTOMER BASE

# TAB 4 - RFM SEGMENT DETAIL


# TAB 5 - Top Performers
from top_performers_tab import get_bar_chart_and_line


@app.callback(
    Output('total-sales-bar', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_total_sales_bar(month, year, country, customer, product):
    # print('update_total_sales_bar Input:')
    return get_bar_chart_and_line(df=df,
                                  current_year=year,
                                  current_month=month,
                                  chart_type='Total Sales',
                                  customer=customer,
                                  country=country,
                                  product_group=product)


@app.callback(
    Output('active-customers-bar', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_active_customers_bar(month, year, country, customer, product):
    # print('active-customers-bar Input:')
    return get_bar_chart_and_line(df=df,
                                  current_year=year,
                                  current_month=month,
                                  chart_type='Active Customers #',
                                  customer=customer,
                                  country=country,
                                  product_group=product)


@app.callback(
    Output('sales-margin-pct-bar', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_sales_margin_pct_bar(month, year, country, customer, product):
    # print('sales-margin-pct-bar Input:')
    return get_bar_chart_and_line(df=df,
                                  current_year=year,
                                  current_month=month,
                                  chart_type='Sales Margin %',
                                  customer=customer,
                                  country=country,
                                  product_group=product)


@app.callback(
    Output('total-sales-margin-bar', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_total_sales_margin_bar(month, year, country, customer, product):
    # print('total-sales-margin-bar Input:')
    return get_bar_chart_and_line(df=df,
                                  current_year=year,
                                  current_month=month,
                                  chart_type='Total Sales Margin',
                                  customer=customer,
                                  country=country,
                                  product_group=product)


from horizontal_bar_charts import get_horizontal_bar_chart


@app.callback(
    Output('bar-names', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     Input('top_dropdown', 'value'),
     Input('by_kpi', 'value'),
     # Input('scope_dropdown', 'value'),
     ])
def update_bar_names(month, year, country, customer, product, top, by):
    # print('bar-names Input:')
    return get_horizontal_bar_chart(df=df,
                                    current_year=year,
                                    current_month=month,
                                    chart='left',  # names
                                    top=top,
                                    by=by,
                                    customer=customer,
                                    country=country,
                                    product_group=product)


@app.callback(
    Output('top-by-performers-bar-h', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     Input('top_dropdown', 'value'),
     Input('by_kpi', 'value'),
     # Input('scope_dropdown', 'value'),
     ])
def update_top_by_performers_bar_h(month, year, country, customer, product, top, by):
    # print('top-by-performers-bar-h Input:')
    return get_horizontal_bar_chart(df=df,
                                    current_year=year,
                                    current_month=month,
                                    chart='right',  # bars
                                    top=top,
                                    by=by,
                                    customer=customer,
                                    country=country,
                                    product_group=product)


# TAB 6 - PRODUCT PERFORMANCE TAB
@app.callback(
    Output('best-selling-products-bar-h', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_best_selling_products_bar_h(month, year, country, customer, product):
    # print('best-selling-products-bar-h Input:')
    return get_bar_charts_h(month_int=month, year=year, df=df,
                            column_to_group_by='Business Line',
                            max_bars=15,
                            bar_charts=['Total Sales', 'Sales Margin %', 'Total Sales Margin'],
                            column_widths=[0.5, 0.25, 0.25],
                            country=country,
                            customer=customer,
                            product_group=product
                            )


# Bubble Chart
from bubble_charts import get_bubble_chart


@app.callback(
    Output('product-base-bubble-chart', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     # Input('scope_dropdown', 'value'),
     ])
def update_product_base_bubble_chart(month, year, country, customer, product):
    # print('product-base-bubble-chart Input:')
    return get_bubble_chart(month_int=month,
                            year=year,
                            df=df,
                            column_to_group_by='Business Line',
                            country=country,
                            customer=customer,
                            product=product
                            )


# TAB 7 - CUSTOMER INSIGHT TAB
from active_and_new_customers import get_active_and_new_customers


@app.callback(
    Output('active-and-new-customers', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_active_and_new_customers(month, year, country, customer, product):
    print('active-and-new-customers Input:')
    return get_active_and_new_customers(month, year, df, range=3, country=country, customer=customer, product=product)


@app.callback(
    Output('top-customers-bar-h-3', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_top_customers_bar_h_3(month, year, country, customer, product):
    # print('top-customers-bar-h-3 Input:')
    return get_bar_charts_h(month_int=month, year=year, df=df,
                            column_to_group_by='Customer',
                            max_bars=7,
                            bar_charts=['Total Sales', 'Sales Margin %', 'Total Sales Margin'],
                            country=country,
                            customer=customer,
                            product_group=product
                            )


@app.callback(
    Output('customer-base-bubble-chart', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     # Input('scope_dropdown', 'value'),
     ])
def update_customer_base_bubble_chart(month, year, country, customer):
    # print('customer-base-bubble-chart Input:')
    return get_bubble_chart(month_int=month,
                            year=year,
                            df=df,
                            column_to_group_by='Customer',
                            country=country,
                            customer=customer)


# TAB 9 - PRICE VOLUME MIX ANALYSIS / SALES BRIDGE
from sales_bridge import get_sales_bridge


@app.callback(
    Output('p-v-m-waterfall-main', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_sales_bridge(month, year, country, customer, product):
    return get_sales_bridge(df=df,
                            current_year=year,
                            current_month=month,
                            dimension=None,
                            customer=customer,
                            country=country,
                            product_group=product)


@app.callback(
    Output('p-v-m-waterfall-grouped', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     Input('waterfall_group_dropdown', 'value'),
     ])
def update_sales_bridge_grouped(month, year, country, customer, product, waterfall_group):
    return get_sales_bridge(df=df,
                            current_year=year,
                            current_month=month,
                            dimension=waterfall_group,
                            customer=customer,
                            country=country,
                            product_group=product)


# TAB 11 - COUNTRY ANALYSIS
@app.callback(
    Output('map-l', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('show_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_map_l(month, year, kpi, country, customer, product):
    # print('map-l Input:')
    return get_map(df, kpi=kpi,
                   month_int=month,
                   year=year,
                   country=country,
                   customer=customer,
                   product=product)


# todo - fix this func
from horizontal_bar_charts import total_sales_per_country


@app.callback(
    Output('total-sales-per-country', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     # Input('split_by_dropdown', 'value'), #'Year x Quarter'
     Input('product_dropdown', 'value'),
     Input('show_dropdown', 'value'),  # Total Sales
     ])
def update_total_sales_per_country(dates, country, customer, product, show_kpi):
    # print('total-sales-per-country Input:')
    return total_sales_per_country(df,
                                   kpi=show_kpi,
                                   dates=dates,
                                   state=country,
                                   product=product,
                                   store=customer,
                                   )


from customer_ltv_charts import get_ltv_table, get_customer_ltv_1, get_customer_ltv_2, get_customer_ltv_3


@app.callback(
    Output('customer-ltv-table', 'children'),
    [
        Input('country_dropdown', 'value'),
        Input('customer_dropdown', 'value'),
        Input('product_dropdown', 'value'),
        Input('ltv_filter_dropdown', 'value'),

    ])
def customer_ltv_table(country, customer, product, ltv_on):
    return get_ltv_table(df,
                         country=country,
                         customer=customer,
                         product_group=product,
                         ltv_on=ltv_on
                         )


@app.callback(
    Output('customer-ltv-1', 'figure'),
    [
        Input('country_dropdown', 'value'),
        Input('customer_dropdown', 'value'),
        Input('product_dropdown', 'value'),
        Input('ltv_filter_dropdown', 'value'),
    ])
def customer_ltv_1(country, customer, product, ltv_on):
    return get_customer_ltv_1(df,
                              country=country,
                              customer=customer,
                              product_group=product,
                              ltv_on=ltv_on
                              )


@app.callback(
    Output('customer-ltv-2', 'figure'),
    [
        Input('country_dropdown', 'value'),
        Input('customer_dropdown', 'value'),
        Input('product_dropdown', 'value'),
        Input('ltv_filter_dropdown', 'value'),
    ])
def customer_ltv_2(country, customer, product, ltv_on):
    return get_customer_ltv_2(df,
                              country=country,
                              customer=customer,
                              product_group=product,
                              ltv_on=ltv_on
                              )


@app.callback(
    Output('customer-ltv-3', 'figure'),
    [
        Input('country_dropdown', 'value'),
        Input('customer_dropdown', 'value'),
        Input('product_dropdown', 'value'),
        Input('ltv_filter_dropdown', 'value'),
    ])
def customer_ltv_3(country, customer, product, ltv_on):
    return get_customer_ltv_3(df,
                              country=country,
                              customer=customer,
                              product_group=product,
                              ltv_on=ltv_on
                              )

# Indicators
from adhoc import total_sales_trends, total_sales_distribution, pareto_analysis


@app.callback(
    Output('total-sales-trends', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('show_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_total_sales_trend(dates, kpi, country, customer, product):
    # print('total-sales-indicator Input:')
    return total_sales_trends(df,
                              kpi=kpi,
                              dates=dates,
                              country=country,
                              customer=customer,
                              Business_line=product)


@app.callback(
    Output('total-sales-by-brand', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('show_dropdown', 'value'),
     Input('by_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_total_sales_distribution(dates, kpi, by, country, customer, product):
    # print('sales-per-customer-indicator Input:')
    return total_sales_distribution(df,
                              dates=dates,
                              kpi=kpi,
                              column_to_group_by=by,
                              country=country,
                              customer=customer,
                              Business_line=product)

@app.callback(
    Output('pareto-analysis', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('show_dropdown', 'value'),
     Input('by_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_pareto_analysis(dates, kpi, by, country, customer, product):
    # print('total-sales-indicator Input:')
    return pareto_analysis(df,
                              kpi=kpi,
                              column_to_group_by=by,
                              dates=dates,
                              country=country,
                              customer=customer,
                              Business_line=product)

# TOP 4 KPIs TRENDS tab
from kpi import get_top_kpi_trends


@app.callback(
    Output('total_sales-MTD', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_kpi_trends_1(month, year,
                            country=None,
                            customer=None,
                            product=None
                            ):
    # print('total_sales-MTD Input:')
    return get_top_kpi_trends(month, year, df,
                              chart='Total Sales',
                              country=country,
                              customer=customer,
                              product=product
                              )


@app.callback(
    Output('kpi-active-customers', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_kpi_trends_2(month, year,
                            country=None,
                            customer=None,
                            product=None
                            ):
    # print('sales_per_store-MTD Input:')
    return get_top_kpi_trends(month, year, df,
                              chart='Active Customers #',
                              country=country,
                              customer=customer,
                              product=product
                              )


@app.callback(
    Output('kpi-sales-margin-pct', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_kpi_trends_3(month, year,
                            country=None,
                            customer=None,
                            product=None
                            ):
    # print('avg_inventory_amount-MTD Input:')
    return get_top_kpi_trends(month, year, df,
                              chart='Sales Margin %',
                              country=country,
                              customer=customer,
                              product=product
                              )


@app.callback(
    Output('kpi-total-sales-margin', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_kpi_trends_4(month, year,
                            country=None,
                            customer=None,
                            product=None
                            ):
    # print('total_on_hand_amount-MTD Input:')
    return get_top_kpi_trends(month, year, df,
                              chart='Total Sales Margin',
                              country=country,
                              customer=customer,
                              product=product
                              )


# RFM CUSTOMER SEGMENTATION
@app.callback(
    [Output('Segment_RFM', 'children'),
     Output('Description_RFM', 'children'),
     Output('Advice_RFM', 'children'),
    ],
    [Input('rfm_segment_dropdown', 'value'),
     ])
def update_rgm_desc(segment):
  return segment, customer_segments_desc[segment], customer_segments_rec[segment]

#Customer by RFM
from customer_segment import customer_by_rfm, bar_segment_rfm
@app.callback(
    Output('customers-rmf-s-r', 'figure'),
    [Input('rfm_segment_dropdown', 'value'),
      Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_customer_r(class_rfm=None,
                      country=None,
                      customer=None,
                      product=None
                      ):
    return customer_by_rfm(df,
                           class_rfm=class_rfm,
                           country=country,
                           customer=customer,
                           product=product,
                           metric='Recency',
                           )
@app.callback(
    Output('customers-rmf-s-f', 'figure'),
    [Input('rfm_segment_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_customer_f(class_rfm=None,
                      country=None,
                      customer=None,
                      product=None
                      ):
    return customer_by_rfm(df,
                           class_rfm=class_rfm,
                           country=country,
                           customer=customer,
                           product=product,
                           metric='Frequency',
                           )
@app.callback(
    Output('customers-rmf-s-m', 'figure'),
    [Input('rfm_segment_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_customer_m(class_rfm=None,
                      country=None,
                      customer=None,
                      product=None
                      ):
    return customer_by_rfm(df,
                           class_rfm=class_rfm,
                           country=country,
                           customer=customer,
                           product=product,
                           metric='Monetary',
                           )

@app.callback(
    Output('customers-rmf-l', 'figure'),
    [Input('rfm_segment_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customer_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_segment_rfm(class_rfm=None,
                      country=None,
                      customer=None,
                      product=None
                      ):
    return bar_segment_rfm(df,
                           class_rfm=class_rfm,
                           country=country,
                           customer=customer,
                           product=product,
                           )

from customer_base import get_customer_table


@app.callback(
    Output('rfm-customer-base', 'children'),
    [
        Input('country_dropdown', 'value'),
        Input('customer_dropdown', 'value'),
        Input('product_dropdown', 'value'),

        # Input('scope_dropdown', 'value'),
    ])
def rfm_customer_base(
        country=None,
        customer=None,
        product=None
):
    return get_customer_table(df,
                              country=country,
                              customer=customer,
                              product=product
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

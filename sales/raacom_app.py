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

test = True
warnings.filterwarnings(action='once')

# BOOTSTRAP THEME
from dash_bootstrap_components.themes import LITERA
from funcs import font_family, set_favicon

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

tabs_list = [dbc.Tab(label="Main", tab_id="main"),
             dbc.Tab(label="Sales", tab_id="tab-1"),
             dbc.Tab(label="Product Performance", tab_id="tab-2"),
             dbc.Tab(label="Customer Insight", tab_id="tab-3"),
             ]

visible_tabs = []
for tab in tabs_config:
    index = tabs_config.index(tab)
    if tab['status'] is True:
        visible_tab = tabs_list[index]
        visible_tabs.append(visible_tab)

if not test:
    # SERVER
    client = Client(host=db_host,
                    user=user,
                    password=password,
                    port=port,
                    database=database)
else:
    # --- TEST CODE ---
    client = Client(host='54.227.137.142',
                    user='default',
                    password='',
                    port='9000',
                    database='superstore')

df = pd.DataFrame(client.execute(f'select * from {tablename}'))  # sales_cockpit_matview_v2

# SET COLUMNS NAMES
try:
    column_names_ch = client.execute(f'SHOW CREATE {tablename}')
    string = column_names_ch[0][0]
    lst = string.split('`')
    column_names_duplicated = lst[1::2]
    # MAINTAIN THE ORDER
    column_names = list(dict.fromkeys(column_names_duplicated))
    df.columns = column_names
    print(df.columns)
except Exception as e:
    print('THE FOLLOWING EXCEPTION WAS RAISED DURING THE LUNCH:')
    print(e)

# print(df.columns)
print(f'DF len: {len(df)}')
# --- -- ---

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
avbl_customers = sorted(df['Customer'].unique().tolist())
avbl_prod_categories = sorted(df['Business Line'].unique().tolist())

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
# filters 1
month = dbc.FormGroup(
    [
        dbc.Label("Current Month", html_for="dropdown"),
        dcc.Dropdown(
            id="month_dropdown",
            placeholder='Select month',  # instead of Select...
            value=7,
            # Example: month_names_enumerated = {name: num for num, name in enumerate(calendar.month_name) if num}
            options=[{'label': month, 'value': num} for num, month in enumerate(calendar.month_name) if
                     month in avbl_months],  # [{'label': 'July', 'value': 7}, ...]
        ),
    ],
    className='form-group col-md-6',
)

year = dbc.FormGroup(
    [
        dbc.Label("Current Year", html_for="dropdown"),
        dcc.Dropdown(
            id="year_dropdown",
            placeholder='Select year',  # 2020
            value=2010,
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
        dbc.Label("Performance Scope", html_for="dropdown"),
        dcc.Dropdown(
            id="scope_dropdown",
            placeholder='Select scope',
            # value='Current Month vs Previous Month',
            value=1,
            options=[
                {"label": "Current Month vs Same Month, Previous Year", "value": 1},
            ],
        ),
    ],
)

# filters 2
customer = dbc.FormGroup(
    [
        dbc.Label("Customer", html_for="dropdown"),
        dcc.Dropdown(
            id="customers_dropdown",
            placeholder='(All)',
            value=None,
            # value='customer',
            options=[{"label": customer, "value": customer} for customer in avbl_customers],
        ),
    ],
)

country = dbc.FormGroup(
    [
        dbc.Label("Country", html_for="dropdown"),
        dcc.Dropdown(
            id="country_dropdown",
            placeholder='(All)',  # Germany
            value=None,  # default value
            # value='country',
            options=[{"label": country, "value": country} for country in avbl_countries]

        ),
    ],
    style={'margin-bottom': '1.1rem'}  # '1.98rem'
)

# Tabs
tabs = html.Div(
    [
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H6(  # [] children
                            style={'font-size': 14,
                                   # 'border': '1px solid red',
                                   # 'font-weight': 500,
                                   'margin-top': '-12px',
                                   'margin-bottom': '6px',
                                   'text-align': 'left',
                                   'color': headings_color,
                                   },
                            id='reporting-period'
                        ),
                        html.P(id="card-content"),
                        # style={'height': '50rem'}

                    ], id='background-image'
                ),
            ],
            style={
                'height': '46rem'
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

# TAB 1
card_height_s = '21rem'  # 19.6rem
sales_revenues_indicators_1 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("SALES REVENUES",
                        # style={'font-size': 13,
                        #        'color': headings_color,
                        #        'text-align': 'left',
                        #      # 'border': '1px solid green',
                        #        'font-weight': 'bold',
                        #        'margin-bottom': '-3px',
                        #        'font-family': 'Lato-Regular',
                        # },
                        ),
                # CHARTS (Total Sales, Sales per Customer)
                dcc.Graph(id='sales-per-customer-indicator',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',  # chart height
                              'width': '48%',
                              'float': 'right',
                          },

                          ),
                dcc.Graph(id='total-sales-indicator',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',  # chart height
                              'width': '48%',

                          },

                          ),
                dcc.Graph(id='average-selling-price-indicator',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',
                              'width': '48%',
                              'float': 'right',
                          },
                          ),
                dcc.Graph(id='total-sold-quantity-indicator',
                          style={
                              # 'border': '1px solid black',
                              'height': '48%',
                              'width': '48%',

                          },
                          ),

            ],
            # className='overflow-auto',
            # className='overflow-hidden',
            # display full width and height
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
                # 'height':'50%',
                # 'float': 'left',
            },
        ),
    ],
)

# sales_revenues_indicators_2
profitability = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("PROFITABILITY",
                        ),
                # CHARTS (Total Sales, Sales per Customer)
                dcc.Graph(id='sales-margin-pct-indicator',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',  # chart height
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
                'height': card_height_s,  # parent height
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
                # 'height':'50%',
                # 'max-height': '50%',
                # 'min-height': '50%',
            },
        ),
    ],
)

top_products_2 = dbc.Card(
    [
        dbc.CardBody(
            [

                html.H6("TOP PRODUCTS",
                        ),
                dcc.Graph(id='top-products-bar-h-2',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',  # !!! KEY ARGUMENT FOR SCALING !!!
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

row_1 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    sales_revenues_indicators_1,

                ],
                width=4,
            ),
            dbc.Col(
                [
                    # html.H6("2 INDICATORS", className="card-title"),
                    profitability,

                ],
                width=2,
            ),
            dbc.Col(
                [
                    # html.H6("TOP PRODUCTS", className="card-title"),
                    top_products_2,
                ],
                width=6,
            ),
        ],
        # style={'margin-bottom': '20px'},
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)

# row 2
map = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES PER COUNTRY",
                        style={
                            'margin-bottom': '2px',
                        },
                        ),
                dcc.Graph(id='map',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '94%',  # chart height
                          },
                          ),
            ],
            # display full width and height
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
                # 'height':'50%',
                # 'max-height': '50%',
                # 'min-height': '50%',
            },
        ),
    ],
)

customers_indicators = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("CUSTOMERS",
                        ),
                # CHARTS (Total Sales, Sales per Customer)
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
            # display full width and height
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
            },
        ),
    ],
)

top_customers_2 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOP CUSTOMERS",
                        ),
                dcc.Graph(id='top-customers-bar-h-2',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',  # !!! KEY ARGUMENT FOR SCALING !!!
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

row_2 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    # html.H6("MAP", className="card-title"),
                    map,
                ],
                width=4,
            ),
            dbc.Col(
                [
                    # html.H6("Customers", className="card-title"),
                    customers_indicators,
                ],
                width=2,
            ),
            dbc.Col(
                [
                    # html.H6("Top Customers", className="card-title"),
                    top_customers_2,
                ],
                width=6,
            )
        ],
        # style={'margin-bottom': '20px'},
    ),
    # margin between the rows
    style={'margin-bottom': '20px',
           # 'margin-left': '5px',

           },
)

# TAB 2
card_height_l = '43.4rem'  # 40.4rem
# row_3
top_products_3 = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOP PRODUCTS",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                dcc.Graph(id='top-products-bar-h-large',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',  # !!! KEY ARGUMENT FOR SCALING !!!
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

product_profile = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("PRODUCT PROFILE",
                        style={
                            'margin-bottom': '2px',
                        },
                        ),
                dcc.Graph(id='products-bubble-chart',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '98%',  # !!! KEY ARGUMENT FOR SCALING !!!
                          },
                          ),

            ],
            style={
                'padding': '3px 5px 10px',
                'height': card_height_l,
            }

        ),
    ],
)

row_3 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    top_products_3,
                ],
                width=8,
            ),
            dbc.Col(
                [
                    product_profile,
                ],
                width=4,
            ),
        ]
    ),
    # style={'margin-bottom': '20px'},
)

# TAB 3
# row 5
customer_performance = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.CardBody(
                            [
                                html.H6("CUSTOMER ACQUISITION",
                                        style={
                                            'margin-bottom': '-2px',
                                        }
                                        ),
                                dcc.Graph(id='active-customers-indicator',
                                          style={
                                              # 'border': '1px solid green',
                                              # 'padding': '0px 0px 0px',
                                              'height': '48%',  # !!! KEY ARGUMENT FOR SCALING !!!
                                          },

                                          ),
                                dcc.Graph(id='new-customers-indicator',
                                          style={
                                              # 'border': '1px solid green',
                                              # 'padding': '0px 0px 0px',
                                              'height': '48%',  # !!! KEY ARGUMENT FOR SCALING !!!
                                          },
                                          ),
                                # style = {'padding': '0px 0px 5px',
                                #
                                # },
                            ],
                            # className='col-sm-2',
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
                html.H6("TOP CUSTOMERS",
                        ),
                dcc.Graph(id='top-customers-bar-h-3',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',  # !!! KEY ARGUMENT FOR SCALING !!!
                          },
                          ),
            ],
            # className='card-small',
            style={
                'padding': '3px 5px 3px',
                'height': card_height_s,
            }
        ),
    ],
    # style={'width': '20rem'}
    # className='card-small'
)

sales_margin_total_sales = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("CUSTOMER PROFILE",
                        style={
                            'margin-bottom': '2px',
                        },
                        ),
                dcc.Graph(id='customers-bubble-chart',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '98%',  # !!! KEY ARGUMENT FOR SCALING !!!
                          },
                          ),

            ],
            style={
                'padding': '3px 5px 10px',
                'height': '43.5rem',
            }
        ),
    ],

)

customer_insight = html.Div(
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
                    sales_margin_total_sales,
                ],
                width=4,
            ),
        ]
    ),
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
                        dbc.Col(
                            [
                                dbc.CardBody(
                                    [
                                        logo_and_header,

                                    ],
                                )
                            ],
                            width=7,

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

                        dbc.Col(  # filters 2
                            [
                                dbc.CardBody(
                                    [
                                        country, customer
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
# Tabs
# Multiple Outputs
@app.callback(
    [Output("card-content", "children"),
     Output("title", "children"),
     Output("filters_pane", "style"),
     Output("main_card", "style"),
     Output("background-image", 'style')
     ],
    [Input("card-tabs", "active_tab")]
)
def tab_content(active_tab):
    # print(f'tab_content: {active_tab}')

    filters_pane_style = None
    main_card_style = {'height': '46rem'}  # default
    background = None
    if active_tab == 'tab-1':
        children = row_1, row_2
        # style = {'background-color': 'green'}
        return children, 'Sales', filters_pane_style, main_card_style, background
    elif active_tab == 'tab-2':
        children = row_3
        return children, 'Product Perfomance', filters_pane_style, main_card_style, background
    elif active_tab == 'tab-3':
        children = customer_insight
        return children, 'Customer Insight', filters_pane_style, main_card_style, background
    elif active_tab == 'main':  # main tab
        children = html.Div(  # content
            [
                html.H1(title, style={'color': headings_color}),
                html.Hr(className='raacom-hr'),
                html.H6(company_name),
            ],
            style={'padding-top': '18%',
                   'text-align': 'left'},
        ),  # content
        filters_pane_style = {'display': 'none'}  # filters_pane
        main_card_style = {
            # 'background-color': 'green',
            'margin-top': '20px',
            'height': '56.75rem',  #

        }
        background = {
            'background-image': f'url({background_image})',
            'background-size': '100%'
        }
        return children, '', filters_pane_style, main_card_style, background


@app.callback(
    [Output("reporting-period", "children"),
     ],
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input("card-tabs", "active_tab"),
     ]
)
def update_reporting_period(month, year, active_tab):  # heading
    previous_year = year - 1
    month_abbr = calendar.month_abbr[month]
    # Convert to a string
    year = str(year)[-2:]
    previous_year = str(previous_year)[-2:]

    if active_tab in ['tab-1', 'tab-2', 'tab-3']:
        children = [f'{month_abbr}-{year} vs {month_abbr}-{previous_year}']
    else:
        children = ['']

    # print(f'update_reporting_period: {children}, len: {len(children)}')
    return children


# TAB 1
from funcs import blue_palette, orange_palette
from bar_charts_h import get_bar_charts_h
# INDICATORS
from indicators import get_indicator_plot


@app.callback(
    Output('total-sales-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_total_sales_indicator(month, year, country, customer, filter=None):  # specify default values here
    # print('total-sales-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Total Sales', country, customer)


@app.callback(
    Output('total-sold-quantity-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_total_sold_quantity_indicator(month, year, country, customer, filter=None):
    # print('total-sold-quantity-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Total Sold Quantity', country, customer)


@app.callback(
    Output('sales-per-customer-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_sales_per_customer_indicator(month, year, country, customer):
    # print('total-sold-quantity-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Sales per Customer', country, customer)


@app.callback(
    Output('average-selling-price-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),
     # Input('scope_dropdown', 'value'),
     ])
def update_average_selling_price_indicator(month, year, country, customer
                                           # country=None, product_cat=None, customer=None, filter=None
                                           ):  # specify default values here
    # print('average-selling-price-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Average Selling Price', country, customer)


@app.callback(
    Output('sales-margin-pct-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),
     # Input('scope_dropdown', 'value'),
     ])
def update_sales_margin_pct_indicator(month, year, country, customer):
    # print('sales-margin-pct-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Sales Margin %', country, customer)


@app.callback(
    Output('total-sales-margin-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_total_sales_margin_indicator(month, year, country, customer):
    # print('total-sales-margin-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Total Sales Margin', country, customer)


@app.callback(
    Output('active-customers-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_active_customers_indicator(month, year, country, customer):
    # print('active-customers-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'Active Customers', country, customer)


@app.callback(
    Output('new-customers-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_new_customers_indicator(month, year, country, customer):
    # print('new-customers-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df, 'New Customers', country, customer)


# BARS
@app.callback(
    Output('top-products-bar-h-2', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_products_bar_h_2(month, year, country, customer):  # specify default values here
    print('top-products-bar-h-2 Input:')  #
    try:
        return get_bar_charts_h(month_int=month, year=year, df=df,
                                column_to_group_by='Business Line',
                                max_bars=7,
                                bar_charts=['Total Sales', 'Sales Margin %'],
                                country=country, customer=customer)
    except Exception as e:
        print('THE FOLLOWIING EXCEPTION WAS RAISED DURING UPDATING top-products-bar-h-2:')
        print(e)


@app.callback(
    Output('top-customers-bar-h-2', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_customers_bar_h_2(month, year, country, customer):  # specify default values here
    print('top-customers-bar-h-2 Input:')

    try:
        return get_bar_charts_h(month_int=month, year=year, df=df,
                                column_to_group_by='Customer',
                                max_bars=7,
                                bar_charts=['Total Sales', 'Sales Margin %'],
                                country=country, customer=customer)
    except Exception as e:
        print('THE FOLLOWIING EXCEPTION WAS RAISED DURING UPDATING top_customers_bar_h_2:')
        print(e)


# MAP
from map import get_map


@app.callback(
    Output('map', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_map(month, year, country, customer):
    print('map Input:')
    # print(month, year)
    # print(month, year, country, product_cat, customer, filter, '\n')
    try:
        return get_map(df, country, customer)
    except Exception as e:
        print('THE FOLLOWIING EXCEPTION WAS RAISED DURING UPDATING THE MAP:')
        print(e)


# TAB 2
@app.callback(
    Output('top-products-bar-h-large', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_products_bar_h_large(month, year, country, customer):
    # print('top-products-bar-h-large Input:')
    return get_bar_charts_h(month_int=month, year=year, df=df,
                            column_to_group_by='Business Line',
                            max_bars=15,
                            bar_charts=['Total Sales', 'Sales Margin %', 'Total Sales Margin'],
                            column_widths=[0.5, 0.25, 0.25],
                            country=country,
                            customer=customer,
                            )


from bubble_charts import get_bubble_chart
from funcs import bubbles_palette_1, bubbles_palette_2


@app.callback(
    Output('products-bubble-chart', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),
     # Input('scope_dropdown', 'value'),
     ])
def update_products_bubble_chart(month, year, country, customer):
    # print('products-bubble-chart Input:')
    return get_bubble_chart(month, year, df,
                            column_to_group_by='Business Line',
                            country=country,
                            customer=customer)


# TAB 3
@app.callback(
    Output('top-customers-bar-h-3', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),
     #
     # Input('filter_4_dropdown', 'value'),
     # Input('scope_dropdown', 'value'),
     ])
def update_top_customers_bar_h_3(month, year, country, customer):
    print('top-customers-bar-h-3 Input:')

    return get_bar_charts_h(month_int=month, year=year, df=df,
                            column_to_group_by='Customer',
                            max_bars=7,
                            bar_charts=['Total Sales', 'Sales Margin %', 'Total Sales Margin'],
                            country=country,
                            customer=customer)


@app.callback(
    Output('customers-bubble-chart', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_customers_bubble_chart(month, year, country, customer):
    print('customers-bubble-chart Input:')
    return get_bubble_chart(month, year, df,
                            column_to_group_by='Customer',
                            country=country,
                            customer=customer,
                            )


from active_and_new_customers import get_active_and_new_customers


@app.callback(
    Output('active-and-new-customers', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('country_dropdown', 'value'),
     Input('customers_dropdown', 'value'),
     # Input('scope_dropdown', 'value'),
     ])
def update_active_and_new_customers(month, year, country, customer):
    print('active-and-new-customers Input:')
    return get_active_and_new_customers(month, year, df, range=3, country=country, customer=customer)


# -----------------------------------------------------------------------------------------------------------------------
set_favicon(favicon)

if not test:
    server = app.server
else:
    application = app.server

if __name__ == '__main__':
    if not test:
        # FOR ALIBABA CLOUD
        app.run_server(debug=False)
    else:
        # FOR AWS
        application.run(debug=True,
                        # host='0.0.0.0',
                        port=8080)

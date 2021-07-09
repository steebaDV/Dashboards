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

warnings.filterwarnings(action='ignore')  # action='once'

test = True

# BOOTSTRAP THEME
from dash_bootstrap_components.themes import LITERA
from funcs import font_family, set_favicon  # directory.file

# LOAD JSON
with open('config.json', 'r') as f:
    config_file = json.load(f)

dbconfig = config_file['dbconfig'][0]  # dict
db_host, user, password, port, database = dbconfig.values()

tablename = config_file['tablename']
if test:
    tablename = tablename.split('.')[-1]
themeSettings = config_file['themeSettings'][0]
logo_img, color, title, description, favicon, background_image, company_name = themeSettings.values()
headings_color = '#007AB9'

# TABS VISIBILITY
tabs_config = config_file['tabs']  # dict
tab_names = [tab['tabname'] for tab in tabs_config if tab['status'] is True]  # tab names to be displayed
# indexes = list(range(len(tab_names)))
visible_tabs = [dbc.Tab(label=name, tab_id=name.lower()) for name in tab_names]  # dbc.Tab(label="Main", tab_id="main"),

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
except Exception as e:
    print('THE FOLLOWING EXCEPTION WAS RAISED DURING THE LUNCH:')
    print(e)

# --- ---
if test:
    df.rename(columns={'State': 'City'}, inplace=True)
df.drop_duplicates(subset=["Date", "City", "Product"], keep='first', inplace=True)
print(f'DF LEN: {len(df)}')


# SORT BY DATES
df.sort_values(by='Date', ascending=True, inplace=True)
app = dash.Dash(__name__, external_stylesheets=[LITERA], title=title)  # set CSS and Bootstrap Theme

app.scripts.config.serve_locally = True
app.css.config.serve_locally = True

now = datetime.now()
date = now.strftime("%Y-%m-%d")

# For cites with special encodings
import chardet

def decode_item(x):
  if type(x) != str:
    result_code = chardet.detect(x)
    original_text = x.decode(result_code['encoding'])
    return original_text
  else:
    return x
df['City'] = df['City'].apply(decode_item)


# DropDown menu values
avbl_months = [calendar.month_name[month_int] for month_int in df['Date'].dt.month.unique().tolist()]
avbl_years = sorted(df['Date'].dt.year.unique().tolist())
avbl_states = sorted(df['City'].unique().tolist())
avbl_stores = sorted(df['Store'].unique().tolist())
avbl_products = sorted(df['Product'].unique().tolist())
avbl_brands = sorted(df['Brand'].unique().tolist())


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
        dbc.Label("Current Year", html_for="dropdown"),
        dcc.Dropdown(
            id="year_dropdown",
            placeholder='Select year',  # 2020
            value=2020,
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
                {"label": "Current Month vs Previous Month", "value": 1},
            ],
        ),
    ],
    id='performance-scope'
)

date_dropdown = dbc.FormGroup(  # to be
    [
        dbc.Label("Date", html_for="date_dropdown"),
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
        dbc.Label("City", html_for="state_dropdown"),
        dcc.Dropdown(
            id="state_dropdown",
            placeholder='(All)',
            value=None,
            # value='customer',
            options=[{"label": state, "value": state} for state in avbl_states],
        ),
    ],
)

store_dropdown = dbc.FormGroup(
    [
        dbc.Label("Store", html_for="store_dropdown"),
        dcc.Dropdown(
            id="store_dropdown",
            placeholder='(All)',  # Germany
            value=None,  # default value
            # value='country',
            options=[{"label": store, "value": store} for store in avbl_stores]

        ),
    ],
    style={'margin-bottom': '1.1rem'},  # '1.98rem'
)

# filters 3
brand = dbc.FormGroup(
    [
        dbc.Label("Brand", html_for="brand_dropdown"),
        dcc.Dropdown(
            id="brand_dropdown",
            placeholder='(All)',
            value=None,  # default value
            options=[{"label": brand, "value": brand} for brand in avbl_brands]
        ),
    ],
    style={'margin-bottom': '1.1rem',  # '1.98rem'
           }
)

product = dbc.FormGroup(
    [
        dbc.Label("Product", html_for="product_dropdown"),
        dcc.Dropdown(
            id="product_dropdown",
            placeholder='(All)',
            value=None,  # default value
            options=[{"label": product, "value": product} for product in avbl_products]

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
                                html.H6(  # [] children
                                    # style = # change style in reporting-period callback
                                    id='reporting-period',
                                ),
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

# COCKPIT TAB
card_height_s = '20rem'  # '21rem'
# 2 charts
cockpit_sales_indicators = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("SALES",
                        ),
                dcc.Graph(id='total-sales-indicator',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',  # chart height
                          },

                          ),
                dcc.Graph(id='sales-per-store-indicator',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',

                          },
                          ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
                #'margin-top':'1rem',
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
            },
        ),
    ],
)

# 4 charts
cockpit_inventory_indicators = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("INVENTORY",
                        # style={'font-size': 13,
                        #        'color': headings_color,
                        #        'text-align': 'left',
                        #      # 'border': '1px solid green',
                        #        'font-weight': 'bold',
                        #        'margin-bottom': '0.3rem',
                        #        'font-family': 'Lato-Regular',
                        # },
                        ),
                dcc.Graph(id='average-inventory-amount',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                              'width': '48%',
                              'float': 'left'
                          },

                          ),
                dcc.Graph(id='inventory-turns',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                              'width': '48%',
                              'float': 'right',
                          },
                          ),
                dcc.Graph(id='total-on-hand-amount',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',
                              'width': '48%',
                              'float': 'left',
                          },
                          ),
                dcc.Graph(id='days-sales-of-indentory',
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
            # display full width and height
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
                #'font-size':6,
                # 'border': '2px solid green',
                # 'margin-bottom': '0.1rem',
            },
        ),
    ],
)

# 2 charts
cockpit_stores_indicators = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("STORES",
                        ),
                dcc.Graph(id='nb-of-stores',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',  # chart height
                          },

                          ),
                dcc.Graph(id='nb-of-new-stores',
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
            },
        ),
    ],
)

cockpit_products_indicators = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("PRODUCTS",
                        #style={'margin-bottom':'0.5rem'}
                        ),
                dcc.Graph(id='nb-of-products',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '48%',
                              'width': '48%',
                              'float': 'left',
                              #'margin-bottom':'0.5rem',
                          },

                          ),
                dcc.Graph(id='top-products-bar-h',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',
                              'width': '48%',
                              'float': 'right',
                          },
                          ),
                dcc.Graph(id='average-selling-price',
                          style={
                              # 'border': '1px solid red',
                              'height': '48%',
                              'width': '48%',
                              'float': 'left',
                          },
                          ),

            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_s,  # parent height
                # 'border': '1px solid green',
                # 'margin-bottom': '0.1rem',
            },
        ),
    ],
)

# COCKPIT TAB
cockpit_row_1 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    cockpit_sales_indicators,
                ],
                width=2,
            ),
            dbc.Col(
                [
                    cockpit_inventory_indicators,

                ],
                width=4,
            ),
            dbc.Col(
                [
                    cockpit_stores_indicators,
                ],
                width=2,
            ),
            dbc.Col(
                [
                    cockpit_products_indicators,
                ],
                width=4,
            ),

        ],
        # style={'margin-bottom': '20px'},
    ),
    # margin between the rows
    style={'margin-bottom': '20px'},
)

cockpit_performance_by_brand = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("PERFORMANCE BY BRAND", #style={'margin-bottom':'0.5rem'}
                        ),
                dcc.Graph(id='performance-by-brand',
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
                #'margin-bottom':'0.5rem',
                # 'border': '2px solid green',
                #                    # 'margin-bottom': '0.1rem',
            },
        ),
    ],
)

cockpit_row_2 = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    cockpit_performance_by_brand,
                ],
                width=12  # full width
            ),
        ],
        # style={'margin-bottom': '20px'},
    ),
)

# TOP BRANDS TAB
card_height_l = '41.4rem'  # '43.4rem'

# 1 chart
top_brands_row = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOP BRANDS BY TOTAL SALES",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                dcc.Graph(id='top-brands',
                          style={
                              # 'border': '1px solid green',
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

# TOP STORES TAB
top_stores_row = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOP STORES BY TOTAL SALES",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                dcc.Graph(id='top-stores',
                          style={
                              # 'border': '1px solid green',
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

# TOP O/S PRODUCTS TAB
top_os_products_row = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOP OUT-OF-STOCK PRODUCTS",
                        style={
                            'margin-bottom': '0px',
                        },
                        ),
                dcc.Graph(id='top-os-products',
                          style={
                              # 'border': '1px solid green',
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
                #                    # 'margin-bottom': '0.1rem',
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
                # 'border': '2px solid green',
                #                    # 'margin-bottom': '0.1rem',
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
        # style={'margin-bottom': '20px'},
    ),
)

# SEASONALITY ANALYSIS TAB
seasonality_analysis_row = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("none",  # keep spacing
                        style={
                            'margin-bottom': '0px',
                            'visibility': 'hidden',
                        },
                        ),
                dcc.Graph(id='seasonality-analysis',
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

# CITY ANALYSIS TAB
city_analysis_total_sales = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES",
                        ),
                dcc.Graph(id='total-sales-map',
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

city_analysis_total_sales_per_city = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES PER STATE",
                        ),
                dcc.Graph(id='total-sales-per-state',
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
    style={'margin-bottom': '20px',
           },
    # className='card-small'
)
city_analysis_total_sales_per_country = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES PER COUNTRY",
                        ),
                dcc.Graph(id='total-sales-per-country',
                          style={
                              # 'border': '1px solid green',
                              # 'padding': '0px 0px 0px',
                              'height': '96%',
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

city_analysis_row = html.Div(
    dbc.Row(
        [
            dbc.Col(
                [
                    city_analysis_total_sales
                ],
                width=7,
            ),
            dbc.Col(
                [
                    city_analysis_total_sales_per_city, city_analysis_total_sales_per_country
                ],
                width=5,
            ),
        ]
    ),
    style={'margin-bottom': '20px'},
)

# TOP KPIS TAB

kpi_total_sales = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL SALES",
                        ),

                dcc.Graph(id='total_sales-MTD',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # chart height
                          },

                          ),
                # dcc.Graph(id='total_sales-YTD',
                #           style={
                #                  # 'border': '1px solid red',
                #                  'height': '48%',
                #           },
                # ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,  # parent height

            },
        ),
    ],
)

kpi_sales_per_store = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("SALES PER STORE",
                        ),

                dcc.Graph(id='sales_per_store-MTD',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # chart height
                          },

                          ),
                # dcc.Graph(id='kpi_sales_per_store-YTD',
                #           style={
                #                  # 'border': '1px solid red',
                #                  'height': '48%',
                #           },
                # ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,  # parent height

            },
        ),
    ],
)

kpi_avg_inventory_amount = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("AVERAGE INVENTORY AMOUNT",
                        ),

                dcc.Graph(id='avg_inventory_amount-MTD',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # chart height
                          },


                          ),
                # dcc.Graph(id='kpi_avg_inventory_amount-YTD',
                #           style={
                #                  # 'border': '1px solid red',
                #                  'height': '48%',
                #           },
                # ),
            ],
            style={
                'padding': '3px 5px 3px',  # top, right/left, bottom
                'height': card_height_l,  # parent height

            },
        ),
    ],
)

kpi_total_on_hand_amount = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H6("TOTAL ON-HAND AMOUNT",
                        ),

                dcc.Graph(id='total_on_hand_amount-MTD',
                          # responsive=True,
                          style={
                              # 'border': '1px solid green',
                              'height': '96%',  # chart height
                          },

                          ),
                # dcc.Graph(id='kpi_total_on_hand_amount-YTD',
                #           style={
                #                  # 'border': '1px solid red',
                #                  'height': '48%',
                #           },
                # ),
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
                # width=3,
                style={'margin-left': '-2rem',  # margin between headings and 1st card
                       'margin-bottom':'1rem',
                       # 'border': '1px solid green',
                       },
            ),
            dbc.Col(
                [
                    kpi_sales_per_store,

                ],
                # width=3,
                style={
                        'margin-bottom':'1rem',
                    # 'border': '1px solid green',
                },
            ),
            dbc.Col(
                [
                    kpi_avg_inventory_amount,
                ],
                # width=3,
                style={
                      'margin-bottom':'1rem',
                    # 'border': '1px solid green',
                },
            ),
            dbc.Col(
                [
                    kpi_total_on_hand_amount,
                ],
                # width=3,
                style={
                      'margin-bottom':'1rem',
                    # 'border': '1px solid green',
                },
            ),

        ],
        # style={'margin-bottom': '20px'},
    ),
    # margin between the rows
    style={'margin-bottom': '30px'},
)

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
)

# customers-bubble-chart
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

kpis_lst = ['Total Sales',
            'Sales per Store',
            'Average Inventory Amount',
            'Total On-Hand Amount',
            'Average Selling Price',
            'Average On-hand Price']

filters_2 = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label("Show:", html_for="show_dropdown", style={'margin-right': '1rem'}),
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
            ),
            width=2,
            className="form-inline justify-content-end",
            style={'margin-right': '3rem'}
            # style={'border': '1px solid yellow',
            # },
        ),
        dbc.Col(
            dbc.FormGroup(
                # [
                #     dbc.Label("By:", html_for="by_dropdown", style={'margin-right': '2rem'}),
                #     dcc.Dropdown(
                #         id="by_dropdown",
                #         placeholder='By',
                #         value='Brand',
                #         options=[{'label': 'Brand', 'value': 'Brand'}],
                #         style={'width': '10rem',
                #                'text-align': 'left',
                #         },
                #     ),
                # ],
                id='by_and_split_by'
            ),
            width=2,
            className="form-inline justify-content-end",  #
            # style={'border': '1px solid green',
            # },
        ),
    ],
    justify="end",
    style={
        'font-size': '14px'
    }
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
                                                        states, store_dropdown
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
                                                        brand, product
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
# top brands
# top stores
# top o/s products
# adhoc analysis
# seasonality analysis
# city analysis
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
    # print(f'tab_content: {active_tab}')

    filters_pane_style = None
    main_card_style = {'height': main_card_height}  # default
    background = None
    if active_tab == 'cockpit':
        children = cockpit_row_1, cockpit_row_2
        return children, 'Cockpit', filters_pane_style, main_card_style, background
    elif active_tab == 'top brands':
        children = top_brands_row
        return children, 'Top Brands', filters_pane_style, main_card_style, background
    elif active_tab == 'top stores':
        children = top_stores_row
        return children, 'Top Stores', filters_pane_style, main_card_style, background
    elif active_tab == 'top o/s products':
        children = top_os_products_row
        return children, 'Top out-of-stock Products', filters_pane_style, main_card_style, background
    elif active_tab == 'adhoc analysis':
        children = adhoc_analysis_row_1, adhoc_analysis_row_2
        return children, 'Adhoc Analysis',filters_pane_style, main_card_style, background
    elif active_tab == 'seasonality analysis':
        children = seasonality_analysis_row
        return children, 'Seasonality Analysis', filters_pane_style, main_card_style, background
    elif active_tab == 'city analysis':
        children = city_analysis_row
        return children, 'City Analysis', filters_pane_style, main_card_style, background
    elif active_tab == 'top kpis trends':
        children = top_kpis_trends_row
        return children, 'Top 4 KPIs Trends', filters_pane_style, main_card_style, background


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
    if active_tab in ['cockpit', 'top brands', 'top stores']:
        year_and_month.style['visibility'] = 'visible'
        return year_and_month, scope

    elif active_tab in ['top o/s products', 'top kpis trends']:
        year_and_month.style['visibility'] = 'visible'
        return year_and_month

    elif active_tab in ['adhoc analysis', 'seasonality analysis', 'city analysis']:
        year_and_month.style['visibility'] = 'hidden'
        return year_and_month, date_dropdown


# UPDATE HEADINGS
@app.callback(
    [Output("reporting-period", "children"),  # div
     Output("reporting-period", "style"),
     ],
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input("card-tabs", "active_tab"),
     ]
)
def update_reporting_period(month, year, active_tab):
    # Current Month VS Previous Month
    current_month = month
    previous_month = current_month - 1
    current_month_abbr = calendar.month_abbr[current_month]
    previous_month_abbr = calendar.month_abbr[previous_month]
    # Convert to a string
    year = str(year)[-2:]
    style = {'font-size': 14,
             # 'margin-top': '1rem',
             # 'margin-bottom': '6px',
             'text-align': 'left',
             'color': headings_color,
             'padding-top': '0.5rem',  # vertical alignment
             }

    if active_tab in ['cockpit', 'top brands', 'top stores']:
        children = [f'{current_month_abbr}-{year} vs {previous_month_abbr}-{year}']
        style.update({'visibility': 'visible'})
    else:
        children = ['none']  # hidden
        style.update({'visibility': 'hidden'})

    return children, style


# UPDATE FILTERS 2
@app.callback(
    Output("header_div", "children"),  # div
    [Input("card-tabs", "active_tab")]
)
def update_header_div(active_tab):
    if active_tab in ['adhoc analysis', 'seasonality analysis', 'city analysis']:
        return filters_2
    else:
        return html.H6(  # [] children
            style={'font-size': 14,
                   # 'font-weight': 500,
                   'margin-top': '-12px',
                   'margin-bottom': '6px',
                   'text-align': 'left',
                   'color': headings_color,
                   # 'border': '1px solid red',
                   },
            id='reporting-period',
        ),


# UPDATE BY AND SPLIT BY FILTERS

by_filter = [dbc.Label("By:", html_for="by_dropdown", style={'margin-right': '1rem'}),
             dcc.Dropdown(
                 id="by_dropdown",
                 placeholder='By',
                 value='Brand',
                 options=[{'label': 'Brand', 'value': 'Brand'}],
                 style={'width': '10rem',
                        'text-align': 'left',
                        },
             ),
             ]

split_by_lst = ['Year x Quarter',
                'Year x Month',
                'Year x Week',
                'Year x Day of Year',
                'Month x Day of Month',
                'Month x Hour',
                'Week x Day of Week',
                'Week x Hour',
                'Day of Week x Hour', ]

split_by_filter = [dbc.Label("Split by:", html_for="split_by_dropdown", style={'margin-right': '0.7rem'}),
                   dcc.Dropdown(
                       id="split_by_dropdown",
                       placeholder='Split by',
                       value='Year x Quarter',
                       options=[{'label': value, 'value': value} for value in split_by_lst],
                       style={'width': '13rem',
                              'text-align': 'left',
                              },
                   ),
                   ]


@app.callback(
    Output("by_and_split_by", "children"),  # div
    [Input("card-tabs", "active_tab")]
)
def update_by_and_split_by(active_tab):
    if active_tab in ['seasonality analysis']:
        return split_by_filter
    else:
        return by_filter


from funcs import blue_palette, orange_palette
# TAB 1
# INDICATORS
from indicators import get_indicator_plot


@app.callback(
    Output('total-sales-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     # Input('country_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_total_sales_indicator(month, year,
                                 state=None,
                                 store=None,
                                 brand=None,
                                 product=None):  # specify default values here
    # print('total-sales-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Total Sales')


@app.callback(
    Output('sales-per-store-indicator', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_sales_per_store(month, year,
                           state=None,
                           store=None,
                           brand=None,
                           product=None
                           ):
    print('sales-per-store-indicator Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Sales per Store')


@app.callback(
    Output('average-inventory-amount', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_avg_inventory_amount(month, year,
                                 state=None,
                                 store=None,
                                 brand=None,
                                 product=None
                                 ):
    # print('average-inventory-amount Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Average Inventory Amount')


@app.callback(
    Output('total-on-hand-amount', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_total_on_hand_amount(month, year,
                                 state=None,
                                 store=None,
                                 brand=None,
                                 product=None
                                 ):
    # print('total-on-hand-amount Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Total On-Hand Amount')


@app.callback(
    Output('inventory-turns', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_inventory_turns(month, year,
                           state=None,
                           store=None,
                           brand=None,
                           product=None
                           ):
    #print('inventory-turns Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Inventory Turns')


@app.callback(
    Output('days-sales-of-indentory', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_days_sales_of_indentory(month, year,
                                   state=None,
                                   store=None,
                                   brand=None,
                                   product=None
                                   ):
    #print('days-sales-of-indentory Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Days Sales of Inventory')


@app.callback(
    Output('nb-of-stores', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_nb_of_stores(month, year,
                           state=None,
                           store=None,
                           brand=None,
                           product=None
                           ):
    # print('nb-of-stores Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Nb of Stores')


@app.callback(
    Output('nb-of-new-stores', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_nb_of_new_stores(month, year,
                           state=None,
                           store=None,
                           brand=None,
                           product=None
                           ):
    # print('nb-of-new-stores Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Nb of New Stores')


@app.callback(
    Output('nb-of-products', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_nb_of_products(month, year,
                           state=None,
                           store=None,
                           brand=None,
                           product=None
                           ):
    # print('nb-of-products Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Nb of Products')


@app.callback(
    Output('average-selling-price', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_avg_selling_price(month, year,
                             state=None,
                             store=None,
                             brand=None,
                             product=None
                             ):
    # print('average-selling-price Input:')
    return get_indicator_plot(year, calendar.month_abbr[month], df,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              chart_type='Average Selling Price')


# Top Products Bar
from top_products_bar_h import get_top_products_bar_h


@app.callback(
    Output('top-products-bar-h', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     Input('brand_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_products_bar_h(month, year,
                              state=None,
                              store=None,
                              product=None,
                              brand=None,
                              filter=None):
    # print('top-products-bar-h Input:')
    return get_top_products_bar_h(month, year, df, column_to_group_by='Product',
                                  state=state,
                                  store=store,
                                  product=product,
                                  brand=brand,
                                  )


# Performance By Brand - Large Bar Chart
from performace_by_brand_h import get_performace_by_brand_h


@app.callback(
    Output('performance-by-brand', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     #Input('filter_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_products_bar_h(month, year,
                              state=None,
                              store=None,
                              brand=None,
                              product=None
                              ):
    # print('top-products-bar-h Input:')
    return get_performace_by_brand_h(month, year, df, column_to_group_by='Brand',
                                     max_bars=10,
                                     state=state,
                                     store=store,
                                     brand=brand,
                                     product=product,
                                     bar_charts=['Total Sales', 'Sales per Store', 'Average Inventory Amount',
                                                 'Total On-Hand Amount', 'Inventory Turns', 'Days Sales of Inventory',
                                                 'Nb of Stores', 'Nb of New Stores', 'Nb of Products',
                                                 'Average Selling Price']
                                     )


# TAB 2
from bars_and_treemaps_h import get_bars_and_treemaps_h


@app.callback(
    Output('top-brands', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_brands(month, year,
                      state=None,
                      store=None,
                      brand=None,
                      product=None
                      ):
    # print('top-brands Input:')
    return get_bars_and_treemaps_h(month, year, df,
                                   state=state,
                                   store=store,
                                   brand=brand,
                                   product=product,
                                   column_to_group_by='Brand',
                                   bar_charts=['Total Sales', 'Total Sales by Product'],
                                   trees_column='Product',
                                   )


# TAB 3
@app.callback(
    Output('top-stores', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_stores(month, year,
                      state=None,
                      store=None,
                      brand=None,
                      product=None
                      ):
    # print('top-stores Input:')
    return get_bars_and_treemaps_h(month, year, df,
                                   state=state,
                                   store=store,
                                   brand=brand,
                                   product=product,
                                   column_to_group_by='Store',
                                   bar_charts=['Total Sales', 'Total Sales by Brand'],
                                   trees_column='Brand',
                                   )


# TAB 4 - TOP OS PRODUCTS
from top_os_products import get_top_os_products


@app.callback(
    Output('top-os-products', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_os_products(month, year,
                           state=None,
                           store=None,
                           brand=None,
                           product=None,
                           ):
    # print('top-os-products Input:')
    return get_top_os_products(month, year, df, column_to_group_by='Product',
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              )


# TAB 5
from total_sales_trends import total_sales_trends, total_sales_by_brand
from pareto_analysis import pareto_analysis


@app.callback(
    Output('total-sales-trends', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('show_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_total_sales_trends(dates,
                              show_kpi,
                              state=None,
                              store=None,
                              brand=None,
                              product=None
                              ):
    # print('total-sales-trends Input:')
    return total_sales_trends(df,
                              kpi=show_kpi,
                              dates=dates,
                              state=state,
                              store=store,
                              brand=brand,
                              product=product,
                              )


@app.callback(
    Output('total-sales-by-brand', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     Input('by_dropdown', 'value'),
     Input('show_dropdown', 'value'),
     ])
def update_total_sales_by_brand(dates, state, store, brand, product, by_dimension, show_kpi):
    # print('total-sales-by-brand Input:')
    return total_sales_by_brand(df,
                                column_to_group_by=by_dimension,
                                kpi=show_kpi,
                                max_bars=14,
                                dates=dates,
                                state=state,
                                store=store,
                                brand=brand,
                                product=product,
                                )


@app.callback(
    Output('pareto-analysis', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('by_dropdown', 'value'),  # Brand
     Input('show_dropdown', 'value'),  # Total Sales
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     ])
def update_pareto_analysis(dates,
                           by_dimension,
                           show_kpi,
                           state=None,
                           store=None,
                           brand=None,
                           product=None,
                           ):
    # print('total-sales-by-brand Input:')
    return pareto_analysis(df,
                           column_to_group_by=by_dimension,
                           kpi=show_kpi,
                           dates=dates,
                           state=state,
                           store=store,
                           brand=brand,
                           product=product
                           )


# TAB 6
# SPLIT BY
from seasonality_analysis import seasonality_analysis


@app.callback(
    Output('seasonality-analysis', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     Input('split_by_dropdown', 'value'),  # 'Year x Quarter'
     Input('show_dropdown', 'value'),  # Total Sales
     ])
def update_seasonality_analysis(dates, state, store, brand, product, split_by_dimension, show_kpi):
    # print('total-sales-by-brand Input:')
    return seasonality_analysis(df,
                                dimension=split_by_dimension,
                                kpi=show_kpi,
                                dates=dates,
                                state=state,
                                store=store,
                                brand=brand,
                                product=product,
                                )


# TAB 7 - CITY ANALYSIS
from city_analysis import get_state_map, total_sales_per_state, total_sales_per_country


@app.callback(
    Output('total-sales-map', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     # Input('split_by_dropdown', 'value'), #'Year x Quarter'
     Input('show_dropdown', 'value'),  # Total Sales
     ])
def update_state_map(dates, state, store, brand, product, show_kpi):
    # print('total-sales-map Input:')
    return get_state_map(df,
                         kpi=show_kpi,
                         dates=dates,
                         state=state,
                         store=store,
                         brand=brand,
                         product=product)


@app.callback(
    Output('total-sales-per-state', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     # Input('split_by_dropdown', 'value'), #'Year x Quarter'
     Input('show_dropdown', 'value'),  # Total Sales
     ])
def update_total_sales_per_state(dates, state, store, brand, product, show_kpi):
    # print('total-sales-per-state Input:')
    return total_sales_per_state(df,
                                 kpi=show_kpi,
                                 max_bars=10,
                                 dates=dates,
                                 state=state,
                                 store=store,
                                 brand=brand,
                                 product=product)


@app.callback(
    Output('total-sales-per-country', 'figure'),
    [Input('date_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),
     # Input('split_by_dropdown', 'value'), #'Year x Quarter'
     Input('show_dropdown', 'value'),  # Total Sales
     ])
def update_total_sales_per_country(dates, state, store, brand, product, show_kpi):
    # print('total-sales-per-country Input:')
    return total_sales_per_country(df,
                                   kpi=show_kpi,
                                   dates=dates,
                                   state=state,
                                   store=store,
                                   brand=brand,
                                   product=product)


# TAB 8 - TOP KPIS
from top_kpi_trends import get_top_kpi_trends


@app.callback(
    Output('total_sales-MTD', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_kpi_trends_1(month, year,
                            state=None,
                            store=None,
                            brand=None,
                            product=None
                            ):
    # print('total_sales-MTD Input:')
    return get_top_kpi_trends(month, year, df,
                              kpi='Total Sales',
                              store=store,
                              state=state,
                              brand=brand,
                              product=product
                              )


@app.callback(
    Output('sales_per_store-MTD', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_kpi_trends_2(month, year,
                            state=None,
                            store=None,
                            brand=None,
                            product=None
                            ):
    # print('sales_per_store-MTD Input:')
    return get_top_kpi_trends(month, year, df,
                              kpi='Sales per Store',
                              store=store,
                              state=state,
                              brand=brand,
                              product=product
                              )


@app.callback(
    Output('avg_inventory_amount-MTD', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_kpi_trends_3(month, year,
                            state=None,
                            store=None,
                            brand=None,
                            product=None
                            ):
    # print('avg_inventory_amount-MTD Input:')
    return get_top_kpi_trends(month, year, df,
                              kpi='Average Inventory Amount',
                              store=store,
                              state=state,
                              brand=brand,
                              product=product
                              )


@app.callback(
    Output('total_on_hand_amount-MTD', 'figure'),
    [Input('month_dropdown', 'value'),
     Input('year_dropdown', 'value'),
     Input('state_dropdown', 'value'),
     Input('store_dropdown', 'value'),
     Input('brand_dropdown', 'value'),
     Input('product_dropdown', 'value'),

     # Input('scope_dropdown', 'value'),
     ])
def update_top_kpi_trends_4(month, year,
                            state=None,
                            store=None,
                            brand=None,
                            product=None
                            ):
    # print('total_on_hand_amount-MTD Input:')
    return get_top_kpi_trends(month, year, df,
                              kpi='Total On-Hand Amount',
                              store=store,
                              state=state,
                              brand=brand,
                              product=product
                              )


# -----------------------------------------------------------------------------------------------------------------------
set_favicon(favicon)

if not test:
  server = app.server
else:
  application = app.server

if __name__ == '__main__':
    # FOR ALIBABA CLOUD
    if not test:
      app.run_server(debug=False)
    # FOR AWS
    else:
      application.run(debug=True,
                    # host='0.0.0.0',
                    port=8060)

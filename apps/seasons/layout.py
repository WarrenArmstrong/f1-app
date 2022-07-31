from pydoc import classname
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

#from .charts import seasons_chart

def layout(url):
    contents = [
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        dbc.Card(
                            children=[
                                dbc.CardBody(
                                    children=[
                                        dbc.Row(
                                            children=[
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Metric', width='auto'),
                                                        dbc.Select(
                                                            id='seasons_metric_select',
                                                            value='Podiums',
                                                            options=[
                                                                {'label': item, 'value': item}
                                                                for item in ['Points', 'Race Wins', 'Podiums', 'Championships']
                                                            ],
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Cumualtive', width='auto'),
                                                        dbc.Select(
                                                            id='seasons_cumulative_select',
                                                            value='True',
                                                            options=[
                                                                {'label': item, 'value': item}
                                                                for item in ['True', 'False']
                                                            ],
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Start Year', width='auto'),
                                                        dbc.Select(
                                                            id='seasons_start_year_select',
                                                            value=1950,
                                                            options=[
                                                                {'label': item, 'value': item}
                                                                for item in range(1950, 2023)
                                                            ],
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Top N', width='auto'),
                                                        dbc.Input(
                                                            id='seasons_top_n_input',
                                                            type='number',
                                                            value=10,
                                                            min=1,
                                                            max=1000,
                                                            step=1,
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                            ]
                                        ),
                                        dcc.Loading(dcc.Graph(id='seasons_rank_graph')),
                                    ]
                                )
                            ],
                            className='shadow mb-4',
                        )
                    ],
                    width=10,
                ),
            ]
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        dbc.Card(
                            children=[
                                dbc.CardBody(
                                    children=[
                                        dbc.Row(
                                            children=[
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Metric', width='auto'),
                                                        dbc.Select(
                                                            id='season_metric_select',
                                                            value='Points',
                                                            options=[
                                                                {'label': item, 'value': item}
                                                                for item in ['Points', 'Race Wins', 'Podiums']
                                                            ],
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Cumualtive', width='auto'),
                                                        dbc.Select(
                                                            id='season_cumulative_select',
                                                            value='True',
                                                            options=[
                                                                {'label': item, 'value': item}
                                                                for item in ['True', 'False']
                                                            ],
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Season', width='auto'),
                                                        dbc.Select(
                                                            id='season_season_select',
                                                            value=2021,
                                                            options=[
                                                                {'label': item, 'value': item}
                                                                for item in range(1950, 2023)
                                                            ],
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Top N', width='auto'),
                                                        dbc.Input(
                                                            id='season_top_n_input',
                                                            type='number',
                                                            value=10,
                                                            min=1,
                                                            max=1000,
                                                            step=1,
                                                        ),
                                                    ],
                                                    width=3,
                                                ),
                                            ]
                                        ),
                                        dcc.Loading(dcc.Graph(id='season_rank_graph')),
                                    ]
                                )
                            ],
                            className='shadow mb-4',
                        )
                    ],
                    width=10,
                ),
            ]
        ),
        dbc.Row(
            children=[
                dbc.Col(
                    children=[
                        dbc.Card(
                            children=[
                                dbc.CardBody(
                                    children=[
                                        dbc.Row(
                                            children=[
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Season', width='auto'),
                                                        dbc.Select(
                                                            id='race_season_select',
                                                            value=2021,
                                                            options=[
                                                                {'label': item, 'value': item}
                                                                for item in range(1996, 2023)
                                                            ],
                                                        ),
                                                    ],
                                                    width=4,
                                                ),
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Race', width='auto'),
                                                        dbc.Select(
                                                            id='race_race_select',
                                                            value='Abu Dhabi Grand Prix',
                                                            options=[
                                                                {'label': item, 'value': item}
                                                                for item in ['Abu Dhabi Grand Prix', 'Saudi Arabian Grand Prix']
                                                            ],
                                                        ),
                                                    ],
                                                    width=4,
                                                ),
                                                dbc.Col(
                                                    children=[
                                                        dbc.Label('Focus', width='auto'),
                                                        dbc.Select(
                                                            id='race_focus_select',
                                                            value='None',
                                                            options=[
                                                                {'label': item, 'value': item}
                                                                for item in ['Max Verstappen', 'None']
                                                            ],
                                                        ),
                                                    ],
                                                    width=4,
                                                ),
                                            ],
                                        ),
                                        #dcc.Loading(
                                            dcc.Graph(id='race_bump_graph')
                                        #),
                                    ]
                                )
                            ],
                            className='shadow mb-4',
                        )
                    ],
                    width=10,
                ),
            ]
        ),
        html.Div(id='seasons_placeholder'),
        html.Div(id='season_placeholder'),
    ]

    return contents
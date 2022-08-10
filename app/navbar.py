from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

from app import app



with open('README.md', 'r') as readme_file:
    readme = readme_file.read()


navbar = html.Div(
    children=[
        dbc.Navbar(
            children=[
                dbc.Container(
                    children=[
                        dcc.Link(
                            dbc.Row(
                                children=[
                                    dbc.Col([
                                        html.Img(src=r'\assets\f1_logo_cropped.png', height='30px')
                                    ])
                                ],
                            ),
                            href='/Home/'
                        ),
                        html.Div(
                            children=[
                                # dbc.Button(
                                #     children='Home',
                                #     color='secondary',
                                #     style={
                                #         'marginLeft': '20px',
                                #     }
                                # ),
                                dbc.Button(
                                    id='navbar_offcanvas_button',
                                    children='?',
                                    color='secondary',
                                    style={
                                        'marginLeft': '20px',
                                        'width': '40px',
                                    },
                                ),
                            ]
                        )

                        # dbc.Toast(
                        #     'Data Updated: ' + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M %p'),
                        #     #header="Info",
                        #     is_open=True,
                        #     dismissable=True,
                        #     icon='info',
                        #     style={"position": "fixed", "top": 66, "right": 10, "width": 260},
                        # ),
                    ]
                )
            ],
            color='white',
            className='shadow mb-4',
        ),
        dbc.Offcanvas(
            id='navbar_readme_offcanvas',
            title='Project Readme',
            is_open=False,
            style={
                'width': '750px',
            },
            children=[
                dcc.Markdown(
                    children=readme,
                    style={
                        'width': '700px',
                    },
                ),
            ],
        )
    ],
    className='sticky-top'
)

@app.callback(
    Output('navbar_readme_offcanvas', 'is_open'),
    Input('navbar_offcanvas_button', 'n_clicks'),
    [State('navbar_readme_offcanvas', 'is_open')],
)
def toggle_offcanvas(n_clicks, is_open):
    return not is_open if n_clicks else is_open
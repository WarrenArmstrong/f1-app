from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd

import apps

from app import app

from app_interface import app_list

navbar = dbc.Navbar(
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
                dbc.Toast(
                    'Data Updated: ' + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M %p'),
                    #header="Info",
                    is_open=True,
                    dismissable=True,
                    icon='info',
                    style={"position": "fixed", "top": 66, "right": 10, "width": 260},
                ),
            ]
        )
    ],
    color='white',
    className='shadow mb-4 sticky-top',
)

app.layout = html.Div(
    children=[
        dcc.Location(id='url', refresh=False),
        navbar,
        dbc.Container(id='app_content'),
    ]
)

@app.callback(
    Output('app_content', 'children'),
    Input('url', 'pathname')
)
def display_page(url):
    # for app in app_list:
    #     if app['routing']['path_is_valid'](url):
    #         return app['layout'](url)

    for app in app_list:
        if app['name'] == 'Seasons':
            return app['layout'](url)


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')
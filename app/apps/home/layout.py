from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

from app_interface import app_list

def page_card(name, path, description, thumbnail_path):
    card = dbc.Card(
        children=[
            dbc.CardHeader(
                html.H5(name),
                # dcc.Link(
                #     children=[
                #         html.H5(name)
                #     ],
                #     href=path
                # ),
                style={'background-color': '#FFFFFF'}
            ),

            dcc.Link(
                children=[
                    dbc.CardImg(
                        src=thumbnail_path,
                        top=True,
                        style={
                            'height': '200px',
                            'width': '305px',
                            'display': 'block',
                            'margin-left': 'auto',
                            'margin-right': 'auto',
                        },
                        className='center-block'
                    )
                ],
                href=path,
            ),
            dbc.CardBody(
                children=[
                    html.P(
                        description,
                        className='card-text'
                    )
                ]
            )
        ],
        className='shadow'
    )

    return card

def layout(url):
    cards = [
        dbc.Col(page_card(
            name=app['name'],
            path=app['routing']['default_path'],
            description=app['shortcut']['description'],
            thumbnail_path=app['shortcut']['thumbnail'],
        ))
        for app in app_list
        if 'shortcut' in app
        # dbc.Row([
        #     dbc.Col(
        #         children=[
        #             page_card(
        #                 name='DAN',
        #                 path='/DAN/',
        #                 description='DAN based tool for EDA and model evaluation',
        #                 thumbnail_path=r'\assets\dan_preview.png',
        #             ),
        #         ],
        #         width=3
        #     ),
        #     dbc.Col(
        #         page_card(
        #             name='Lift',
        #             path='/Lift/',
        #             description='Lift exhibit for model evaluation',
        #             thumbnail_path=r'\assets\lift_preview.png',
        #         ),
        #         width=3
        #     )]
        # )
    ]

    content = [dbc.Row(cards[i: i+3]) for i in range(0, len(cards), 3)]

    return content
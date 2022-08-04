from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

from sqlalchemy import create_engine
import os

app = Dash(
    __name__,
    title='F1',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

db_path = os.path.join(os.path.dirname(__file__), 'data.db')

engine = create_engine(f'sqlite:///{db_path}')

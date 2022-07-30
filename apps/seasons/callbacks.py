from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

from app import app

from . import charts

@app.callback(
    Output('seasons_rank_graph', 'figure'),
    Input('seasons_metric_select', 'value'),
    Input('seasons_cumulative_select', 'value'),
    Input('seasons_start_year_select', 'value'),
    Input('seasons_top_n_input', 'value'),
)
def seasons_update_rank_graph(metric, cumulative, start_year, top_n):
    return charts.seasons_rank_chart(metric, cumulative, start_year, top_n)


@app.callback(
    Output('season_rank_graph', 'figure'),
    Input('season_metric_select', 'value'),
    Input('season_cumulative_select', 'value'),
    Input('season_season_select', 'value'),
    Input('season_top_n_input', 'value'),
)
def seasons_update_rank_graph(metric, cumulative, season, top_n):
    return charts.season_rank_chart(metric, cumulative, season, top_n)
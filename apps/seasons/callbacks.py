from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

from dash.exceptions import PreventUpdate
import webbrowser

from app import app, engine

from . import charts

import pandas as pd


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


@app.callback(
    Output('race_bump_graph', 'figure'),
    Input('race_season_select', 'value'),
    Input('race_race_select', 'value'),
    Input('race_focus_select', 'value'),
)
def seasons_update_rank_graph(season, race, focus):
    return charts.race_bump_chart(season, race, focus)


@app.callback(
    Output('seasons_placeholder', 'children'),
    Input('seasons_rank_graph', 'clickData'),
)
def seasons_open_wiki(clickData):
    if clickData is None:
        raise PreventUpdate
    else:
        customdata = clickData['points'][0]['customdata']
        if not type(customdata[0]) is int:    
            url = clickData['points'][0]['customdata'][0]
            webbrowser.open_new_tab(url)
        else:
            raise PreventUpdate


@app.callback(
    Output('season_placeholder', 'children'),
    Input('season_rank_graph', 'clickData'),
)
def season_open_wiki(clickData):
    if clickData is None:
        raise PreventUpdate
    else:
        customdata = clickData['points'][0]['customdata']
        if not type(customdata[0]) is int:
            url = customdata[0]
            webbrowser.open_new_tab(url)
        else:
            raise PreventUpdate


@app.callback(
    Output('race_focus_select', 'value'),
    Input('race_bump_graph', 'clickData'),
)
def season_open_wiki(clickData):
    if clickData is None:
        return 'None'
    else:
        return clickData['points'][0]['customdata'][0]


@app.callback(
    Output('race_race_select', 'options'),
    Input('race_season_select', 'value'),
)
def race_race_select(season):
    races = pd.read_sql(
        con=engine,
        sql=f'''
            --sql
            
            SELECT name
            FROM dim_race
            WHERE year = {season}
            GROUP BY name
            ORDER BY MAX(date);
        '''
    )['name']

    options = [
        {'label': item, 'value': item}
        for item in races
    ]

    return options

@app.callback(
    Output('race_focus_select', 'options'),
    Input('race_season_select', 'value'),
    Input('race_race_select', 'value'),
)
def race_focus_select(season, race):
    drivers = ['None'] + pd.read_sql(
        con=engine,
        sql=f'''
            --sql
            
            SELECT d.full_name
            FROM
                fact_race_result AS rr
                LEFT JOIN dim_race AS r
                    ON rr.race_k = r.race_k
                LEFT JOIN dim_driver AS d
                    ON rr.driver_k = d.driver_k
            WHERE TRUE
                AND NOT rr.is_sprint
                AND r.year = {season}
                AND r.name = '{race}'
            GROUP BY d.full_name;
        '''
    )['full_name'].to_list()

    options = [
        {'label': item, 'value': item}
        for item in drivers
    ]

    return options


@app.callback(
    Output('race_season_select', 'value'),
    Output('race_race_select', 'value'),
    Input('season_rank_graph', 'clickData'),
)
def season_open_wiki_2(clickData):
    if clickData is None:
        raise PreventUpdate
    else:
        customdata = clickData['points'][0]['customdata']
        if type(customdata[0]) is int:
            return customdata[0], customdata[1]
        else:
            raise PreventUpdate

@app.callback(
    Output('season_season_select', 'value'),
    Input('seasons_rank_graph', 'clickData'),
)
def seasons_open_wiki(clickData):
    if clickData is None:
        raise PreventUpdate
    else:
        customdata = clickData['points'][0]['customdata']
        if type(customdata[0]) is int:
            return customdata[0]
        else:
            raise PreventUpdate
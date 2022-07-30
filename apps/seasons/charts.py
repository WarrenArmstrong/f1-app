import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import numpy as np
from random import sample
import itertools as it

from app import engine

def gen_color(df, cols):
    color_df = df[cols].drop_duplicates()

    color_df['color'] = list(it.islice(it.cycle(px.colors.qualitative.Dark24), color_df.shape[0]))

    return pd.merge(df, color_df, how='left', left_on=cols, right_on=cols)

def seasons_rank_chart(metric, cumulative, start_year, top_n):
    cumualtive_prefix = 'cumulative_' if cumulative == 'True' else ''

    df = pd.read_sql(
        con=engine,
        sql=f'''
            --sql
            
            WITH
                metrics AS (
                    SELECT
                        year,
                        type,
                        id,
                        name,
                        constructor_name,
                        constructor_color,
                        wiki_url,
                        season_wiki_url,
                        metric_value,
                        position,
                        SUM(COALESCE(metric_value, 0)) OVER (
                            PARTITION BY
                                id,
                                type
                            ORDER BY
                                year
                            ROWS BETWEEN
                                UNBOUNDED PRECEDING
                                AND CURRENT ROW
                        ) AS cumulative_metric_value
                    FROM report_seasons_metrics
                    WHERE TRUE
                        AND year >= {start_year}
                        AND metric = '{metric}'
                ),
                rankings AS (
                    SELECT
                        year,
                        type,
                        id,
                        name,
                        constructor_name,
                        constructor_color,
                        wiki_url,
                        season_wiki_url,
                        metric_value,
                        position,
                        cumulative_metric_value,
                        ROW_NUMBER() OVER (PARTITION BY year, type ORDER BY cumulative_metric_value DESC) AS cumulative_position
                    FROM metrics
                )
            SELECT
                year,
                type,
                id,
                name,
                constructor_name,
                constructor_color,
                wiki_url,
                season_wiki_url,
                {cumualtive_prefix}metric_value AS metric_value,
                {cumualtive_prefix}position AS position
            FROM rankings
            WHERE {cumualtive_prefix}position <= {top_n}
            ORDER BY year, type, position DESC;
        '''
    )

    frames_data = [
        {
            'frame_label': frame['year'],
            'df': df[df['year'] == frame['year']],
        }
        for frame in df[['year']].drop_duplicates().to_dict('records')
    ]

    def frame_figure(frame_data):
        df = frame_data['df']
        
        data = [
            go.Bar(
                x=df[df['type'] == 'Driver']['metric_value'],
                y=df[df['type'] == 'Driver']['name'],
                marker_color=df[df['type'] == 'Driver']['constructor_color'],
                xaxis='x1',
                yaxis='y1',
                #name=F'Driver {metric}',
                name='',
                legendgroup=1,
                showlegend=False,
                orientation='h',
                text=df[df['type'] == 'Driver']['constructor_name'],
                customdata=np.dstack([
                    df[df['type'] == 'Driver']['wiki_url'],
                    df[df['type'] == 'Driver']['constructor_name'],
                ])[0],
                hovertemplate= '<br>'.join([
                    'Driver: %{y}',
                    'Constructor: %{customdata[1]}',
                    f'{metric}: %{{x}}',
                ]),
            ),
            go.Bar(
                x=df[df['type'] == 'Constructor']['metric_value'],
                y=df[df['type'] == 'Constructor']['name'],
                marker_color=df[df['type'] == 'Constructor']['constructor_color'],
                xaxis='x2',
                yaxis='y2',
                #name=f'Constructor {metric}',
                name='',
                legendgroup=2,
                showlegend=False,
                orientation='h',
                text=df[df['type'] == 'Constructor']['constructor_name'],
                customdata=np.dstack([
                    df[df['type'] == 'Constructor']['wiki_url'],
                ])[0],
                hovertemplate= '<br>'.join([
                    'Constructor: %{y}',
                    f'{metric}: %{{x}}',
                ]),
            ),
        ]

        season_wiki_url = df['season_wiki_url'].iloc[0]

        layout = {
            'annotations': [
                {
                    'text': f'<a href="{season_wiki_url}">Season Wiki</a>',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1,
                    'y': 0.475,
                }
            ],
        }

        fig = {
            'data': data,
            'layout': layout,
        }

        return fig

    season_wiki_url = df['season_wiki_url'].iloc[0]

    fig = go.Figure({
        'data': frame_figure(frames_data[0])['data'],
        'layout': {
            'template': 'gridon',
            'height': 700,
            'margin': {
                't': 30,
                'b': 0,
                'l': 200,
            },
            'legend': {
                'orientation': 'h',
                'y': 1.30,
            },
            'font': {
                'size': 16,
            },
            'hovermode': 'y',
            'xaxis1': {
                'title': metric,
                'range': [0, df[df['type'] == 'Driver']['metric_value'].max()],
                'anchor': 'y1',
            },
            'xaxis2': {
                'title': metric,
                'range': [0, df[df['type'] == 'Constructor']['metric_value'].max()],
                'anchor': 'y2',
            },
            'yaxis1': {
                'title': 'Driver',
                'domain': [0.6, 1],
            },
            'yaxis2': {
                'title': 'Constructor',
                'domain': [0, 0.4]
            },
            'annotations': [
                {
                    'text': f'<a href="{season_wiki_url}">Season Wiki</a>',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1,
                    'y': 0.475,
                }
            ],
            'updatemenus': [
                {
                    'buttons': [
                        {
                            'args': [
                                None,
                                {
                                    'frame': {
                                        'duration': 100,
                                        'redraw': True,
                                    },
                                    'fromcurrent': True,
                                    'transition': {
                                        'duration': 0,
                                        'easing': 'linear',
                                    }
                                }
                            ],
                            'label': 'Play',
                            'method': 'animate',
                        },
                        {
                            'args': [
                                [None],
                                {
                                    'frame': {
                                        'duration': 0,
                                        'redraw': True,
                                    },
                                    'mode': 'immediate',
                                    'transition': {
                                        'duration': 0,
                                    }
                                }
                            ],
                            'label': 'Pause',
                            'method': 'animate',
                        }
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 87},
                    "showactive": False,
                    "type": "buttons",
                    "x": 0.1,
                    "xanchor": "right",
                    "y": 0,
                    "yanchor": "top"
                },
            ],
            'sliders': [{
                'yanchor': 'top',
                'xanchor': 'left',
                'currentvalue': {
                    'font': {"size": 20},
                    'prefix': ' Season:',
                    'visible': True,
                    'xanchor': 'right',
                },
                'transition': {
                    'duration': 0,
                    'easing': 'linear',
                },
                'pad': {
                    'b': 10,
                    't': 50
                },
                'len': 0.9,
                'x': 0.1,
                'y': 0,
                'steps': [
                    {
                        'args': [
                            [frame_label],
                            {
                                'frame': {
                                    'duration': 0,
                                    'redraw': True,
                                },
                                'mode': 'immediate',
                                'transition': {'duration': 0}
                            }
                        ],
                        'label': str(frame_label),
                        'method': 'animate',
                    }
                    for frame_label in
                    map(lambda row: row['frame_label'], frames_data)
                ]
            }]
        },
        'frames': [
            {
                'name': str(frame['frame_label']),
                'data': frame_figure(frame)['data'],
                'layout': frame_figure(frame)['layout'],
            }
            for frame in frames_data
        ]
    })

    return fig


def season_rank_chart(metric, cumulative, season, top_n):
    df = pd.read_sql(
        con=engine,
        sql=f'''
            --sql
            
            SELECT *
            FROM report_season_metrics
            WHERE TRUE
                AND year = {season}
                AND metric = '{metric}'
                AND {'' if cumulative == 'True' else 'not '} is_cumulative
                AND position <= {top_n}
            ORDER BY race_date, type, position DESC;
        '''
    )

    frames_data = [
        {
            'frame_label': frame['race'],
            'df': df[df['race'] == frame['race']],
        }
        for frame in df[['race']].drop_duplicates().to_dict('records')
    ]

    def frame_figure(frame_data):
        df = frame_data['df']
        
        data = [
            go.Bar(
                x=df[df['type'] == 'Driver']['metric_value'],
                y=df[df['type'] == 'Driver']['name'],
                marker_color=df[df['type'] == 'Driver']['constructor_color'],
                xaxis='x1',
                yaxis='y1',
                #name='Driver Points',
                name='',
                legendgroup=1,
                showlegend=False,
                orientation='h',
                text=df[df['type'] == 'Driver']['constructor_name'],
                customdata=np.dstack([
                    df[df['type'] == 'Driver']['wiki_url'],
                    df[df['type'] == 'Driver']['constructor_name'],
                ])[0],
                hovertemplate= '<br>'.join([
                    'Driver: %{y}',
                    'Constructor: %{customdata[1]}',
                    f'{metric}: %{{x}}',
                ]),
            ),
            go.Bar(
                x=df[df['type'] == 'Constructor']['metric_value'],
                y=df[df['type'] == 'Constructor']['name'],
                marker_color=df[df['type'] == 'Constructor']['constructor_color'],
                xaxis='x2',
                yaxis='y2',
                #name='Constructor Points',
                name='',
                legendgroup=2,
                showlegend=False,
                orientation='h',
                text=df[df['type'] == 'Constructor']['constructor_name'],
                customdata=np.dstack([
                    df[df['type'] == 'Constructor']['wiki_url'],
                ])[0],
                hovertemplate= '<br>'.join([
                    'Constructor: %{y}',
                    f'{metric}: %{{x}}',
                ]),
            ),
        ]

        race_wiki_url = df['race_wiki_url'].iloc[0]
        circuit_wiki_url = df['circuit_wiki_url'].iloc[0]
        season_wiki_url = df['season_wiki_url'].iloc[0]

        layout = {
            'annotations': [
                {
                    'text': f'<a href="{race_wiki_url}">Race Wiki</a>',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1,
                    'y': 0.475,
                },
                {
                    'text': f'<a href="{circuit_wiki_url}">Circuit Wiki</a>',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1,
                    
                    'y': 0.525,
                },
                {
                    'text': f'<a href="{season_wiki_url}">Season Wiki</a>',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1,
                    'y': 0.425,
                },
            ],
        }

        fig = {
            'data': data,
            'layout': layout,
        }

        return fig

    race_wiki_url = df['race_wiki_url'].iloc[0]
    circuit_wiki_url = df['circuit_wiki_url'].iloc[0]
    season_wiki_url = df['season_wiki_url'].iloc[0]

    fig = go.Figure({
        'data': frame_figure(frames_data[0])['data'],
        'layout': {
            'template': 'gridon',
            'height': 700,
            'margin': {
                't': 30,
                'b': 0,
                'l': 200,
            },
            'legend': {
                'orientation': 'h',
                'y': 1.30,
            },
            'font': {
                'size': 16,
            },
            'hovermode': 'y',
            'xaxis1': {
                'title': metric,
                'range': [0, df[df['type'] == 'Driver']['metric_value'].max()],
                'anchor': 'y1',
            },
            'xaxis2': {
                'title': metric,
                'range': [0, df[df['type'] == 'Constructor']['metric_value'].max()],
                'anchor': 'y2',
            },
            'yaxis1': {
                'title': 'Driver',
                'domain': [0.6, 1],
            },
            'yaxis2': {
                'title': 'Constructor',
                'domain': [0, 0.4]
            },
            'annotations': [
                {
                    'text': f'<a href="{race_wiki_url}">Race Wiki</a>',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1,
                    'y': 0.475,
                },
                {
                    'text': f'<a href="{circuit_wiki_url}">Circuit Wiki</a>',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1,
                    
                    'y': 0.525,
                },
                {
                    'text': f'<a href="{season_wiki_url}">Season Wiki</a>',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1,
                    'y': 0.425,
                },
            ],
            'updatemenus': [
                {
                    'buttons': [
                        {
                            'args': [
                                None,
                                {
                                    'frame': {
                                        'duration': 100,
                                        'redraw': True,
                                    },
                                    'fromcurrent': True,
                                    'transition': {
                                        'duration': 0,
                                        'easing': 'linear',
                                    }
                                }
                            ],
                            'label': 'Play',
                            'method': 'animate',
                        },
                        {
                            'args': [
                                [None],
                                {
                                    'frame': {
                                        'duration': 0,
                                        'redraw': True,
                                    },
                                    'mode': 'immediate',
                                    'transition': {
                                        'duration': 0,
                                    }
                                }
                            ],
                            'label': 'Pause',
                            'method': 'animate',
                        }
                    ],
                    "direction": "left",
                    "pad": {"r": 10, "t": 87},
                    "showactive": False,
                    "type": "buttons",
                    "x": 0.1,
                    "xanchor": "right",
                    "y": 0,
                    "yanchor": "top"
                },
            ],
            'sliders': [{
                'yanchor': 'top',
                'xanchor': 'left',
                'currentvalue': {
                    'font': {"size": 20},
                    'prefix': '',
                    'visible': True,
                    'xanchor': 'right',
                },
                'transition': {
                    'duration': 0,
                    'easing': 'linear',
                },
                'pad': {
                    'b': 10,
                    't': 50
                },
                'len': 0.9,
                'x': 0.1,
                'y': 0,
                'steps': [
                    {
                        'args': [
                            [frame_label],
                            {
                                'frame': {
                                    'duration': 0,
                                    'redraw': True,
                                },
                                'mode': 'immediate',
                                'transition': {'duration': 0}
                            }
                        ],
                        'label': str(frame_label),
                        'method': 'animate',
                    }
                    for frame_label in
                    map(lambda row: row['frame_label'], frames_data)
                ]
            }]
        },
        'frames': [
            {
                'name': str(frame['frame_label']),
                'data': frame_figure(frame)['data'],
                'layout': frame_figure(frame)['layout'],
            }
            for frame in frames_data
        ]
    })

    return fig
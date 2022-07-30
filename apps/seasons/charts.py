import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
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
                #name='Driver Points',
                legendgroup=1,
                showlegend=False,
                orientation='h',
                text=df[df['type'] == 'Driver']['constructor_name']
            ),
            go.Bar(
                x=df[df['type'] == 'Constructor']['metric_value'],
                y=df[df['type'] == 'Constructor']['name'],
                marker_color=df[df['type'] == 'Constructor']['constructor_color'],
                xaxis='x2',
                yaxis='y2',
                #name='Constructor Points',
                legendgroup=2,
                showlegend=False,
                orientation='h',
                text=df[df['type'] == 'Constructor']['constructor_name']
            ),
        ]

        return data

    fig = go.Figure({
        'data': frame_figure(frames_data[0]),
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
                'data': frame_figure(frame),
                'name': str(frame['frame_label']),
            }
            for frame in frames_data
        ]
    })

    return fig


def season_rank_chart(metric, cumulative, season, top_n):
    cumualtive_prefix = 'cumulative_' if cumulative == 'True' else ''

    df = pd.read_sql(
        con=engine,
        sql=f'''
            --sql
            
            WITH
                metrics AS (
                    SELECT
                        year,
                        race,
                        race_date,
                        type,
                        id,
                        name,
                        constructor_name,
                        constructor_color,
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
                    FROM report_season_metrics
                    WHERE TRUE
                        AND year = {season}
                        AND metric = '{metric}'
                ),
                rankings AS (
                    SELECT
                        year,
                        race,
                        race_date,
                        type,
                        id,
                        name,
                        constructor_name,
                        constructor_color,
                        metric_value,
                        position,
                        cumulative_metric_value,
                        ROW_NUMBER() OVER (PARTITION BY race, type ORDER BY cumulative_metric_value DESC) AS cumulative_position
                    FROM metrics
                )
            SELECT
                year,
                race,
                race_date,
                type,
                id,
                name,
                constructor_name,
                constructor_color,
                {cumualtive_prefix}metric_value AS metric_value,
                {cumualtive_prefix}position AS position
            FROM rankings
            WHERE {cumualtive_prefix}position <= {top_n}
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
                legendgroup=1,
                showlegend=False,
                orientation='h',
                text=df[df['type'] == 'Driver']['constructor_name'],
            ),
            go.Bar(
                x=df[df['type'] == 'Constructor']['metric_value'],
                y=df[df['type'] == 'Constructor']['name'],
                marker_color=df[df['type'] == 'Constructor']['constructor_color'],
                xaxis='x2',
                yaxis='y2',
                #name='Constructor Points',
                legendgroup=2,
                showlegend=False,
                orientation='h',
                text=df[df['type'] == 'Constructor']['constructor_name'],
            ),
        ]

        return data

    fig = go.Figure({
        'data': frame_figure(frames_data[0]),
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
                'data': frame_figure(frame),
                'name': str(frame['frame_label']),
            }
            for frame in frames_data
        ]
    })

    return fig
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
    df = pd.read_sql(
        con=engine,
        sql=f'''
            --sql
            
        WITH
            vector(idx) AS (
                SELECT 0 AS idx
                UNION ALL
                SELECT idx + 1 AS idx
                FROM vector
                WHERE idx <= 10
            ),
            season_drivers AS (
                SELECT
                    d.*
                FROM
                    fact_race_result AS rr
                    LEFT JOIN dim_race AS r
                        ON rr.race_k = r.race_k
                    LEFT JOIN dim_driver AS d
                        ON rr.driver_k = d.driver_k
                WHERE r.year = {season}
                GROUP BY rr.driver_k
            ),
            season_constructors AS (
                SELECT
                    c.*
                FROM
                    fact_race_result AS rr
                    LEFT JOIN dim_race AS r
                        ON rr.race_k = r.race_k
                    LEFT JOIN dim_constructor AS c
                        ON rr.constructor_k = c.constructor_k
                WHERE r.year = {season}
                GROUP BY rr.constructor_k
            ),
            season_races AS (
                SELECT *
                FROM dim_race
                WHERE year = {season}
            ),
            driver_metrics AS (
                SELECT
                    r.name AS race,
                    r.date AS race_date,
                    'Driver' AS type,
                    d.driver_k AS id,
                    d.full_name AS name,
                    COALESCE(c.name, 'No Constructor') AS constructor_name,
                    COALESCE(c.color, '#BAB0AC') AS constructor_color,
                    SUM(rr.points) AS points,
                    SUM(CASE WHEN NOT rr.is_sprint THEN rr.position = 1 ELSE 0 END) AS race_wins,
                    SUM(CASE WHEN NOT rr.is_sprint THEN rr.position BETWEEN 1 AND 3 ELSE 0 END) AS podiums
                FROM
                    season_drivers AS d
                    CROSS JOIN season_races AS r
                    LEFT JOIN fact_race_result AS rr
                        ON r.race_k = rr.race_k
                        AND d.driver_k = rr.driver_k
                    LEFT JOIN dim_constructor AS c
                        ON rr.constructor_k = c.constructor_k
                GROUP BY
                    r.race_k,
                    d.driver_k
            ),
            constructor_metrics AS (
                SELECT
                    r.name AS race,
                    r.date AS race_date,
                    'Constructor' AS type,
                    c.constructor_k AS id,
                    c.name AS name,
                    c.name AS constructor_name,
                    c.color AS constructor_color,
                    SUM(rr.points) AS points,
                    SUM(CASE WHEN NOT rr.is_sprint THEN rr.position = 1 ELSE 0 END) AS race_wins,
                    SUM(CASE WHEN NOT rr.is_sprint THEN rr.position BETWEEN 1 AND 3 ELSE 0 END) AS podiums
                FROM
                    season_constructors AS c
                    CROSS JOIN season_races AS r
                    LEFT JOIN fact_race_result AS rr
                        ON r.race_k = rr.race_k
                        AND c.constructor_k = rr.constructor_k
                GROUP BY
                    r.race_k,
                    c.constructor_k
            ),
            combined_metrics AS (
                SELECT * FROM driver_metrics
                UNION ALL
                SELECT * FROM constructor_metrics
            ),
            unpivoted_metrics AS (
                SELECT
                    m.race,
                    m.race_date,
                    m.type,
                    m.id,
                    m.name,
                    m.constructor_name,
                    m.constructor_color,
                    CASE
                        WHEN v.idx = 0 THEN 'Points'
                        WHEN v.idx = 1 THEN 'Race Wins'
                        WHEN v.idx = 2 THEN 'Podiums'
                    END AS metric,
                    CASE
                        WHEN v.idx = 0 THEN m.points
                        WHEN v.idx = 1 THEN m.race_wins
                        WHEN v.idx = 2 THEN m.podiums
                    END AS metric_value,
                    FALSE AS is_cumulative
                FROM
                    combined_metrics AS m
                    CROSS JOIN vector AS v
                WHERE v.idx <= 2
            ),
            cumulative_unpivoted_metrics AS (
                SELECT
                    race,
                    race_date,
                    type,
                    id,
                    name,
                    constructor_name,
                    constructor_color,
                    metric,
                    SUM(COALESCE(metric_value, 0)) OVER (
                        PARTITION BY
                            id,
                            type,
                            metric
                        ORDER BY
                            race_date
                        ROWS BETWEEN
                            UNBOUNDED PRECEDING
                            AND CURRENT ROW
                    ) AS metric_value,
                    TRUE AS is_cumulative
                FROM unpivoted_metrics
            ),
            combined_unpivoted_metrics AS (
                SELECT * FROM unpivoted_metrics
                UNION ALL
                SELECT * FROM cumulative_unpivoted_metrics
            ),
            rankings AS (
                SELECT
                    race,
                    race_date,
                    type,
                    id,
                    name,
                    constructor_name,
                    constructor_color,
                    metric,
                    metric_value,
                    is_cumulative,
                    ROW_NUMBER() OVER (PARTITION BY race, type, metric, is_cumulative ORDER BY metric_value DESC) AS position
                FROM combined_unpivoted_metrics
            )
        SELECT * FROM rankings
        WHERE TRUE
            AND position <= {top_n}
            AND {'' if cumulative == 'True' else 'not '} is_cumulative
            AND metric = '{metric}'
        ORDER BY race_date, is_cumulative, metric, type, position DESC;
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
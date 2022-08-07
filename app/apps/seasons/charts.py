import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import numpy as np
import itertools as it

from app import engine

def text_color(background_color):
    background_color = background_color.lstrip('#')
    
    r, g, b = tuple(int(background_color[i:i+2], 16) for i in (0, 2, 4))

    brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000

    return '#FFFFFF' if brightness < 125 else '#000000'


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
        year = frame_data['frame_label']
        
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
            'title': {
                'text': f"{'Cumulative ' if cumulative == 'True' else ''}{metric} by Season and Driver/Constructor",
                'y': 0.975
            },
            'template': 'gridon',
            'height': 720,
            'margin': {
                't': 50,
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
                #'title': metric,
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
                },
                {
                    'text': f'Click Bars for Driver/Constructor Wiki',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.475,
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
        race = frame_data['frame_label']
        
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
            'title': {
                'text': f"{'Cumulative ' if cumulative == 'True' else ''}{metric} by Race and Driver/Constructor in {season}",
                'y': 0.975
            },
            'template': 'gridon',
            'height': 720,
            'margin': {
                't': 50,
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
                #'title': metric,
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
                {
                    'text': f'Click Bars for Driver/Constructor Wiki',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 0.5,
                    'y': 0.475,
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

def race_bump_chart(season, race, focus):
    df = pd.read_sql(
        con=engine,
        sql=f'''
            --sql
            
            SELECT *
            FROM report_race_metrics
            WHERE TRUE
                AND year = {season}
                AND race_name = '{race}'
            ORDER BY year, race_date, constructor_name, driver_name, lap;
        '''
    )

    fig = go.Figure({
        'data': [
            go.Scatter(
                x=df[df['driver_name'] == driver_name]['lap'],
                y=df[df['driver_name'] == driver_name]['position'],
                xaxis='x1',
                yaxis='y1',
                marker_color=df[df['driver_name'] == driver_name]['constructor_color'].iloc[0],
                name=driver_name,
                showlegend=False,
                mode='lines+markers+text',
                text=df[df['driver_name'] == driver_name]['ending_status'],
                marker={
                    'size': 10,
                },
                line={
                    'width': 10,
                },  
                textposition='middle right',
                opacity=0.75 if focus in [driver_name, 'None'] else 0.25,
                customdata=np.dstack([
                    df[df['driver_name'] == driver_name]['driver_name'],
                    df[df['driver_name'] == driver_name]['constructor_name'],
                ])[0],
                hovertemplate= '<br>'.join([
                    'Driver: %{customdata[0]}',
                    'Constructor: %{customdata[1]}',
                    'Lap: %{x}',
                    'Position: %{y}',
                ]),
            )
            for driver_name in df['driver_name'].unique()
        ],
        'layout': {
            'title': f'{season} {race} Bump Chart',
            'template': 'simple_white',
            'height': 720,
            'margin': {
                'r': 50,
            },
            'font': {
                'size': 16,
            },
            'xaxis1': {
                'title': 'Lap #',
                'range': [-0, df['lap'].max() * 1.09],
                #'domain': [0.2, 0.8],
            },
            'yaxis1': {
                'title':'Position',
                'range': [df['position'].max() + 0.2, 0.7],
                'visible': False,
            },
            'annotations': [
                {
                    'text': f'Click Line to Focus',
                    'align': 'left',
                    'showarrow': False,
                    'xref': 'paper',
                    'yref': 'paper',
                    'x': 1,
                    'y': 1.1,
                }
            ] + [
                {
                    'text': row['driver_code'],
                    'font': {
                        'color': text_color(row['constructor_color'])
                    },
                    'align': 'center',
                    'showarrow': False,
                    'xref': 'x1',
                    'xanchor': 'left',
                    'yref': 'y1',
                    'x': df['lap'].max() * 1.09,
                    'y': row['position'],
                    'bgcolor': row['constructor_color'],
                    'width': 40,
                }
                for row in df[~df['ending_status'].isna()].sort_values(by='position').to_dict('records')
            ] + [
                {
                    'text': row['driver_code'],
                    'font': {
                        'color': text_color(row['constructor_color'])
                    },
                    'align': 'center',
                    'showarrow': False,
                    'xref': 'x1',
                    'xanchor': 'right',
                    'yref': 'y1',
                    'x': 0,
                    'y': row['position'],
                    'bgcolor': row['constructor_color'],
                    'width': 40,
                }
                for row in df[df['lap'] == 0].sort_values(by='position').to_dict('records')
            ]
        },
    })

    return fig
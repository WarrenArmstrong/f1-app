from app_interface import app_list

from .layout import layout

import re

app_list.append({
    'routing': {
        'path_is_valid': lambda path: bool(re.match(r'^\/Seasons\/$', path)),
        'default_path': '/Seasons/',
    },
    'name': 'Seasons',
    'shortcut': {
        'thumbnail': r'',
        'description': 'Shows F1 results by Season',
    },
    'layout': layout,
})
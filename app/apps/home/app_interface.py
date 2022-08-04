from app_interface import app_list

from .layout import layout

import re

app_list.append({
    'routing': {
        'path_is_valid': lambda path: bool(re.match(r'^\/Home\/$|^\/$|^$', path)),
        'default_path': '/Home/',
    },
    'name': 'Home',
    # 'shortcut': {
    #     'thumbnail': '',
    #     'description': '',
    # }
    'layout': layout
})
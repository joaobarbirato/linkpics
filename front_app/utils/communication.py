from urllib.request import urlopen

from flask import json
from requests import post

from front_app import front_app

__BASE_URL = '127.0.0.1:9444'

__ALIGN_URL = '/align/'
__ALL_JSON_URL = '/align/all_json'


def request_to_back(action='', **kwargs):
    r = None
    if action == 'align' or action == '' and 'url' in kwargs:
        r = post(f'http://{__BASE_URL}{__ALIGN_URL}?link={kwargs["url"]}')
    elif action == 'all_json' and 'linklist' in kwargs and 'restriction' in kwargs:
        r = post(f'http://{__BASE_URL}{__ALL_JSON_URL}?restriction={kwargs["restriction"]}&linklist={",".join(kwargs["linklist"])}')
    return front_app.response_class(
        response=r.text,
        status=r.status_code,
        mimetype='application/json',
        direct_passthrough=True,
    )

import os
import re
from math import floor

from flask import Markup, url_for

from . import app


@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)


@app.template_filter('hyperlink')
def hyperlink(value):
    if not value:
        return value
    url_re = re.compile(r'(?:(?:https?|ftp|file):\/\/|www\.|ftp\.)' +
                        r'(?:\([-A-Z0-9+&@#\/%=~_|$?!:,.]*\)|[-A-Z' +
                        r'0-9+&@#\/%=~_|$?!:,.])*(?:\([-A-Z0-9+&@#' +
                        r'\/%=~_|$?!:,.]*\)|[A-Z0-9+&@#\/%=~_|$])',
                        flags=re.IGNORECASE)
    result = url_re.sub(r'<a target="_blank" href="\g<0>">Link</a>', value)
    result = Markup(result)
    return result


@app.template_filter('optional_decimal')
def optional_decimal(number):
    if floor(number) == number:
        return (floor(number))
    else:
        return number

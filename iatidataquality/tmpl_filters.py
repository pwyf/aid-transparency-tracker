import re

from flask import Markup

from . import app


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

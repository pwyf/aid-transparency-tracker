
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import collections
from contextlib import contextmanager
import json
import os
import traceback
import urllib.request, urllib.error, urllib.parse
import ssl

from flask import request, current_app


@contextmanager
def report_error(success, failure):
    try:
        yield
        if success is not None:
            print(success)
    except Exception as e:
        if failure is not None:
            print(failure, e)
            #print traceback.print_exc()

def ensure_download_dir(directory):
    if not os.path.exists(directory):
        with report_error(None, "Couldn't create directory"):
            os.makedirs(directory)

def download_file(url, path):
    with open(path, 'w') as localFile:
        req = urllib.request.Request(url, headers={'User-Agent': 'PWYF/Aid Transparency Tracker'})
        webFile = urllib.request.urlopen(req)
        localFile.write(webFile.read())
        webFile.close()

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def jsonify(*args, **kwargs):
    return current_app.response_class(json.dumps(dict(*args, **kwargs),
            indent=None if request.is_xhr else 2, cls=JSONEncoder),
        mimetype='application/json')

def resort_sqlalchemy_indicator(data):
    resort_fn = lambda x: x[1]['indicator']['indicator_order']

    new = sorted(list(data.items()),key=resort_fn)
    return collections.OrderedDict(new)

def resort_dict_indicator(data):
    resort_fn = lambda x: x[1]['indicator']['indicator_order']
    new = sorted(list(data.items()),
                    key=resort_fn)
    return collections.OrderedDict(new)

def group_by_subcategory(data):
    grouped_data = collections.OrderedDict()
    for x in list(data.values()):
        subcat = x['indicator']['indicator_subcategory_name']
        if subcat not in grouped_data:
            grouped_data[subcat] = []
        grouped_data[subcat].append(x)
    return grouped_data

def resort_indicator_tests(data):
    resort_fn = lambda x: x[1]['indicator_order']
    new = sorted(list(data.items()),
                    key=resort_fn)
    return collections.OrderedDict(new)

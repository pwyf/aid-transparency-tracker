
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import contextlib
import os
import urllib2
import json
from flask import request, current_app
import traceback
import collections

@contextlib.contextmanager
def report_error(success, failure):
    try:
        yield
        if success is not None:
            print success
    except Exception, e:
        if failure is not None:
            print failure, e
            #print traceback.print_exc()
    finally:
        pass

def ensure_download_dir(directory):
    if not os.path.exists(directory):
        with report_error(None, "Couldn't create directory"):
            os.makedirs(directory)

def download_file(url, path):
    with file(path, 'w') as localFile:
        webFile = urllib2.urlopen(url)
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
    resort_fn = lambda x, y: cmp(x[1]['indicator'].indicator_order,
                                        y[1]['indicator'].indicator_order)
    new = sorted(data.items(),
                    cmp=resort_fn)
    return collections.OrderedDict(new)

def resort_dict_indicator(data):
    resort_fn = lambda x, y: cmp(x[1]['indicator']['indicator_order'],
                                        y[1]['indicator']['indicator_order'])
    new = sorted(data.items(),
                    cmp=resort_fn)
    return collections.OrderedDict(new)

def resort_indicator_tests(data):
    resort_fn = lambda x, y: cmp(x[1]["indicator_order"],
                                        y[1]["indicator_order"])
    new = sorted(data.items(),
                    cmp=resort_fn)
    return collections.OrderedDict(new)

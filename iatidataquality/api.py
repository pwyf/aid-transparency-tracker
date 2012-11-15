from flask import Flask, abort, url_for, redirect, request, current_app
from functools import wraps
import json
import models
from sqlalchemy import func
import math

from iatidataquality import app, db

import datetime
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def jsonify(*args, **kwargs):
    return current_app.response_class(json.dumps(dict(*args, **kwargs),
            indent=None if request.is_xhr else 2, cls=JSONEncoder),
        mimetype='application/json')

def support_jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs).data)
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return current_app.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_function

class AggregatedTestResults:
    def make_division(self,i):
        return [i* self.divisions, (i+1) * self.divisions]
    def x_axis(self):
        return map(self.make_division, range(self.n))
    def __init__(self, n, data):
        self.n = n
        self.data = data
        self.divisions = 100.0/n
    def aggregate_data(self):
        out = [0] * self.n
        for value in self.data.values():
            if value == 100.0: out[-1] += 1
            else: out[ int(math.floor(value/(100.0/self.n))) ] += 1
        return out
    def create_report(self):
        return {"data" : self.aggregate_data(), "x_axis": self.x_axis()}

def test_percentages(data):
    packages = set(map(lambda x: x[2], data))
    d = dict(map(lambda x: ((x[2],x[1]),x[0]), data))
    out = {}
    for p in packages:
        try: fail = d[(p,0)]
        except: fail = 0
        try: success = d[(p,1)]
        except: success = 0
        out[p] =  (float(success)/(fail+success)) * 100
    return out

def test_tuples(data):
    packages = set(map(lambda x: x[2], data))
    d = dict(map(lambda x: ((x[2],x[1]),x[0]), data))
    out = {}
    for p in packages:
        try: fail = d[(p,0)]
        except: fail = 0
        try: success = d[(p,1)]
        except: success = 0
        out[p] = (success, fail+success) 
    return out

def aggregated_test_results(data):
    return AggregatedTestResults(10, test_percentages(data)).create_report()

def results_by_org(data, packages):
    tests = test_tuples(data)
    package_dict = map(lambda x: x.as_dict(), packages)
    for package in package_dict:
        try:
            package['passed'] = tests[package['id']][0]
            package['total'] = tests[package['id']][1]
        except KeyError:
            package['passed'] = 0
            package['total'] = 0
    return package_dict 

@app.route("/api/")
def api_index():
    return jsonify({"packages": url_for("api_packages"), "tests":url_for("tests")})

@app.route("/api/tests/")
def api_tests():
    session = db.session
    data = session.query(func.count(models.Result.id),
                models.Result.result_data,
                models.Result.test_id
            ).group_by(models.Result.test_id
            ).group_by(models.Result.result_data).all()
    percentage_passed = test_percentages(data)

    tests = map(lambda x: x.as_dict(),
                session.query(models.Test).all()
            )
    for test in tests:
        try:
            test["percentage_passed"] = percentage_passed[test['id']] 
        except KeyError:
            test["percentage_passed"] = ""
    return jsonify({"tests": tests})

@app.route("/api/tests/<test_id>")
def api_test(test_id):
    test = db.session.query(models.Test).filter(models.Test.id == test_id).first()
    if test == None:
        abort(404)
    else:
        return jsonify(test.as_dict())

@app.route("/api/packages/")
@support_jsonp
def api_packages():
    packages = db.session.query(models.Package).all()

    session = db.session
    data = session.query(func.count(models.Result.id),
                models.Result.result_data,
                models.Result.package_id
            ).group_by(models.Result.package_id
            ).group_by(models.Result.result_data).all()

    return jsonify(
                   aggregated_test_results= aggregated_test_results(data), results_by_org=results_by_org(data, packages))

@app.route('/api/packages/<package_name>')
@support_jsonp
def api_package(package_name):
    package = db.session.query(models.Package).filter(models.Package.package_name == package_name).first()
    if package == None:
        abort(404)
    else:
        return jsonify(package.as_dict())


from flask import Flask, abort, url_for, jsonify, redirect, request, current_app
from functools import wraps
import json
import models
import database
import random
from sqlalchemy import func
import math

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
            out[ int(math.floor(value/(100.0/self.n))) ] += 1
        return out
    def create_report(self):
        return {"data" : self.aggregate_data(), "x_axis": self.x_axis()}


app = Flask(__name__)
app.config.from_pyfile('config.py')

def test_results():
    session = database.db_session
    data = session.query(func.count(models.Result.id),
                models.Result.result_data,
                models.Result.package_id
            ).group_by(models.Result.package_id
            ).group_by(models.Result.result_data).all()
    packages = set(map(lambda x: x[2], data))
    d = dict(map(lambda x: ((x[2],x[1]),x[0]), data))
    out = {}
    for p in packages:
        try: fail = d[(p,0)]
        except: fail = 0
        try: success = d[(p,1)]
        except: success = 0
        out[p] =  float(success)/fail+success
    return out

def aggregated_test_results():
    return AggregatedTestResults(10, test_results()).create_report()

@app.route("/packages/")
@support_jsonp
def packages():
    packages = database.db_session.query(models.Package).all()
    package_links = map(
        lambda package: {"link": url_for( "package", package_name=package.package_name)},
        packages)

    return jsonify(packages=package_links,
                   aggregated_test_results= aggregated_test_results())

@app.route('/packages/<package_name>')
@support_jsonp
def package(package_name):
    package = database.db_session.query(models.Package).filter(models.Package.package_name == package_name).first()
    if package == None:
        abort(404)
    else:
        return jsonify(package.as_dict())

if __name__ == '__main__':
    app.debug = True
    database.init_db()

    print
    print
    print test_results()
    app.run()


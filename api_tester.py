from flask import Flask, abort, url_for, jsonify, redirect, request, current_app
from functools import wraps
import json
import models
import database
import random

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
   def __init__(self, n):
    self.n = n
    self.divisions = 100.0/n
   def fake_data(self):
       return map (lambda i: random.randint(10, 200), range(self.n))
   def create_report(self):
    return {"data" : self.fake_data(), "x_axis": self.x_axis()}


app = Flask(__name__)
app.config.from_pyfile('config.py')


def aggregated_test_results():
    return AggregatedTestResults(10).create_report()

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

@app.route("/tests/")
@support_jsonp
def tests():
    tests = database.db_session.query(models.Test).all()
    test_links = map(
        lambda test: {"link": url_for( "test", test_name=test.name)},
        tests)

    return jsonify(tests=test_links,
                   aggregated_test_results= aggregated_test_results())

@app.route('/tests/<test_name>')
@support_jsonp
def test(test_name):
    test = database.db_session.query(models.Test).filter(models.Test.name == test_name).first()
    if test == None:
        abort(404)
    else:
        return jsonify(test.as_dict())

if __name__ == '__main__':
    app.debug = True
    database.init_db()
    app.run()

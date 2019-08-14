
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import datetime
from functools import wraps, update_wrapper
import json
import math
import urllib.request, urllib.error, urllib.parse

from flask import abort, url_for, request, current_app, make_response

from . import app, db
from iatidq import dqpackages
from iatidq.models import Organisation, Package, PackageGroup, Result, Runtime, Test


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


def nocache(f):
    def new_func(*args, **kwargs):
        resp = make_response(f(*args, **kwargs))
        resp.cache_control.no_cache = True
        return resp
    return update_wrapper(new_func, f)


class AggregatedTestResults:
    def make_division(self,i):
        return [i* self.divisions, (i+1) * self.divisions]
    def x_axis(self):
        return list(map(self.make_division, list(range(self.n))))
    def __init__(self, n, data):
        self.n = n
        self.data = data
        self.divisions = 100.0/n
    def aggregate_data(self):
        out = [0] * self.n
        for value in list(self.data.values()):
            if value == 100.0: out[-1] += 1
            else: out[ int(math.floor(value/(100.0/self.n))) ] += 1
        return out
    def create_report(self):
        return {"data" : self.aggregate_data(), "x_axis": self.x_axis()}


def test_percentages(data):
    packages = set([x[2] for x in data])
    d = dict([((x[2],x[1]),x[0]) for x in data])
    out = {}
    for p in packages:
        try: fail = d[(p,0)]
        except: fail = 0
        try: success = d[(p,1)]
        except: success = 0
        out[p] =  (float(success)/(fail+success)) * 100
    return out


def test_tuples(data):
    packages = set([x[2] for x in data])
    d = dict([((x[2],x[1]),x[0]) for x in data])
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
    package_dict = [x.as_dict() for x in packages]
    for package in package_dict:
        try:
            package['passed'] = tests[package['id']][0]
            package['total'] = tests[package['id']][1]
        except KeyError:
            package['passed'] = 0
            package['total'] = 0
    return package_dict


def api_index():
    return jsonify({
        "packages": url_for("api_packages"),
        "tests": url_for("get_tests")
    })


def api_tests():
    session = db.session
    data = session.query(db.func.count(Result.id),
                Result.result_data,
                Result.test_id
            ).group_by(Result.test_id
            ).group_by(Result.result_data).all()
    percentage_passed = test_percentages(data)

    tests = [x.as_dict() for x in session.query(Test).all()]
    for test in tests:
        try:
            test["percentage_passed"] = percentage_passed[test['id']]
        except KeyError:
            test["percentage_passed"] = ""
    return jsonify({"tests": tests})


def api_test(test_id):
    test = db.session.query(Test).filter(Test.id == test_id).first()
    if test == None:
        abort(404)
    else:
        return jsonify(test.as_dict())


def api_packages_active():
    data = []
    for package in Package.query.filter_by(active=True).all():
        data.append((package.package_name, package.active))
    return jsonify(data)


@support_jsonp
def api_packages():
    packages = db.session.query(Package).all()

    session = db.session
    data = session.query(db.func.count(Result.id),
                Result.result_data,
                Result.package_id
            ).group_by(Result.package_id
            ).group_by(Result.result_data).all()

    return jsonify(
                   aggregated_test_results= aggregated_test_results(data), results_by_org=results_by_org(data, packages))


@nocache
def api_package_status(package_id):
    try:
        status = dqpackages.package_status(package_id)
        return jsonify(status.as_dict())
    except Exception:
        return jsonify({"status":"failed"})


@support_jsonp
def api_package(package_name):
    package = db.session.query(Package).filter(Package.package_name == package_name).first()
    if package == None:
        abort(404)
    else:
        return jsonify(package.as_dict())


@support_jsonp
def api_publisher_data(publisher_id):
    url = "http://staging.publishwhatyoufund.org/api/publishers/" + publisher_id

    req = urllib.request.Request(url)
    try:
        response = urllib.request.urlopen(req)
        the_page = response.read()
        rv = app.make_response(the_page)
        rv.mimetype = 'application/json'
        return rv
    except urllib.error.HTTPError as e:
        return jsonify(e)


@support_jsonp
def api_package_activities(package_name, test_id, hierarchy_id=None):
    package = db.session.query(Package).filter(Package.package_name == package_name).first()
    latest_runtime = db.session.query(Runtime
        ).filter(Result.package_id==package.id
        ).join(Result
        ).order_by(Runtime.id.desc()
        ).first()

    if (hierarchy_id):
        if (hierarchy_id=="None"): hierarchy_id=None
        test_results = db.session.query(Result.result_identifier,
                                        Result.result_data
            ).filter(Package.package_name == package_name,
                     Result.runtime_id==latest_runtime.id,
                     Result.test_id==test_id,
                     Result.result_hierarchy==hierarchy_id
            ).join(Package
            ).all()
    else:
        test_results = db.session.query(Result.result_identifier,
                                        Result.result_data
            ).filter(Package.package_name == package_name,
                     Result.runtime_id==latest_runtime.id,
                     Result.test_id==test_id
            ).join(Package
            ).all()
    if ((package == None) or (test_results==None)):
        abort(404)
    else:
        return jsonify(test_results)


@support_jsonp
def api_publisher_activities(packagegroup_name, test_id, hierarchy_id=None):
    if (("offset" in request.args) and (int(request.args['offset'])>=0)):
        offset = int(request.args['offset'])
    else:
        offset = 0
    packagegroup = db.session.query(PackageGroup).filter(PackageGroup.name == packagegroup_name).first()

    if (hierarchy_id):
        if (hierarchy_id=="None"): hierarchy_id=None
        # This is crude because it assumes there is only one result for this
        # test per activity-identifier. But that should be the case anyway.
        test_count = db.session.query(db.func.count(Result.result_identifier)
            ).filter(PackageGroup.name == packagegroup_name,
                     Result.test_id==test_id,
                     Result.result_hierarchy==hierarchy_id
            ).join(Package
            ).join(PackageGroup
            ).all()
        test_results = db.session.query(Result.result_identifier,
                                        Result.result_data,
                                        db.func.max(Result.runtime_id)
            ).filter(PackageGroup.name == packagegroup_name,
                     Result.test_id==test_id,
                     Result.result_hierarchy==hierarchy_id
            ).group_by(Result.result_identifier
            ).group_by(Result.result_data
            ).join(Package
            ).join(PackageGroup
            ).limit(50
            ).offset(offset
            ).all()
    else:
        # This is crude because it assumes there is only one result for this
        # test per activity-identifier. But that should be the case anyway.
        test_count = db.session.query(db.func.count(Result.result_identifier)
            ).filter(PackageGroup.name == packagegroup_name,
                     Result.test_id==test_id
            ).join(Package
            ).join(PackageGroup
            ).all()
        test_results = db.session.query(Result.result_identifier,
                                        Result.result_data,
                                        db.func.count(Result.runtime_id)
            ).filter(PackageGroup.name == packagegroup_name,
                     Result.test_id==test_id
            ).group_by(Result.result_identifier
            ).join(Package
            ).join(PackageGroup
            ).limit(50
            ).offset(offset
            ).all()

    test_results = dict([(x[0],x[1]) for x in test_results])

    if ((packagegroup == None) or (test_results==None)):
        abort(404)
    else:
        return jsonify({"count": test_count, "results": test_results})


@support_jsonp
def api_organisation_activities(organisation_code, test_id, hierarchy_id=None):
    if (("offset" in request.args) and (int(request.args['offset'])>=0)):
        offset = int(request.args['offset'])
    else:
        offset = 0
    organisation = Organisation.query.filter(Organisation.organisation_code==organisation_code
                    ).first()

    if (hierarchy_id):
        if (hierarchy_id=="None"): hierarchy_id=None
        """test_count = db.session.query(db.func.count(Result.result_identifier)
            ).filter(Organisation.organisation_code == organisation_code,
                     Result.test_id==test_id,
                     Result.result_hierarchy==hierarchy_id
            ).join(Package
            ).join(OrganisationPackage
            ).join(Organisation
            ).all()"""
        test_results = db.session.query(Result.result_identifier,
                                        Result.result_data,
                                        db.func.max(Result.runtime_id)
            ).filter(Organisation.organisation_code == organisation_code,
                     Result.test_id==test_id,
                     Result.result_hierarchy==hierarchy_id
            ).group_by(Result.result_identifier
            ).group_by(Result.result_data
            ).join(Package
            ).join(OrganisationPackage
            ).join(Organisation
            ).limit(50
            ).offset(offset
            ).all()
    else:
        """test_count = db.session.query(db.func.count(Result.result_identifier)
            ).filter(Organisation.organisation_code == organisation_code,
                     Result.test_id==test_id
            ).join(Package
            ).join(OrganisationPackage
            ).join(Organisation
            ).all()"""
        test_results = db.session.query(Result.result_identifier,
                                        Result.result_data,
                                        db.func.max(Result.runtime_id)
            ).filter(Organisation.organisation_code == organisation_code,
                     Result.test_id==test_id
            ).group_by(Result.result_identifier
            ).join(Package
            ).join(OrganisationPackage
            ).join(Organisation
            ).limit(50
            ).offset(offset
            ).all()

    test_results = dict([(x[0],x[1]) for x in test_results])

    if ((organisation_code == None) or (test_results==None)):
        abort(404)
    else:
        return jsonify({"results": test_results})

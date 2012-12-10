from flask import Flask, render_template, flash, request, Markup, session, redirect, url_for, escape, Response
from flask.ext.celery import Celery
#from celery.task.sets import TaskSet # Is this going to be used?
import sys, os
from lxml import etree
from flask.ext.sqlalchemy import SQLAlchemy
from flask import render_template
from sqlalchemy import func
from datetime import datetime

app = Flask(__name__)
app.config.from_pyfile('../config.py')
celery = Celery(app)
db = SQLAlchemy(app)

import models
import api
import dqfunctions
import dqprocessing

def DATA_STORAGE_DIR():
    return app.config["DATA_STORAGE_DIR"]

@app.route("/aggregate_results/<runtime>/")
@app.route("/aggregate_results/<runtime>/<commit>/")
def aggregate_results(runtime, commit=False):
    return dqprocessing.aggregate_results(runtime, commit)

def test_activity(runtime_id, package_id, result_identifier, data, test_functions, condition_functions, result_hierarchy):
    xmldata = etree.fromstring(data)

    tests = models.Test.query.filter(models.Test.active == True).all()
    conditions = models.TestCondition.query.filter(models.TestCondition.active == True).all()
    
    for test in tests:
        if not test.id in test_functions:
            continue
        
        if (condition_functions.has_key(test.id)):
            if condition_functions[test.id](xmldata):
                continue

        if test_functions[test.id](xmldata):
            the_result = 1
        else:
            the_result = 0

        newresult = models.Result()
        newresult.runtime_id = runtime_id
        newresult.package_id = package_id
        newresult.test_id = test.id
        newresult.result_data = the_result
        newresult.result_identifier = result_identifier
        newresult.result_hierarchy = result_hierarchy
        db.session.add(newresult)
    return "Success"

def check_file(file_name, runtime_id, package_id, context=None):
    try:
        data = etree.parse(file_name)
    except etree.XMLSyntaxError:
        dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, False)
        return
    dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, True)
    from parsetests import test_functions, condition_functions
    for activity in data.findall('iati-activity'):
        try:
            result_hierarchy = activity.get('hierarchy')
        except KeyError:
            result_hierarchy = None
        result_identifier = activity.find('iati-identifier').text
        activity_data = etree.tostring(activity)
        res = test_activity(runtime_id, package_id, result_identifier, activity_data, test_functions, condition_functions, result_hierarchy)

@celery.task(name="iatidataquality.load_package", track_started=True)
def load_package(runtime):
    output = ""
    
    path = DATA_STORAGE_DIR()
    for package in models.Package.query.order_by(models.Package.id).all():
        print package.id
        output = output + ""
        output = output + "Loading file " + package.package_name + "...<br />"
        
        filename = path + '/' + package.package_name + '.xml'

        # run tests on file
        res = check_file(filename, runtime, package.id, None)

        output = output + 'Finished adding task </a>.<br />'
    db.session.commit()
    aggregate_results(runtime)
    db.session.commit()
    return output


@app.route("/")
def home():
    return redirect(url_for('publishers'))

@app.route("/tests/")
@app.route("/tests/<id>/")
def tests(id=None):
    if (id is not None):
        test = models.Test.query.filter_by(id=id).first()
        return render_template("test.html", test=test)
    else:
        tests = models.Test.query.order_by(models.Test.id).all()
        return render_template("tests.html", tests=tests)

@app.route("/tests/<id>/edit/", methods=['GET', 'POST'])
def tests_editor(id=None):
    if (request.method == 'POST'):
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            test = models.Test.query.filter_by(id=id).first()
            test.name = request.form['name']
            test.description = request.form['description']
            test.test_level = request.form['test_level']
            test.active = request.form['active']
            test.test_group = request.form['test_group']
            db.session.add(test)
            db.session.commit()
            flash('Updated', "success")
            return render_template("test_editor.html", test=test)
        else:
            flash('Incorrect password', "error")
            test = models.Test.query.filter_by(id=id).first()
            return render_template("test_editor.html", test=test)
    else:
        test = models.Test.query.filter_by(id=id).first()
        return render_template("test_editor.html", test=test)

@app.route("/publishers/")
@app.route("/packages/")
def publishers(id=None):
    p_groups = models.PackageGroup.query.order_by(models.PackageGroup.name).all()

    pkgs = models.Package.query.order_by(models.Package.package_name).all()
    return render_template("publishers.html", p_groups=p_groups, pkgs=pkgs)

@app.route("/publishers/<id>/")
def publisher(id=None):
    p_group = models.PackageGroup.query.filter_by(name=id).first()

    pkgs = db.session.query(models.Package
            ).filter(models.Package.package_group == p_group.id
            ).order_by(models.Package.package_name).all()

    latest_runtime = db.session.query(models.Runtime
        ).filter(models.PackageGroup.id==p_group.id
        ).join(models.Result,
               models.Package,
               models.PackageGroup,
        ).order_by(models.Runtime.id.desc()
        ).first()

    aggregate_results = db.session.query(models.Test,
                                         models.AggregateResult.results_data,
                                         models.AggregateResult.results_num,
                                         models.AggregateResult.result_hierarchy,
                                         models.AggregateResult.package_id
            ).filter(models.Package.package_group==p_group.id,
                     models.AggregateResult.runtime_id==latest_runtime.id
            ).group_by(models.AggregateResult.result_hierarchy, models.Test.id, models.AggregateResult.package_id
            ).join(models.AggregateResult,
                   models.Package
            ).all()

    aggregate_results = dqfunctions.agr_publisher_results(aggregate_results)

    return render_template("publisher.html", p_group=p_group, pkgs=pkgs, results=aggregate_results, runtime=latest_runtime)

@app.route("/packages/<id>/")
@app.route("/packages/<id>/runtimes/<runtime_id>/")
def packages(id=None, runtime_id=None):

    # Get package data
    p = db.session.query(models.Package,
        models.PackageGroup
		).filter(models.Package.package_name == id
        ).join(models.PackageGroup).first()

    if (p is None):
        p = db.session.query(models.Package
		).filter(models.Package.package_name == id
        ).first()

    # Get list of runtimes
    runtimes = db.session.query(models.Result.runtime_id,
                                models.Runtime.runtime_datetime
        ).filter(models.Result.package_id ==p[0].id
        ).distinct(
        ).join(models.Runtime
        ).all()

    if (runtime_id):
        # If a runtime is specified in the request, get the data

        latest_runtime = db.session.query(models.Runtime
            ).filter(models.Runtime.id==runtime_id
            ).first()
        latest = False
    else:
        # Select the highest runtime; then get data for that one

        latest_runtime = db.session.query(models.Runtime
            ).filter(models.Result.package_id==p[0].id
            ).join(models.Result
            ).order_by(models.Runtime.id.desc()
            ).first()
        latest = True

    aggregate_results = db.session.query(models.Test,
                                         models.AggregateResult.results_data,
                                         models.AggregateResult.results_num,
                                         models.AggregateResult.result_hierarchy
            ).filter(models.AggregateResult.package_id==p[0].id,
                     models.AggregateResult.runtime_id==latest_runtime.id
            ).group_by(models.AggregateResult.result_hierarchy, models.Test
            ).join(models.AggregateResult
            ).all()

    aggregate_results = dqfunctions.agr_results(aggregate_results)
 
    return render_template("package.html", p=p, runtimes=runtimes, results=aggregate_results, latest_runtime=latest_runtime, latest=latest)

@app.route("/runtests/new/")
def run_new_tests():
    newrun = models.Runtime()
    db.session.add(newrun)
    db.session.commit()
    res = load_package.delay(newrun.id)
    
    flash('Running tests; this may take some time. Runtime ID is ' + str(newrun.id), "success")
    return render_template("runtests.html", task=res,runtime=newrun)

@app.route("/runtests/")
@app.route("/runtests/<id>/")
def check_tests(id=None):
    if (id):
        task = load_package.AsyncResult(id)
        return render_template("checktest.html", task=task)
    else: 
        i = celery.control.inspect()
        active_tasks = i.active()
        registered_tasks = i.reserved()
        return render_template("checktests.html", active_tasks=active_tasks, registered_tasks=registered_tasks)

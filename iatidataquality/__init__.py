from flask import Flask, render_template, flash, request, Markup, session, redirect, url_for, escape, Response
from flask.ext.celery import Celery
#from celery.task.sets import TaskSet # Is this going to be used?
import sys, os
from lxml import etree
from flask.ext.sqlalchemy import SQLAlchemy
from flask import render_template
from sqlalchemy import func

app = Flask(__name__)
app.config.from_pyfile('../config.py')
celery = Celery(app)
db = SQLAlchemy(app)
def add_hardcoded_result(test_id, runtime_id, package_id, result_data):
    result = models.Result()
    result.test_id = test_id 
    result.runtime_id = runtime_id
    result.result_level = u'file'
    result.package_id = package_id
    if result_data:
        result.result_data = 1
    else:
        result.result_data = 0 
    db.session.add(result)
import models
import api

from parsetests import test_functions

# Has the test completed?
@app.route("/resultcheck/<task_id>")
def check_result(task_id):
    retval = load_file.AsyncResult(task_id).status
    return retval


# run XPATH tests, stored in the database against each activity
#@celery.task(name="myapp.test_activity", callback=None)
def test_activity(runtime_id, package_id, result_level, result_identifier, data):
    xmldata = etree.fromstring(data)
    result_level = '1' # activity

    tests = models.Test.query.all()
    for test in tests:
        if not test.line:
            continue
        if not test.line in test_functions:
            continue

        if test_functions[test.line](xmldata):
            the_result = 1
        else:
            the_result = 0

        newresult = models.Result()
        newresult.runtime_id = runtime_id
        newresult.package_id = package_id
        newresult.test_id = test.id
        newresult.result_data = the_result
        newresult.result_level = result_level
        newresult.result_identifier = result_identifier
        db.session.add(newresult)
    db.session.commit()

def check_file(file_name, runtime_id, package_id, context=None):
    result_level = '1' # ACTIVITY
    try:
        data = etree.parse(file_name)
    except etree.XMLSyntaxError:
        add_hardcoded_result(-3, runtime_id, package_id, False)
        return
    add_hardcoded_result(-3, runtime_id, package_id, True)
    for activity in data.findall('iati-activity'):
        result_identifier = activity.find('iati-identifier').text
        activity_data = etree.tostring(activity)
        res = test_activity(runtime_id, package_id, result_level, result_identifier, activity_data)

def load_package(runtime):
    output = ""
    
    path = 'data/'
    for package in models.Package.query.order_by(models.Package.id).all():
        print package.id
        output = output + ""
        output = output + "Loading file " + package.package_name + "...<br />"
        
        filename = path + '/' + package.package_name + '.xml'

        # run tests on file
        res = check_file(filename, runtime, package.id, None)
        # res.task_id is the id of the task
        output = output + 'Finished processing.<br />'
    return output

@app.route("/")
def home():
    return redirect("/test_summaries")

@app.route("/test_summaries")
def test_summaries():
    return render_template("test_summaries.html")

@app.route("/organisation_quality")
def organisation_quality():
    return render_template("organisation_quality.html")

@app.route("/table/")
def table_select():
    rows = db.session.query(func.count(models.Result.result_data), 
		models.Runtime, 
		models.Result.result_data
		).group_by(models.Result.result_data
		).group_by(models.Runtime
		).join(models.Runtime
		).order_by(models.Runtime.id).all() 
        
    runtimes = set(map(lambda x: x[1].id, rows))
    data = []
    for runtime in runtimes:
        datadata = {}
        datadata['runtime_id'] = runtime
        for row in rows:
            # it's the same runtime
            if (row[1].id == runtime):
                datadata[row[2]] = row[0]
                datadata['runtime_datetime'] = row[1].runtime_datetime
        if (datadata.has_key(0) and datadata.has_key(1)):
            datadata['total_tests'] = datadata[0] + datadata[1]
            datadata['percent_passed'] = round(float(datadata[0])/float(datadata['total_tests'])*100, 2)
        elif (datadata.has_key(0)):
            datadata['percent_passed'] = float(0)
            datadata['total_tests'] = datadata[0]
        elif (datadata.has_key(1)):
            datadata['percent_passed'] = float(1)*100
            datadata['total_tests'] = datadata[1]
        data.append(datadata)
    print data

    return render_template("table_select.html", rows=rows, data=data, runtimes=runtimes) 

@app.route("/table/<int:runtime_id>")
def table(runtime_id):
    results = db.session.query(models.Result.package_id, models.Result.test_id, func.sum(models.Result.result_data), func.count(models.Result.id)
                ).filter_by(runtime_id=runtime_id
                ).group_by(models.Result.package_id, models.Result.test_id, models.Result.runtime_id
                ).order_by(models.Result.package_id, models.Result.test_id).all()
    tests = models.Test.query.order_by(models.Test.id).all()
    packages = models.Package.query.order_by(models.Package.id).all()
    package_ids = map(lambda x: x.id, packages)
    test_ids = map(lambda x: x.id, tests)
    def result_generator():
        pos = 0
        for package in packages: 
            def row_generator():
                yield package.package_name
                for tid in test_ids:
                    if results:
                        if results[0][0] == package.id and results[0][1] == tid:
                            yield (results[0][2], results[0][3])
                            results.pop(0)
                        else:
                            yield "/"
                    else:
                        yield "/"
            yield row_generator()
    return render_template("table.html", results=result_generator(), tests=tests)

@app.route("/runtests/")
def runtests():
    newrun = models.Runtime()
    db.session.add(newrun)
    db.session.commit()

    output = ""
    output = load_package(newrun.id)
    output = str(output) + "<br />Runtime is <br />" + str(newrun.id)
    return str(output)


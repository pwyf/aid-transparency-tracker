from flask import Flask, render_template, flash, request, Markup, session, redirect, url_for, escape, Response
from flask.ext.celery import Celery
from celery.task.sets import TaskSet
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UnicodeText, Date, DateTime, Float, Boolean, func
from iati_dq import activity_tests as IATIActivityTests
from iati_dq import file_tests as IATIFileTests
import models
import sys, os
from lxml import etree
import database

def create_app():
    return Flask("myapp")

app = create_app()
app.config.from_pyfile('config.py')
celery = Celery(app)

# Has the test completed?
@app.route("/resultcheck/<task_id>")
def check_result(task_id):
    retval = load_file.AsyncResult(task_id).status
    return retval

def run_a_test(thedata,thexpath):
    test_result = False
    try:
        test_result = thedata.xpath(thexpath)
    except Exception, e:
        pass

    if (test_result):
        return True
    else:
        return False

# run XPATH tests, stored in the database against each activity
@celery.task(name="myapp.test_activity", callback=None)
def test_activity(runtime_id, package_id, result_level, result_identifier, data):

    xmldata = etree.fromstring(data)
    result_level = '1' # activity

    tests = models.Test.query.all()
    for test in tests:
        if (test.xpath == 1):
        # if it's XPATH, run tests using that
            the_result = run_a_test(xmldata, test.code)
            newresult = models.Result()
            newresult.runtime_id = runtime_id
            newresult.package_id = package_id
            newresult.test_id=test_id
            newresult.result_data = the_result
            newresult.result_level = result_level
            newresult.result_identifier = result_identifier
            database.db_session.add(newresult)
            database.db_session.add(newresult)
    # test that it's working, just add some random data...
    examplecode = """//title/text()"""
    the_result = run_a_test(xmldata, examplecode)
    test_id = '-100'
    newresult = models.Result()
    newresult.runtime_id = runtime_id
    newresult.package_id = package_id
    newresult.test_id=test_id
    newresult.result_data = the_result
    newresult.result_level = result_level
    newresult.result_identifier = result_identifier
    database.db_session.add(newresult)
    database.db_session.commit()

def check_file(file_name, runtime_id, package_id, context=None):
    result_identifier = 'FAKE_ACTIVITY_ID' # FAKE
    result_level = '1' # ACTIVITY
    data = etree.parse(file_name)
    for activity in data.findall('iati-activity'):
        activity_data = etree.tostring(data)
        res = test_activity.apply_async((runtime_id, package_id, result_level, result_identifier, activity_data))
        # remove this line when it's working
        break

def load_package(runtime):
    output = ""
    
    path = 'data/'
    for package in models.Package.query.all():
        try:            
            output = output + ""
            output = output + "Loading file"
            
            filename = path + '/' + package.package_name + '.xml'

	        # run tests on file
            res = check_file(filename, runtime, package.id, None)
            # res.task_id is the id of the task
            output = output + 'Ran that'
        except Exception, e:
            output = output + "Error in file: " + package.package_name + " - " + str(e) + "\n"
	    pass
    return output

@app.route("/runtests/")
def runtests():

    newrun = models.Runtime()
    database.db_session.add(newrun)
    database.db_session.commit()

    output = ""
    output = load_package(newrun.id)
    output = str(output) + "<br />Runtime is <br />" + str(newrun.id)
    return str(output)

if __name__ == "__main__":
    database.init_db()
    app.run(debug=True)

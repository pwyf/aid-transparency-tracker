from flask import Flask, render_template, flash, request, Markup, session, redirect, url_for, escape, Response
from flask.ext.celery import Celery
from celery.task.sets import TaskSet
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, UnicodeText, Date, DateTime, Float, Boolean, func
import models
import sys, os
from lxml import etree
import database

from flask.ext.script import Manager
from flask.ext.celery import install_commands as install_celery_commands

app = database.create_app()
celery = Celery(app)

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
        module = __import__('tests.'+test.file)
        submodule = getattr(module, test.file)
        #try:
        the_result = getattr(submodule, test.name)(xmldata)
        #except Exception:
        #    the_result = False

        newresult = models.Result()
        newresult.runtime_id = runtime_id
        newresult.package_id = package_id
        newresult.test_id = test.id
        newresult.result_data = the_result
        newresult.result_level = result_level
        newresult.result_identifier = result_identifier
        database.db_session.add(newresult)
    database.db_session.commit()

def check_file(file_name, runtime_id, package_id, context=None):
    result_level = '1' # ACTIVITY
    data = etree.parse(file_name)
    for activity in data.findall('iati-activity'):
        result_identifier = activity.find('iati-identifier').text
        activity_data = etree.tostring(activity)
        res = test_activity(runtime_id, package_id, result_level, result_identifier, activity_data)
        # remove this line when it's working

def load_package(runtime):
    output = ""
    
    path = 'data/'
    for package in models.Package.query.all():
        output = output + ""
        output = output + "Loading file"
        
        filename = path + '/' + package.package_name + '.xml'

        # run tests on file
        res = check_file(filename, runtime, package.id, None)
        # res.task_id is the id of the task
        output = output + 'Ran that'
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

    manager = Manager(app)
    install_celery_commands(manager)

    if __name__ == "__main__":
        manager.run()

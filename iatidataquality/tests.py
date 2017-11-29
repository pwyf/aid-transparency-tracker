
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import render_template, flash, request, redirect, url_for
from flask_login import login_required, current_user

from . import app, usermanagement
from iatidq import dqimporttests, dqtests, test_level


test_list_location = "tests/tests.yaml"

@app.route("/tests/")
@app.route("/tests/<id>/")
def tests(id=None):
    if (id is not None):
        test = dqtests.tests(id)
        return render_template("test.html", test=test,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)
    else:
        tests = dqtests.tests()
        return render_template("tests.html", tests=tests,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

@app.route("/tests/<id>/edit/", methods=['GET', 'POST'])
@usermanagement.perms_required('tests', 'edit', '<id>')
def tests_editor(id=None):
    if (request.method == 'POST'):
        test = dqtests.tests(id)
        data = {
                "id": id,
                "name": request.form['name'],
                "description": request.form['description'],
                "test_level": request.form['test_level'],
                "active": request.form.get('active', None)
            }
        if dqtests.updateTest(data):
            flash('Updated', "success")
        else:
            flash("Couldn't update", "error")
    else:
        test = dqtests.tests(id)
    return render_template("test_editor.html", test=test,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

@app.route("/tests/<id>/delete/")
@usermanagement.perms_required('tests', 'delete', '<id>')
def tests_delete(id=None):
    if id is not None:
        if dqtests.deleteTest(id):
            flash('Successfully deleted test.', 'success')
        else:
            flash("Couldn't delete test. Maybe results already exist connected with that test?", 'error')
        return redirect(url_for('tests', id=id))
    else:
        flash('No test ID provided', 'error')
        return redirect(url_for('tests'))

@app.route("/tests/new/", methods=['GET', 'POST'])
@usermanagement.perms_required('tests', 'new')
@login_required
def tests_new():
    if (request.method == 'POST'):
        data = {
                "name": request.form['name'],
                "description": request.form['description'],
                "test_level": request.form['test_level'],
                "active": request.form.get('active', None)
            }
        try:
            test = dqtests.addTest(data)
            flash('Created', "success")
        except dqtests.TestNotFound:
            test = data
            flash('Unable to create. Maybe you already have a test using the same expression?', "error")
    else:
        test = {}
    return render_template("test_editor.html", test=test,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)


@app.route("/tests/import/", methods=['GET', 'POST'])
def import_tests():
    if (request.method == 'POST'):
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            if (request.form.get('local')):
                result = dqimporttests.importTestsFromFile(test_list_location,
                                                           test_level.ACTIVITY)
            else:
                url = request.form['url']
                level = int(request.form['level'])
                result = dqimporttests.importTestsFromUrl(url, level=level)
            if (result==True):
                flash('Imported tests', "success")
            else:
                flash('There was an error importing your tests', "error")
        else:
            flash('Wrong password', "error")
    return render_template("import_tests.html",
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

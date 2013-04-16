
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file
import StringIO
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
from sqlalchemy import func
from datetime import datetime

from iatidataquality import app
from iatidataquality import db

import os
import sys
import json

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from iatidq import models, dqdownload, dqregistry, dqindicators, dqorganisations, dqpackages
import aggregation

import StringIO
import unicodecsv
import tempfile
import spreadsheet

test_list_location = "tests/activity_tests.csv"

@app.route("/tests/")
@app.route("/tests/<id>/")
def tests(id=None):
    if (id is not None):
        test = models.Test.query.filter_by(id=id).first_or_404()
        return render_template("test.html", test=test)
    else:
        tests = models.Test.query.order_by(models.Test.id).all()
        return render_template("tests.html", tests=tests)

@app.route("/tests/<id>/edit/", methods=['GET', 'POST'])
def tests_editor(id=None):
    if (request.method == 'POST'):
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            test = models.Test.query.filter_by(id=id).first_or_404()
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
            test = models.Test.query.filter_by(id=id).first_or_404()
            return render_template("test_editor.html", test=test)
    else:
        test = models.Test.query.filter_by(id=id).first_or_404()
        return render_template("test_editor.html", test=test)


@app.route("/tests/new/", methods=['GET', 'POST'])
@login_required
def tests_new(id=None):
    if (request.method == 'POST'):
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            test = models.Test()
            test.setup(
                name = request.form['name'],
                description = request.form['description'],
                test_group = request.form['test_group'],
                test_level = request.form['test_level'],
                active = request.form['active']
                )
            db.session.add(test)
            db.session.commit()
            flash('Updated', "success")
            return render_template("test_editor.html", test=test)
        else:
            flash('Incorrect password', "error")
            return render_template("test_editor.html", test={})
    else:
        return render_template("test_editor.html", test={})

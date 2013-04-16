
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

@app.route("/indicators/")
def indicatorgroups():
    indicatorgroups = dqindicators.indicatorGroups()
    return render_template("indicatorgroups.html", indicatorgroups=indicatorgroups)

@app.route("/indicators/import/")
def indicators_import():
    if dqindicators.importIndicators():
        flash('Successfully imported your indicators', 'success')
    else:
        flash('Could not import your indicators', 'error')
    return redirect(url_for('indicatorgroups'))
    

@app.route("/indicators/<indicatorgroup>/edit/", methods=['GET', 'POST'])
def indicatorgroups_edit(indicatorgroup=None):
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description']
        }
        indicatorgroup = dqindicators.updateIndicatorGroup(indicatorgroup, data)
        flash('Successfully updated IndicatorGroup', 'success')
    else:
        indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)
    return render_template("indicatorgroups_edit.html", indicatorgroup=indicatorgroup)

@app.route("/indicators/<indicatorgroup>/delete/")
def indicatorgroups_delete(indicatorgroup=None):
    indicatorgroup = dqindicators.deleteIndicatorGroup(indicatorgroup)
    flash('Successfully deleted IndicatorGroup', 'success')
    return redirect(url_for('indicatorgroups'))

@app.route("/indicators/new/", methods=['GET', 'POST'])
def indicatorgroups_new():
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description']
        }
        indicatorgroup = dqindicators.addIndicatorGroup(data)
        if indicatorgroup:
            flash('Successfully added IndicatorGroup.', 'success')
        else:
            flash("Couldn't add IndicatorGroup. Maybe one already exists with the same name?", 'error')
    else:
        indicatorgroup = None
    return render_template("indicatorgroups_edit.html", indicatorgroup=indicatorgroup)

@app.route("/indicators/<indicatorgroup>/")
def indicators(indicatorgroup=None):
    indicators = dqindicators.indicators(indicatorgroup)
    indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)
    return render_template("indicators.html", indicatorgroup=indicatorgroup, indicators=indicators)

@app.route("/indicators/<indicatorgroup>_tests.csv")
@app.route("/indicators/<indicatorgroup>_<option>tests.csv")
def indicatorgroup_tests_csv(indicatorgroup=None, option=None):
    strIO = StringIO.StringIO()
    if (option != "no"):
        fieldnames = "indicator_name indicator_description test_name test_description".split()
    else:
        fieldnames = "test_name test_description".split()
    out = unicodecsv.DictWriter(strIO, fieldnames=fieldnames)
    headers = {}
    for fieldname in fieldnames:
        headers[fieldname] = fieldname
    out.writerow(headers)
    data = dqindicators.indicatorGroupTests(indicatorgroup, option)

    for d in data:
        if (option !="no"):
            out.writerow({"test_name": d[2], 
                          "test_description": d[3], 
                          "level": d[4],
                          "indicator_name": d[0], 
                          "indicator_description": d[1], })
        else:
            out.writerow({"test_name": d[0], 
                          "test_description": d[1], 
                          "level": d[2]})            
    strIO.seek(0)
    if option ==None:
        option = ""
    return send_file(strIO,
                     attachment_filename=indicatorgroup + "_" + option + "tests.csv",
                     as_attachment=True)

@app.route("/indicators/<indicatorgroup>/new/", methods=['GET', 'POST'])
def indicators_new(indicatorgroup=None):
    indicatorgroups = dqindicators.indicatorGroups()
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'indicatorgroup_id': request.form['indicatorgroup_id']
        }
        indicator = dqindicators.addIndicator(data)
        if indicator:
            flash('Successfully added Indicator.', 'success')
        else:
            flash("Couldn't add Indicator. Maybe one already exists with the same name?", 'error')
    else:
        indicator = None
    return render_template("indicator_edit.html", indicatorgroups=indicatorgroups, indicator=indicator)

@app.route("/indicators/<indicatorgroup>/<indicator>/edit/", methods=['GET', 'POST'])
def indicators_edit(indicatorgroup=None, indicator=None):
    indicatorgroups = dqindicators.indicatorGroups()
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'indicatorgroup_id': request.form['indicatorgroup_id']
        }
        indicator = dqindicators.updateIndicator(indicatorgroup, indicator, data)
        flash('Successfully updated Indicator', 'success')
    else:
        indicator = dqindicators.indicators(indicatorgroup, indicator)
    return render_template("indicator_edit.html", indicatorgroups=indicatorgroups, indicator=indicator)

@app.route("/indicators/<indicatorgroup>/<indicator>/delete/")
def indicators_delete(indicatorgroup=None, indicator=None):
    indicator = dqindicators.deleteIndicator(indicatorgroup, indicator)
    flash('Successfully deleted Indicator', 'success')
    return redirect(url_for('indicators', indicatorgroup=indicatorgroup))

@app.route("/indicators/<indicatorgroup>/<indicator>/", methods=['GET', 'POST'])
def indicatortests(indicatorgroup=None, indicator=None):
    alltests = dqindicators.allTests()
    indicator = dqindicators.indicators(indicatorgroup, indicator)
    indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)
    if (request.method == 'POST'):
        for test in request.form.getlist('test'):
            data = {
                    'indicator_id': indicator.id,
                    'test_id': test
            }
            if dqindicators.addIndicatorTest(data):
                flash('Successfully added test to your indicator.', 'success')
            else:
                flash("Couldn't add test to your indicator.", 'error')
    indicatortests = dqindicators.indicatorTests(indicatorgroup.name, indicator.name)
    return render_template("indicatortests.html", indicatorgroup=indicatorgroup, indicator=indicator, indicatortests=indicatortests, alltests=alltests)

@app.route("/indicators/<indicatorgroup>/<indicator>/<indicatortest>/delete/")
def indicatortests_delete(indicatorgroup=None, indicator=None, indicatortest=None):
    if dqindicators.deleteIndicatorTest(indicatortest):
        flash('Successfully removed test from indicator ' + indicator + '.', 'success')
    else:
        flash('Could not remove test from indicator ' + indicator + '.', 'error')        
    return redirect(url_for('indicatortests', indicatorgroup=indicatorgroup, indicator=indicator))

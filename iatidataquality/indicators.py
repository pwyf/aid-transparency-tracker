
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
from flask.ext.login import login_required, current_user
from sqlalchemy import func
from datetime import datetime

from iatidataquality import app
from iatidataquality import db
from iatidq import dqusers, util
import usermanagement

import os
import sys
import json

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from iatidq import dqdownload, dqregistry, dqindicators, dqorganisations, dqpackages

import StringIO
import unicodecsv
import tempfile
import spreadsheet


@app.route("/indicators/")
def indicatorgroups():
    if not usermanagement.check_perms('admin'):
        return redirect(url_for('indicators', indicatorgroup=app.config["INDICATOR_GROUP"]))
    indicatorgroups = dqindicators.indicatorGroups()
    return render_template("indicatorgroups.html", indicatorgroups=indicatorgroups,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)

@app.route("/indicators/import/")
@usermanagement.perms_required()
def indicators_import():
    if dqindicators.importIndicators():
        flash('Successfully imported your indicators', 'success')
    else:
        flash('Could not import your indicators', 'error')
    return redirect(url_for('indicatorgroups'))
    
@app.route("/indicators/<indicatorgroup>/edit/", methods=['GET', 'POST'])
@usermanagement.perms_required()
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
    return render_template("indicatorgroups_edit.html", indicatorgroup=indicatorgroup,
                 admin=usermanagement.check_perms('admin'),
                 loggedinuser=current_user)

@app.route("/indicators/<indicatorgroup>/delete/")
@usermanagement.perms_required()
def indicatorgroups_delete(indicatorgroup=None):
    indicatorgroup = dqindicators.deleteIndicatorGroup(indicatorgroup)
    flash('Successfully deleted IndicatorGroup', 'success')
    return redirect(url_for('indicatorgroups'))

@app.route("/indicators/new/", methods=['GET', 'POST'])
@usermanagement.perms_required()
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
    return render_template("indicatorgroups_edit.html", 
                         indicatorgroup=indicatorgroup,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)


@app.route("/indicators/<indicatorgroup>/comparison/<indicator>")
def indicators_comparison(indicatorgroup, indicator):

    indicator = dqindicators.getIndicatorByName(indicator)
    organisations = dqorganisations.organisations()

    return render_template("indicator_comparison.html",
                           loggedinuser=current_user,
                           indicator=indicator,
                           organisations=organisations)


@app.route("/indicators/<indicatorgroup>/")
def indicators(indicatorgroup=None):
    its = {}
    indicators = dqindicators.indicatorsTests(indicatorgroup)
    for indicator in indicators:
        if indicator.Indicator.id not in its:
            its[indicator.Indicator.id] = {}
        its[indicator.Indicator.id].update(indicator.Indicator.as_dict())
        if indicator.Test:
            if ('tests' not in its[indicator.Indicator.id]):
                its[indicator.Indicator.id]['tests'] = []
            its[indicator.Indicator.id]['tests'].append(indicator.Test.as_dict())

    its = util.resort_indicator_tests(its)
    indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)
    return render_template("indicators.html", 
                        indicatorgroup=indicatorgroup, 
                        indicators=its,
                        admin=usermanagement.check_perms('admin'),
                        loggedinuser=current_user)

@app.route("/indicators/<indicatorgroup>_tests.csv")
@app.route("/indicators/<indicatorgroup>_<option>tests.csv")
def indicatorgroup_tests_csv(indicatorgroup=None, option=None):
    strIO = StringIO.StringIO()
    if (option != "no"):
        fieldnames = "test_name test_description test_level indicator_name indicator_description".split()
    else:
        fieldnames = "test_name test_description test_level".split()
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
                          "test_level": d[4],
                          "indicator_name": d[0], 
                          "indicator_description": d[1], })
        else:
            out.writerow({"test_name": d[0], 
                          "test_description": d[1], 
                          "test_level": d[2]})            
    strIO.seek(0)
    if option ==None:
        option = ""
    return send_file(strIO,
                     attachment_filename=indicatorgroup + "_" + option + "tests.csv",
                     as_attachment=True)

@app.route("/indicators/<indicatorgroup>/new/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def indicators_new(indicatorgroup=None):
    indicatorgroups = dqindicators.indicatorGroups()
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'indicatorgroup_id': request.form['indicatorgroup_id'],
            'longdescription': request.form.get("longdescription"),
            'indicator_type': request.form.get("indicator_type"),
            'indicator_category_name': request.form.get("indicator_category_name"),
            'indicator_subcategory_name': request.form.get("indicator_subcategory_name"),
            'indicator_ordinal': request.form.get("indicator_ordinal", None),
            'indicator_noformat': request.form.get("indicator_noformat", None),
            'indicator_order': request.form.get("indicator_order", None),
            'indicator_weight': request.form.get("indicator_weight", None)
        }
        indicator = dqindicators.addIndicator(data)
        if indicator:
            flash('Successfully added Indicator.', 'success')
        else:
            flash("Couldn't add Indicator. Maybe one already exists with the same name?", 'error')
    else:
        indicator = None
    return render_template("indicator_edit.html", 
                         indicatorgroups=indicatorgroups, 
                         indicator=indicator,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)

@app.route("/indicators/<indicatorgroup>/<indicator>/edit/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def indicators_edit(indicatorgroup=None, indicator=None):
    indicatorgroups = dqindicators.indicatorGroups()
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'indicatorgroup_id': request.form['indicatorgroup_id'],
            'longdescription': request.form['longdescription'],
            'indicator_type': request.form.get("indicator_type"),
            'indicator_category_name': request.form.get("indicator_category_name"),
            'indicator_subcategory_name': request.form.get("indicator_subcategory_name"),
            'indicator_ordinal': request.form.get("indicator_ordinal", None),
            'indicator_noformat': request.form.get("indicator_noformat", None),
            'indicator_order': request.form.get("indicator_order", None),
            'indicator_weight': request.form.get("indicator_weight", None)
        }
        indicator = dqindicators.updateIndicator(indicatorgroup, indicator, data)
        flash('Successfully updated Indicator', 'success')
    else:
        indicator = dqindicators.indicators(indicatorgroup, indicator)
    return render_template("indicator_edit.html", 
                         indicatorgroups=indicatorgroups, 
                         indicator=indicator,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)

@app.route("/indicators/<indicatorgroup>/<indicator>/delete/")
@usermanagement.perms_required()
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
    return render_template("indicatortests.html", 
                         indicatorgroup=indicatorgroup, 
                         indicator=indicator, 
                         indicatortests=indicatortests, 
                         alltests=alltests,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)

@app.route("/indicators/<indicatorgroup>/<indicator>/<indicatortest>/delete/")
@usermanagement.perms_required()
def indicatortests_delete(indicatorgroup=None, indicator=None, indicatortest=None):
    if dqindicators.deleteIndicatorTest(indicatortest):
        flash('Successfully removed test from indicator ' + indicator + '.', 'success')
    else:
        flash('Could not remove test from indicator ' + indicator + '.', 'error')        
    return redirect(url_for('indicatortests', indicatorgroup=indicatorgroup, indicator=indicator))

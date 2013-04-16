
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


class User(UserMixin):
    def __init__(self, name, id, active=True):
        self.name = name
        self.id = id
        self.active = active

    def is_active(self):
        return self.active

class Anonymous(AnonymousUser):
    name = u"Anonymous"


USERS = {
    1: User(u"admin", 1),
    3: User(u"notadmin", 3, False),
}

USER_NAMES = dict((u.name, u) for u in USERS.itervalues())

login_manager = LoginManager()

login_manager.anonymous_user = Anonymous
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"

@login_manager.user_loader
def load_user(id):
    return USERS.get(int(id))


login_manager.setup_app(app)

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        if username in USER_NAMES:
            remember = request.form.get("remember", "no") == "yes"
            if login_user(USER_NAMES[username], remember=remember):
                flash("Logged in!")
                return redirect(request.args.get("next") or url_for("index"))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username.")
    return render_template("login.html")



@app.route("/orgview/<organisation_code>/")
def orgview(organisation_code=None):
    p_group = models.Organisation.query.filter_by(organisation_code=organisation_code).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Organisation.organisation_code == organisation_code
            ).join(models.OrganisationPackage
            ).join(models.Organisation
            ).order_by(models.Package.package_name
            ).all()

    aggregate_results = _organisation_indicators(p_group);

    latest_runtime=1

    return render_template("organisation_indicators.html", p_group=p_group, pkgs=pkgs, 
                           results=aggregate_results, runtime=latest_runtime)


@app.route("/tests/import/", methods=['GET', 'POST'])
def import_tests():
    if (request.method == 'POST'):
        import dqimporttests
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            if (request.form.get('local')):
                result = dqimporttests.importTestsFromFile(test_list_location)
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
        return render_template("import_tests.html")
    else:
        return render_template("import_tests.html")


@app.route("/aggregate_results/<package_id>/<runtime>")
def display_aggregate_results(package_id, runtime):
    dqprocessing.aggregate_results(runtime, package_id)
    db.session.commit()
    return "ok"

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
    indicatortests = dqindicators.indicatorTests(indicator.name)
    return render_template("indicatortests.html", indicatorgroup=indicatorgroup, indicator=indicator, indicatortests=indicatortests, alltests=alltests)

@app.route("/indicators/<indicatorgroup>/<indicator>/<indicatortest>/delete/")
def indicatortests_delete(indicatorgroup=None, indicator=None, indicatortest=None):
    if dqindicators.deleteIndicatorTest(indicatortest):
        flash('Successfully removed test from indicator ' + indicator + '.', 'success')
    else:
        flash('Could not remove test from indicator ' + indicator + '.', 'error')        
    return redirect(url_for('indicatortests', indicatorgroup=indicatorgroup, indicator=indicator))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


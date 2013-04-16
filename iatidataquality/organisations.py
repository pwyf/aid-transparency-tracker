
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


@app.route("/organisations/")
@app.route("/organisations/<organisation_code>/")
def organisations(organisation_code=None):
    template_args = {}
    if organisation_code is not None:
        organisation = dqorganisations.organisations(organisation_code)

        try:
            summary_data = _organisation_indicators_summary(organisation)
        except Exception, e:
            summary_data = None

        template_args = dict(organisation=organisation, 
                             summary_data=summary_data)
    else:
        organisations = dqorganisations.organisations()

        template_args = dict(organisations=organisations)

    return render_template("organisations.html", **template_args)

@app.route("/organisations/new/", methods=['GET','POST'])
def organisation_new():
    organisation = None
    if request.method == 'POST':
        data = {
            'organisation_code': request.form['organisation_code'],
            'organisation_name': request.form['organisation_name']
        }
        organisation = dqorganisations.addOrganisation(data)
        if organisation:
            flash('Successfully added organisation', 'success')
            return redirect(url_for(
                    'organisation_edit', 
                    organisation_code=organisation.organisation_code))
        else:
            flash("Couldn't add organisation", "error")
            organisation = data
    return render_template("organisation_edit.html", organisation=organisation)


@app.route("/organisations/<organisation_code>/publication/")
def organisation_publication(organisation_code=None):
    p_group = models.Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Organisation.organisation_code == organisation_code
            ).join(models.OrganisationPackage
            ).join(models.Organisation
            ).order_by(models.Package.package_name
            ).all()

    aggregate_results = _organisation_indicators(p_group);

    latest_runtime=1

    return render_template("organisation_indicators.html", 
                           p_group=p_group, pkgs=pkgs, 
                           results=aggregate_results, runtime=latest_runtime)

@app.route("/organisations/<organisation_code>/edit/", methods=['GET','POST'])
def organisation_edit(organisation_code=None):
    def add_org_pkg(organisation, package):
        data = {
            'organisation_id': organisation.id,
            'package_id': package
            }
        if dqorganisations.addOrganisationPackage(data):
            flash('Successfully added package to your organisation.', 
                  'success')
        else:
            flash("Couldn't add package to your organisation.", 
                  'error')

    packages = dqpackages.packages()
    if request.method == 'POST':
        if 'addpackages' in request.form:
            organisation = dqorganisations.organisations(organisation_code)
            [ add_org_pkg(organisation, package) for package in request.form.getlist('package') ]
                
        elif 'updateorganisation' in request.form:
            data = {
                'organisation_code': request.form['organisation_code'],
                'organisation_name': request.form['organisation_name']
            }
            organisation = dqorganisations.updateOrganisation(
                organisation_code, data)
    else:
        organisation = dqorganisations.organisations(organisation_code)

    organisationpackages = dqorganisations.organisationPackages(
        organisation.organisation_code)

    return render_template(
        "organisation_edit.html", 
        organisation=organisation, 
        packages=packages, 
        organisationpackages=organisationpackages)

@app.route("/organisations/<organisation_code>/<package_name>/<organisationpackage_id>/delete/")
def organisationpackage_delete(organisation_code=None, package_name=None, organisationpackage_id=None):
    if dqorganisation.deleteOrganisationPackage(organisation_code, package_name, organisationpackage_id):
        flash('Successfully removed package ' + package_name + ' from organisation ' + organisation_code + '.', 'success')
    else:
        flash('Could not remove package ' + package_name + ' from organisation ' + organisation_code + '.', 'error')        
    return redirect(url_for('organisation_edit', organisation_code=organisation_code))

def _organisation_indicators_summary(organisation):
    summarydata = _organisation_indicators(organisation)
    # Create crude total score
    totalpct = 0.00
    totalindicators = 0
    for indicator, indicatordata in summarydata.items():
        totalpct += indicatordata['results_pct']
        totalindicators +=1
    totalscore = totalpct/totalindicators
    return totalscore, totalindicators
    

def _organisation_indicators(organisation):
    aggregate_results = db.session.query(models.Indicator,
                                     models.Test,
                                     models.AggregateResult.results_data,
                                     models.AggregateResult.results_num,
                                     models.AggregateResult.result_hierarchy,
                                     models.AggregateResult.package_id,
                                     func.max(models.AggregateResult.runtime_id)
        ).filter(models.Organisation.organisation_code==organisation.organisation_code
        ).group_by(models.AggregateResult.result_hierarchy, 
                   models.Test, 
                   models.AggregateResult.package_id,
                   models.Indicator,
                   models.AggregateResult.results_data,
                   models.AggregateResult.results_num,
                   models.AggregateResult.package_id
        ).join(models.IndicatorTest
        ).join(models.Test
        ).join(models.AggregateResult
        ).join(models.Package
        ).join(models.OrganisationPackage
        ).join(models.Organisation
        ).all()

    #pconditions = models.PublisherCondition.query.filter(
    #        models.Organisation.organisation_code==organisation.organisation_code
    #        ).join(models.OrganisationPackage
    #        ).join(models.Organisation
    #        ).all()
    # TODO: refactor PublisherCondition to refer to 
    # Organisation rather than PackageGroup
    pconditions = None

    return aggregation.agr_results(aggregate_results, 
                                                conditions=pconditions, 
                                                mode="publisher_indicators")



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

from iatidq import dqorganisations, dqpackages
import aggregation

from iatidq.models import *

import StringIO
import unicodecsv

@app.route("/organisations/")
@app.route("/organisations/<organisation_code>/")
def organisations(organisation_code=None, aggregation_type=None):

    aggregation_type=integerise(request.args.get('aggregation_type', None))

    template_args = {}
    if organisation_code is not None:
        organisation = dqorganisations.organisations(organisation_code)

        try:
            summary_data = _organisation_indicators_summary(organisation, aggregation_type)
        except Exception, e:
            summary_data = None

        template_args = dict(organisation=organisation, 
                             summary_data=summary_data)

        return render_template("organisation.html", **template_args)
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


def integerise(data):
    try:
        return int(data)
    except ValueError:
        return None
    except TypeError:
        return None

@app.route("/organisations/<organisation_code>/publication/")
def organisation_publication(organisation_code=None, aggregation_type=None):

    aggregation_type=integerise(request.args.get('aggregation_type', None))

    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    aggregate_results = _organisation_indicators(organisation, aggregation_type)

    latest_runtime=1

    return render_template("organisation_indicators.html", 
                           organisation=organisation,
                           results=aggregate_results, runtime=latest_runtime)

@app.route("/organisations/publication.csv")
def all_organisations_publication_csv():
    strIO = StringIO.StringIO()
    fieldnames = "organisation_name organisation_code indicator_name indicator_description percentage_passed num_results".split()
    out = unicodecsv.DictWriter(strIO, fieldnames=fieldnames)
    headers = {}
    for fieldname in fieldnames:
        headers[fieldname] = fieldname
    out.writerow(headers)
    organisations = Organisation.query.all()
    for organisation in organisations:

        aggregate_results = _organisation_indicators(organisation)

        for resultid, result in aggregate_results.items():
            out.writerow({
                          "organisation_name": organisation.organisation_name, 
                          "organisation_code": organisation.organisation_code, 
                          "indicator_name": result['indicator']['name'],
                          "indicator_description": result['indicator']['description'], 
                          "percentage_passed": result['results_pct'], 
                          "num_results": result['results_num']
                        })      
    strIO.seek(0)
    return send_file(strIO,
                         attachment_filename="dataqualityresults_all.csv",
                         as_attachment=True)

@app.route("/organisations/<organisation_code>/publication.csv")
def organisation_publication_csv(organisation_code=None):
    p_group = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    aggregate_results = _organisation_indicators(p_group)

    strIO = StringIO.StringIO()
    fieldnames = "organisation_name organisation_code indicator_name indicator_description percentage_passed num_results".split()
    out = unicodecsv.DictWriter(strIO, fieldnames=fieldnames)
    headers = {}
    for fieldname in fieldnames:
        headers[fieldname] = fieldname
    out.writerow(headers)

    for resultid, result in aggregate_results.items():
        out.writerow({
                      "organisation_name": p_group.organisation_name, 
                      "organisation_code": p_group.organisation_code, 
                      "indicator_name": result['indicator']['name'],
                      "indicator_description": result['indicator']['description'], 
                      "percentage_passed": result['results_pct'], 
                      "num_results": result['results_num']
                    })      
    strIO.seek(0)
    return send_file(strIO,
                     attachment_filename="dataqualityresults_" + organisation_code + ".csv",
                     as_attachment=True)

@app.route("/organisations/<organisation_code>/edit/", methods=['GET','POST'])
def organisation_edit(organisation_code=None):
    

    packages = dqpackages.packages()
    packagegroups = dqpackages.packageGroups()
    organisation = dqorganisations.organisations(organisation_code)

    if request.method == 'POST':
        if 'addpackages' in request.form:
            condition = request.form['condition']
            def add_org_pkg(package):
                data = {
                    'organisation_id': organisation.id,
                    'package_id': package,
                    'condition': condition
                    }
                if dqorganisations.addOrganisationPackage(data):
                    flash('Successfully added package to your organisation.', 
                          'success')
                else:
                    flash("Couldn't add package to your organisation.", 
                          'error')

            packages = request.form.getlist('package')
            [ add_org_pkg(package) for package in packages ]

        elif 'addpackagegroup' in request.form:
            condition = request.form['condition']
            data = {
                'organisation_id': organisation.id,
                'packagegroup_id': request.form['packagegroup'],
                'condition': condition
            }
            add_packagegroups = dqorganisations.addOrganisationPackageFromPackageGroup(data)
            if 'applyfuture' in request.form:
                if dqorganisations.addOrganisationPackageGroup(data):
                    flash('All future packages in this package group will be added to this organisation', 'success')
                else:
                    flash('Could not ensure that all packages in this package group will be added to this organisation', 'error')
                
            if add_packagegroups:
                flash('Successfully added ' + str(add_packagegroups) + ' packages to your organisation.', 
                      'success')
            else:
                flash("No packages were added to your organisation. This could be because you've already added all existing ones.", 
                      'error')
                
        elif 'updateorganisation' in request.form:
            data = {
                'organisation_code': request.form['organisation_code'],
                'organisation_name': request.form['organisation_name']
            }
            organisation = dqorganisations.updateOrganisation(
                organisation_code, data)

    organisationpackages = dqorganisations.organisationPackages(
        organisation.organisation_code)

    return render_template(
        "organisation_edit.html", 
        organisation=organisation, 
        packages=packages, 
        packagegroups=packagegroups,
        organisationpackages=organisationpackages)

@app.route("/organisations/<organisation_code>/<package_name>/<organisationpackage_id>/delete/")
def organisationpackage_delete(organisation_code=None, 
                               package_name=None, organisationpackage_id=None):

    def get_message(result):
        if result:
            return ('Successfully removed package %s from organisation %s.',
                    'success')
        else:
            return ('Could not remove package %s from organisation %s.',
                    'error')

    result = dqorganisation.deleteOrganisationPackage(
        organisation_code, package_name, organisationpackage_id)

    msg_template, msg_type = get_message(result)    
    flash(msg_template % (package_name, organisation_code), msg_type)
        
    return redirect(url_for('organisation_edit', 
                            organisation_code=organisation_code))

def _organisation_indicators_summary(organisation, aggregation_type=None):
    summarydata = _organisation_indicators(organisation, aggregation_type)
    # Create crude total score
    totalpct = 0.00
    totalindicators = 0
    for indicator, indicatordata in summarydata.items():
        totalpct += indicatordata['results_pct']
        totalindicators +=1
    totalscore = totalpct/totalindicators
    return totalscore, totalindicators
    

def _organisation_indicators(organisation, aggregation_type=None):
    aggregate_results = db.session.query(Indicator,
                                     Test,
                                     AggregateResult.results_data,
                                     AggregateResult.results_num,
                                     AggregateResult.result_hierarchy,
                                     AggregateResult.package_id,
                                     func.max(AggregateResult.runtime_id)
        ).filter(Organisation.organisation_code==organisation.organisation_code
        ).filter(AggregateResult.aggregateresulttype_id == aggregation_type
        ).group_by(AggregateResult.result_hierarchy, 
                   Test, 
                   AggregateResult.package_id,
                   Indicator,
                   AggregateResult.results_data,
                   AggregateResult.results_num,
                   AggregateResult.package_id
        ).join(IndicatorTest
        ).join(Test
        ).join(AggregateResult
        ).join(Package
        ).join(OrganisationPackage
        ).join(Organisation
        ).all()

    pconditions = OrganisationCondition.query.filter_by(organisation_id=organisation.id
            ).all()

    return aggregation.agr_results(aggregate_results, 
                                                conditions=pconditions, 
                                                mode="publisher_indicators")


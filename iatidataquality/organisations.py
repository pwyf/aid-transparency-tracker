
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
from iatidq import dqusers

import os
import sys
import json

import operator

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from iatidq import dqorganisations, dqpackages, dqaggregationtypes, dqsurveys

from iatidq.models import *

import StringIO
import unicodecsv
import usermanagement

@app.route("/organisations/<organisation_code>/index/")
@usermanagement.perms_required('organisation', 'view')
def organisations_index(organisation_code=None):
    info_results = {
        }
    
    aggregation_type=integerise(request.args.get('aggregation_type', 2))

    template_args = {}
    org_packages = dqorganisations.organisationPackages(organisation_code)

    def get_info_results():
        print "gir"
        for _, p in org_packages:
            package_id = p.package_id
            from sqlalchemy import func
            runtime = db.session.query(
                func.max(InfoResult.runtime_id)).filter(
                InfoResult.package_id == package_id
                ).first()
            import iatidq.inforesult
            runtime, = runtime
            results = iatidq.inforesult.info_results(package_id, runtime, organisation.id)
            if "coverage" in results:
                try:
                    yield int(results["coverage_current"])
                except TypeError:
                    yield 0

    organisation = dqorganisations.organisations(organisation_code)
    packagegroups = dqorganisations.organisationPackageGroups(organisation_code)
            
    info_results["coverage_current"] = \
        reduce(operator.add, [ir for ir in get_info_results()], 0)

    # coverage_total = organisation.organisation_total_spend
    # FIXME: use organisation_total_spend 
    # when data is imported to db
    coverage_total = (organisation.organisation_total_spend)*1000000
    coverage_found = info_results["coverage_current"]

    if (coverage_total and coverage_found):
        coverage_pct = int((float(coverage_found)/float(coverage_total))*100)
        coverage = {
                    'total': coverage_total,
                    'found': coverage_found,
                    'pct': coverage_pct
                }
    else:
        coverage = {
                    'total': None,
                    'found': None,
                    'pct': None
        }
    organisation_survey = dqsurveys.getSurvey(organisation_code)
    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)
    if organisation_survey:
        if organisation_survey.Workflow.name in ['donorreview', 'pwyfreview']:
            surveydata = surveydata["researcher"]
            surveydata_workflow = 'donorreview'
        elif organisation_survey.Workflow.name in ['donorcomments', 'pwyffinal']:
            surveydata = surveydata["pwyfreview"]
            surveydata_workflow = 'donorcomments'
        elif organisation_survey.Workflow.name == 'finalised':
            surveydata = surveydata["pwyffinal"]
            surveydata_workflow = 'finalised'
        else:
            surveydata = None
    else:
        surveydata = None

    try:
        summary_data = _organisation_indicators_summary(organisation, 
                      aggregation_type)
    except Exception, e:
        summary_data = None

    template_args = dict(organisation=organisation, 
                         summary_data=summary_data,
                         packagegroups=packagegroups,
                         coverage=coverage,
                         surveydata=surveydata,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)

    return render_template("organisation_index.html", **template_args)

@app.route("/organisations/")
@app.route("/organisations/<organisation_code>/")
def organisations(organisation_code=None):
    check_perms = usermanagement.check_perms('organisation', 'view', {'organisation_code':organisation_code})
    if organisation_code is not None:
        if check_perms:
            return redirect(url_for('organisations_index', organisation_code=organisation_code))
        else:
            return redirect(url_for('organisation_publication', organisation_code=organisation_code))
    else:
        organisations = dqorganisations.organisations()

        template_args = dict(organisations=organisations,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)

        return render_template("organisations.html", **template_args)

@app.route("/organisations/new/", methods=['GET','POST'])
@usermanagement.perms_required()
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
    return render_template("organisation_edit.html", organisation=organisation,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)

def integerise(data):
    try:
        return int(data)
    except ValueError:
        return None
    except TypeError:
        return None

@app.route("/organisations/<organisation_code>/publication/")
def organisation_publication(organisation_code=None, aggregation_type=2):
    check_perms = usermanagement.check_perms('organisation', 'view', {'organisation_code': organisation_code})
    
    if check_perms:
        aggregation_type=integerise(request.args.get('aggregation_type', 2))
        all_aggregation_types = dqaggregationtypes.aggregationTypes()

        organisation = Organisation.query.filter_by(
            organisation_code=organisation_code).first_or_404()

        aggregate_results = dqorganisations._organisation_indicators_split(
            organisation, aggregation_type)
        
        organisation_survey = dqsurveys.getSurvey(organisation_code)
        surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)
        if organisation_survey:
            if organisation_survey.Workflow.name in ['donorreview', 'pwyfreview']:
                surveydata = surveydata["researcher"]
                surveydata_workflow = 'donorreview'
            elif organisation_survey.Workflow.name in ['donorcomments', 'pwyffinal']:
                surveydata = surveydata["pwyfreview"]
                surveydata_workflow = 'donorcomments'
            elif organisation_survey.Workflow.name == 'finalised':
                surveydata = surveydata["pwyffinal"]
                surveydata_workflow = 'finalised'
            else:
                surveydata = None
                surveydata_workflow=None
        else:
            surveydata = None
            surveydata_workflow=None
        published_status = dqsurveys.publishedStatus()

        published_status_by_id = dict(map(lambda x: (x.id, x), published_status))

        publishedformats = dqsurveys.publishedFormatsAll()
        publishedformats = dict(map(lambda pf: (pf.id, pf), publishedformats))

        published_status_by_id[None] = {'name': 'Unknown',
                                        'publishedstatus_class': 'label-inverse'}

        publishedformats[None] = {'name': 'Unknown',
                                        'format_class': 'label-inverse'}

        latest_runtime=1

        return render_template("organisation_indicators.html", 
                               organisation=organisation,
                               results=aggregate_results, 
                               runtime=latest_runtime,
                               all_aggregation_types=all_aggregation_types,
                               aggregation_type=aggregation_type,
                               surveydata=surveydata,
                               published_status=published_status_by_id,
                               published_format=publishedformats,
                               surveydata_workflow=surveydata_workflow,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)
    else:
        aggregation_type=integerise(request.args.get('aggregation_type', 2))
        all_aggregation_types = dqaggregationtypes.aggregationTypes()

        organisation = Organisation.query.filter_by(
            organisation_code=organisation_code).first_or_404()

        aggregate_results = dqorganisations._organisation_indicators(
            organisation, aggregation_type)

        packages = dqorganisations.organisationPackages(organisation_code)

        return render_template("organisation_publication_public.html", 
                               organisation=organisation,
                               results=aggregate_results, 
                               all_aggregation_types=all_aggregation_types,
                               aggregation_type=aggregation_type,
                               packages=packages,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)

@app.route("/organisations/<organisation_code>/publication/detail/")
def organisation_publication_detail(organisation_code=None):
    aggregation_type=integerise(request.args.get('aggregation_type', 2))

    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    packages = dqorganisations.organisationPackages(
        organisation.organisation_code)

    all_aggregation_types = dqaggregationtypes.aggregationTypes()

    aggregate_results = dqorganisations._organisation_detail(organisation, aggregation_type)

    txt = render_template("organisation_detail.html", 
                          organisation=organisation, packages=packages, 
                          results=aggregate_results,
                           all_aggregation_types=all_aggregation_types,
                           aggregation_type=aggregation_type,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user)
    return txt

@app.route("/organisations/publication.csv")
@usermanagement.perms_required()
def all_organisations_publication_csv():
    strIO = StringIO.StringIO()
    fieldnames = "organisation_name organisation_code indicator_category_name indicator_subcategory_name indicator_name indicator_description percentage_passed num_results points".split()
    out = unicodecsv.DictWriter(strIO, fieldnames=fieldnames)
    headers = {}
    for fieldname in fieldnames:
        headers[fieldname] = fieldname
    out.writerow(headers)
    organisations = Organisation.query.all()
    for organisation in organisations:

        aggregate_results = dqorganisations._organisation_indicators(
            organisation)

        if (organisation.frequency == "less than quarterly"):
            freq = 0.9
        else:
            freq = 1.0

        for resultid, result in aggregate_results.items():
            if result['results_pct'] == 0:
                points = str(0)
            else:
                points = str(((float(result['results_pct'])*freq)/2.0)+50)
            out.writerow({
                          "organisation_name": organisation.organisation_name, 
                          "organisation_code": organisation.organisation_code, 
                          "indicator_category_name": result['indicator']['indicator_category_name'],
                          "indicator_subcategory_name": result['indicator']['indicator_subcategory_name'],
                          "indicator_name": result['indicator']['description'],
                          "indicator_description": result['indicator']['longdescription'], 
                          "percentage_passed": result['results_pct'], 
                          "num_results": result['results_num'],
                          "points": points
                        })      
    strIO.seek(0)
    return send_file(strIO,
                         attachment_filename="dataqualityresults_all.csv",
                         as_attachment=True)

@app.route("/organisations/<organisation_code>/publication.csv")
@usermanagement.perms_required('organisation', 'view')
def organisation_publication_csv(organisation_code=None):
    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    aggregate_results = dqorganisations._organisation_indicators(organisation)

    strIO = StringIO.StringIO()
    fieldnames = "organisation_name organisation_code indicator_category_name indicator_subcategory_name indicator_name indicator_description percentage_passed num_results points".split()
    out = unicodecsv.DictWriter(strIO, fieldnames=fieldnames)
    headers = {}
    for fieldname in fieldnames:
        headers[fieldname] = fieldname
    out.writerow(headers)

    if (organisation.frequency == "less than quarterly"):
        freq = 0.9
    else:
        freq = 1.0
    for resultid, result in aggregate_results.items():
        if result['results_pct'] == 0:
            points = str(0)
        else:
            points = str(((float(result['results_pct'])*freq)/2.0)+50)
        out.writerow({
                      "organisation_name": organisation.organisation_name, 
                      "organisation_code": organisation.organisation_code, 
                      "indicator_category_name": result['indicator']['indicator_category_name'],
                      "indicator_subcategory_name": result['indicator']['indicator_subcategory_name'],
                      "indicator_name": result['indicator']['description'], 
                      "indicator_description": result['indicator']['longdescription'], 
                      "percentage_passed": result['results_pct'], 
                      "num_results": result['results_num'],
                      "points": points
                    })      
    strIO.seek(0)
    return send_file(strIO,
                     attachment_filename="dataqualityresults_" + organisation_code + ".csv",
                     as_attachment=True)

@app.route("/organisations/<organisation_code>/edit/", methods=['GET','POST'])
@usermanagement.perms_required()
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
        organisationpackages=organisationpackages,
        admin=usermanagement.check_perms('admin'),
        loggedinuser=current_user)

@app.route("/organisations/<organisation_code>/<package_name>/<organisationpackage_id>/delete/")
@usermanagement.perms_required()
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

def _organisation_indicators_summary(organisation, aggregation_type=2):
    summarydata = dqorganisations._organisation_indicators(organisation, 
                                                            aggregation_type)

    # Create crude total score
    totalpct = 0.00
    totalindicators = 0

    if not summarydata:
        return None

    percentages = [ i["results_pct"] for i in summarydata.values() ]
    totalpct = reduce(operator.add, percentages, 0.0)
    totalindicators = len(percentages)
    totalscore = totalpct/totalindicators

    return totalscore, totalindicators
    

@app.route('/tmp/inforesult/<package_code>/<runtime_id>')
def tmp_inforesult(package_code, runtime_id):
    import json
    from iatidq import inforesult

    return json.dumps(inforesult.info_results(package_code, runtime_id), 
                      indent=2)

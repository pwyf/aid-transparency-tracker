
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
from iatidq import dqusers, dqindicators
from iatidataquality import surveys
from iatidq.dqcsv import make_csv
from iatidq import util

import os
import sys
import json

import operator

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from iatidq import dqorganisations, dqpackages, dqaggregationtypes, donorresponse
import iatidq.survey.data as dqsurveys
import iatidq.inforesult
from iatidq.models import *

import StringIO
import unicodecsv
import usermanagement

def get_info_results(org_packages, organisation):
    for _, p in org_packages:
        package_id = p.package_id
        runtime = db.session.query(
            func.max(InfoResult.runtime_id)).filter(
            InfoResult.package_id == package_id
            ).first()
        runtime, = runtime
        results = iatidq.inforesult.info_results(
            package_id, runtime, organisation.id)
        if "coverage" not in results:
            continue
        try:
            yield int(results["coverage_current"])
        except TypeError:
            yield 0

# FIXME: use organisation_total_spend when data is imported to db
def get_coverage(organisation, info_results):
    coverage_found = reduce(operator.add, info_results, 0)
    coverage_total = organisation.organisation_total_spend * 1000000

    if coverage_total and coverage_found:
        c = float(coverage_found) / float(coverage_total)
        coverage_pct = int(c * 100)
    else:
        coverage_pct = None
        coverage_found = None
        coverage_total = None

    return {
        'total': coverage_total,
        'found': coverage_found,
        'pct': coverage_pct
        }

def get_summary_data(organisation, aggregation_type):    
    #try:
    return _organisation_indicators_summary(organisation, aggregation_type)
    #except Exception, e:
    #    return None

@app.route("/organisations/coverage/")
@usermanagement.perms_required()
def organisations_coverage():
    organisations = dqorganisations.organisations()
    coverage_data = {}

    for organisation in organisations:
        org_packages = dqorganisations.organisationPackages(organisation.organisation_code)
        irs = [ir for ir in get_info_results(org_packages, organisation)]
        coverage_data[organisation.id] = (get_coverage(organisation, irs))
    return render_template("organisations_coverage.html",
        organisations=organisations,
        coverage_data=coverage_data,
        admin=usermanagement.check_perms('admin'),
        loggedinuser=current_user
        )

@app.route("/organisations/<organisation_code>/index/")
@usermanagement.perms_required('organisation', 'view')
def organisations_index(organisation_code=None):
    
    aggregation_type=integerise(request.args.get('aggregation_type', 2))

    template_args = {}
    org_packages = dqorganisations.organisationPackages(organisation_code)

    organisation = dqorganisations.organisations(organisation_code)
    packagegroups = dqorganisations.organisationPackageGroups(organisation_code)

    irs = [ir for ir in get_info_results(org_packages, organisation)]
    coverage = get_coverage(organisation, irs)

    organisation_survey = dqsurveys.getSurvey(organisation_code)

    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)

    surveydata, _ = dqsurveys.get_survey_data_and_workflow(
        organisation_survey, surveydata)

    summary_data = get_summary_data(organisation, aggregation_type)

    allowed_to_view_survey = usermanagement.check_perms(
        "survey",
        "view")
    allowed_to_edit_survey_researcher = usermanagement.check_perms(
        "survey_researcher",
        "edit",
        {"organisation_code": organisation_code})

    show_researcher_button = (
        allowed_to_edit_survey_researcher and
         (
          (organisation_survey and
           organisation_survey.Workflow.name == 'researcher')
           or
          (not organisation_survey)
         )
        )

    template_args = dict(organisation=organisation,
                         summary_data=summary_data,
                         packagegroups=packagegroups,
                         coverage=coverage,
                         surveydata=surveydata,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user,
                         allowed_to_view_survey=allowed_to_view_survey,
                         show_researcher_button=show_researcher_button)

    return render_template("organisation_index.html", **template_args)

@app.route("/organisations/")
@app.route("/organisations/<organisation_code>/")
def organisations(organisation_code=None):
    check_perms = usermanagement.check_perms(
        'organisation', 'view', {'organisation_code':organisation_code})

    if organisation_code is not None:
        template = {
            True: 'organisations_index',
            False: 'organisation_publication'
            }[check_perms]

        return redirect(url_for(template, organisation_code=organisation_code))

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

def get_ordinal_values_years():
    years = [
        (3, '3 years ahead', 'success'),
        (2, '2 years ahead', 'warning'),
        (1, '1 year ahead', 'important'),
        (0, 'No forward data', 'inverse'),
        (None, 'Unknown', '')
        ]
    struct = lambda yr: (yr[0], ({
            "text": yr[1], 
            "class": yr[2] 
            }))
    return map(struct, years)


# this lambda and the things which use it exists in surveys.py as well
# ... merge?
id_tuple = lambda x: (x.id, x.as_dict())

name_tuple = lambda x: (x.name, x.as_dict())

def organisation_publication_authorised(organisation_code, aggregation_type):
    aggregation_type=integerise(request.args.get('aggregation_type', 2))
    all_aggregation_types = dqaggregationtypes.allAggregationTypes()

    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    aggregate_results = dqorganisations._organisation_indicators_split(
        organisation, aggregation_type)

    aggregate_results['zero'] = util.resort_dict_indicator(
                                aggregate_results['zero'])
    aggregate_results['non_zero'] = util.resort_dict_indicator(
                                    aggregate_results['non_zero'])
        
    organisation_survey = dqsurveys.getSurvey(organisation_code)
    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)
    
    surveydata, surveydata_workflow = dqsurveys.get_survey_data_and_workflow(
        organisation_survey, surveydata)

    published_status_by_id = dict(map(id_tuple, dqsurveys.publishedStatus()))
    publishedformats = dict(map(id_tuple, dqsurveys.publishedFormatsAll()))

    published_status_by_id[None] = {
        'title': 'Unknown',
        'title': 'unknown',
        'publishedstatus_class': 'label-inverse'
        }

    publishedformats[None] = {
        'title': 'Unknown',
        'name': 'unknown',
        'format_class': 'label-inverse'
        }

    latest_runtime=1

    years = dict(get_ordinal_values_years())

    test_level_description = {
        3: ("on", "organisation files", ""),
        2: ("on", "each package of data", ""),
        1: ("for", "each activity", "in your data"),
        0: ("for", "each transaction", "in your data")
        }

    links = {
        "organisation_page": url_for(
            'organisations', 
            organisation_code=organisation.organisation_code),
        "organisation_detail": url_for(
            'organisation_publication_detail', 
            organisation_code=organisation.organisation_code),
        "organisation_feedback": url_for(
            'organisations_feedback', 
            organisation_code=organisation.organisation_code)
        }
    if surveydata:
        links.update({
                "organisation_survey_edit": url_for(
                    'organisation_survey_edit', 
                    organisation_code=organisation.organisation_code, 
                    workflow_name=surveydata_workflow)
                })

    def agg_detail(agt):
        tmp = agt.as_dict()
        tmp["selected"] = agt.id == aggregation_type
        return tmp

    agg_type = [ agg_detail(agt) for agt in all_aggregation_types ]

    frequencies = { 
        "less than quarterly": (0.5,
                                """It looks like you publish less often than
          quarterly, so the maximum you can score for IATI data is
          75 points. The total points for the relevant indicators have been
          adjusted accordingly"""),
        "quarterly": (0.9,
                      """It looks like you publish quarterly and not monthly,
          so the maximum you can score for IATI data is 95 points. The total 
          points for the relevant indicators have been adjusted 
          accordingly.""")
        }

    freq_score = frequencies.get(organisation.frequency, (1.0, ))
    if organisation.frequency in frequencies:
        freq_alert = { "text": frequencies.get(organisation.frequency)[1] }
    else:
        freq_alert = None

    def annotate(res, zero):
        def annotate_test(t):
            tmp2 = dict(t)
            tmp2["results_pct_rounded"] = round(tmp2["results_pct"], 2)
            tmp2["results_num_rounded"] = round(tmp2["results_num"], 2)

            if "test_level" not in tmp2["test"]: # hopeless
                return tmp2

            test_level = tmp2["test"]["test_level"]
            level = test_level_description[test_level]
            preposition, description, coda = level
            tmp2["level_preposition"] = preposition
            tmp2["level_description"] = description
            tmp2["level_coda"] = coda

            return tmp2

        tmp = dict(res)

        tmp["is_activity"] = (
            tmp["indicator"]["indicator_category_name"] == "activity")

        multiplier = {True: freq_score[0], False: 1}[tmp["is_activity"]]

        def points():
            if not zero:
                return round((tmp["results_pct"] * multiplier / 2.0 + 50), 2)

            ind_id = res["indicator"]["id"]
            
            if surveydata:
                if (res["indicator"]["indicator_ordinal"] and surveydata[ind_id].PublishedFormat):
                    return round(
                        (surveydata[ind_id].OrganisationSurveyData.ordinal_value/3.0) * 
                        surveydata[ind_id].PublishedFormat.format_value * 50, 2)
                elif (surveydata[ind_id].PublishedStatus and surveydata[ind_id].PublishedFormat):
                    return (
                        surveydata[ind_id].PublishedStatus.publishedstatus_value * 
                        surveydata[ind_id].PublishedFormat.format_value * 50)
                else:
                    return 0
            else:
                return ""

        tmp["points"] = points()
        if not zero:
            tmp["points_minus_50"] = tmp["points"] - 50
            # it all fails if the other branch tries to use this value

        tmp["tests"] = map(annotate_test, res["tests"])

        if zero:
            if surveydata:
                osd = surveydata[tmp["indicator"]["id"]].OrganisationSurveyData.as_dict()

                def status_class_and_text():
                    if tmp["indicator"]["indicator_ordinal"]:
                        return (years[osd["ordinal_value"]]["class"], 
                                years[osd["ordinal_value"]]["text"])
                    else:
                        return (published_status_by_id[osd["published_status"]]["publishedstatus_class"], 
                                published_status_by_id[osd["published_status"]]["title"])
                def format_class_and_text():
                    if published_status_by_id[osd["published_status"]]["publishedstatus_class"] != 'important':
                        return (publishedformats[osd["published_format"]]["format_class"], 
                                publishedformats[osd["published_format"]]["title"])
                    else:
                        return ("", "")
                tmp["status_class"], tmp["status_text"] = status_class_and_text()
                tmp["format_class"], tmp["format_text"] = format_class_and_text()

        tmp["results_pct_rounded"] = round(tmp["results_pct"], 2)
        tmp["results_pct_halved_rounded"] = round(tmp["results_pct"]/2.0, 2)

        return tmp

    annotate_zero = lambda res : annotate(res, True)
    annotate_nonzero = lambda res : annotate(res, False)

    # testdata.results_pct|round(2)
    # testdata["results_num"]|round(2)
    # as far as line 296

    def get_sd(data):
        return {
            "OrganisationSurveyData": data[0].as_dict(),
            "Workflow": data[3].as_dict(),
        }

    def jsonsurvey(surveydata):
        return dict(map(lambda x: (x[0], get_sd(x[1])),
                             surveydata.items()))

    payload = {
        "organisation": organisation.as_dict(),
        "links": links,
        "agg_type": agg_type,
        "freq": freq_score,
        "freq_alert": freq_alert,
        "result": {
            "non_zero": map(annotate_nonzero, aggregate_results["non_zero"].values()),
            "zero":map(annotate_zero, aggregate_results["zero"].values())
            },
        "surveydata": jsonsurvey(surveydata)
        }
    json_data = json.dumps(payload, indent=2)

    return render_template("organisation_indicators.html",
                           organisation=organisation,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user,
                           json_data=json_data)

# this function is unacceptably long; it really wants to be a class
def organisation_publication_unauthorised(organisation_code, aggregation_type):
    aggregation_type=integerise(request.args.get('aggregation_type', 2))
    all_aggregation_types = dqaggregationtypes.aggregationTypes()

    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    aggregate_results = dqorganisations._organisation_indicators_complete_split(
        organisation, aggregation_type)

    packages = dqorganisations.organisationPackages(organisation_code)

    org_indicators = dqindicators.indicators(app.config["INDICATOR_GROUP"])

    lastyearsdata = iatidq.survey.mapping.get_organisation_results(
        organisation_code, 
        [i.name for i in org_indicators]
        )

    publishedformats = dict(map(name_tuple, dqsurveys.publishedFormatsAll()))

    def annotate(res):
        tmp = dict(res)
        name = res["indicator"]["name"]
        lyd = lastyearsdata[name]
        tmp["lastyearsdata"] = lyd
        tmp["lastyearsdata_iati"] = lyd["iati_manual"] == "iati"
        tmp["lastyearsdata_manual"] = lyd["iati_manual"] == "manual"

        def format_and_title():
            if lyd["total_points"] > 0:
                if tmp["lastyearsdata_iati"]:
                    return ("success", "IATI")
                else:
                    pub_format = publishedformats[lyd["publication_format"]]
                    return (pub_format.format_class, pub_format.title)
            elif lyd["publication_status"] == "sometimes":
                return ("default", "Sometimes published")
            else:
                return ("inverse", "Not published")

        ly_format, ly_title = format_and_title()
        tmp["lastyearsdata_format"] = ly_format
        tmp["lastyearsdata_title"] = ly_title

        tmp["uses_iati"] = res.get("results_pct", 0) > 0

        return tmp

    result = {
        "commitment": map(annotate, 
                          util.resort_sqlalchemy_indicator(
                aggregate_results['commitment']).values()),
        "publication_organisation": map(annotate,
                                        util.resort_dict_indicator(
                aggregate_results['publication_organisation']).values()),
        "publication_activity": map(annotate,
                                    util.resort_dict_indicator(
                aggregate_results['publication_activity']).values())
        }

    published_status_by_id = dict(map(id_tuple, dqsurveys.publishedStatus()))

    published_status_by_id[None] = {
        'name': 'Unknown',
        'publishedstatus_class': 'label-inverse'
        }

    publishedformats[None] = {
        'name': 'Unknown',
        'format_class': 'label-inverse'
        }

    latest_runtime=1

    years = dict(get_ordinal_values_years())

    payload = {
        "links": {
            "login": url_for('login', next='/organisations/' 
                             + organisation.organisation_code 
                             + '/publication'),
            "orgpage": url_for('organisations', 
			   organisation_code=organisation.organisation_code)
            },
        "organisation": organisation.as_dict(),
        "result": result
        }
    
    json_data = json.dumps(payload, indent=2)

    return render_template("organisation_index_public_2014.html",
                           organisation=organisation,
                           results=aggregate_results,
                           all_aggregation_types=all_aggregation_types,
                           aggregation_type=aggregation_type,
                           packages=packages,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user,
                           lastyearsdata=lastyearsdata,
                           publishedformats=publishedformats,
                           years=years,
                           json_data=json_data,
                           old_publication_status = surveys.get_old_publication_status())

@app.route("/organisations/<organisation_code>/publication/")
def organisation_publication(organisation_code=None, aggregation_type=2):
    check_perms = usermanagement.check_perms(
        'organisation', 'view', {'organisation_code': organisation_code}
        )
    
    if check_perms:
        return organisation_publication_authorised(
            organisation_code,
            aggregation_type)
    else:
        return organisation_publication_unauthorised(
        organisation_code,
        aggregation_type)

def _organisation_publication_detail(organisation_code, aggregation_type, 
                                     is_admin):

    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    packages = dqorganisations.organisationPackages(
        organisation.organisation_code)

    all_aggregation_types = dqaggregationtypes.aggregationTypes()

    aggregate_results = dqorganisations.make_publisher_summary(
        organisation, aggregation_type)

    return render_template("organisation_detail.html", 
                           organisation=organisation, packages=packages, 
                           results=aggregate_results,
                           all_aggregation_types=all_aggregation_types,
                           aggregation_type=aggregation_type,
                           admin=is_admin,
                           loggedinuser=current_user)

@app.route("/organisations/<organisation_code>/publication/detail/")
def organisation_publication_detail(organisation_code=None):
    aggregation_type=integerise(request.args.get('aggregation_type', 2))
    is_admin = usermanagement.check_perms('admin')
    return _organisation_publication_detail(
        organisation_code, aggregation_type, is_admin)

def _org_pub_csv(organisations, filename, index_data=False, history=False):
    string_io = make_csv(organisations, index_data, history)
    return send_file(string_io, attachment_filename=filename, 
                     as_attachment=True)

@app.route("/organisations/publication_index_history.csv")
@usermanagement.perms_required()
def all_organisations_publication_index_csv_history():
    organisations = Organisation.query.all()
    return _org_pub_csv(organisations, "tracker_index_history.csv", True, True)

@app.route("/organisations/publication_index.csv")
@usermanagement.perms_required()
def all_organisations_publication_index_csv():
    organisations = Organisation.query.all()
    return _org_pub_csv(organisations, "dataqualityresults_index.csv", True)

@app.route("/organisations/publication.csv")
@usermanagement.perms_required()
def all_organisations_publication_csv():
    organisations = Organisation.query.all()
    return _org_pub_csv(organisations, "dataqualityresults_all.csv")

@app.route("/organisations/<organisation_code>/publication.csv")
@usermanagement.perms_required('organisation', 'view')
def organisation_publication_csv(organisation_code=None):
    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    organisations = [organisation]
    filename = "dataqualityresults_%s.csv" % organisation_code

    return _org_pub_csv(organisations, filename)

def add_packages(organisation):
    def add_org_pkg(package):
        condition = request.form['condition']
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

def add_packagegroup(organisation):
    condition = request.form['condition']
    data = {
        'organisation_id': organisation.id,
        'packagegroup_id': request.form['packagegroup'],
        'condition': condition
        }
    total = dqorganisations.addOrganisationPackageFromPackageGroup(data)
    if 'applyfuture' in request.form:
        if dqorganisations.addOrganisationPackageGroup(data):
            flash(
                'All future packages in this package group will be '
                'added to this organisation', 'success')
        else:
            flash(
                'Could not ensure that all packages in this package '
                'group will be added to this organisation', 'error')
    if total:
        flash(
            'Successfully added %d packages to your organisation.' % total, 
            'success')
    else:
        flash(
            "No packages were added to your organisation. This "
            "could be because you've already added all existing ones.", 
            'error')

def update_organisation(organisation_code):
    if 'no_independent_reviewer' in request.form:
        irev=True
    else:
        irev=False
    if 'organisation_responded' in request.form:
        orgresp=donorresponse.RESPONSE_TYPES[request.form['organisation_responded']]["id"]
    else:
        orgresp=None
    data = {
        'organisation_code': request.form['organisation_code'],
        'organisation_name': request.form['organisation_name'],
        'no_independent_reviewer': irev,
        'organisation_responded': orgresp
        }
    organisation = dqorganisations.updateOrganisation(
        organisation_code, data)

@app.route("/organisations/<organisation_code>/edit/", methods=['GET','POST'])
@usermanagement.perms_required()
def organisation_edit(organisation_code=None):
    packages = dqpackages.packages()
    packagegroups = dqpackages.packageGroups()
    organisation = dqorganisations.organisations(organisation_code)

    if request.method == 'POST':
        if 'addpackages' in request.form:
            add_packages(organisation)
        elif 'addpackagegroup' in request.form:
            add_packagegroup(organisation)
        elif 'updateorganisation' in request.form:
            update_organisation(organisation_code)

    organisationpackages = dqorganisations.organisationPackages(
        organisation.organisation_code)

    return render_template(
        "organisation_edit.html", 
        organisation=organisation, 
        packages=packages, 
        packagegroups=packagegroups,
        donorresponses=donorresponse.RESPONSE_TYPES,
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

    result = dqorganisations.deleteOrganisationPackage(
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


    testing = [ (i["indicator"]["name"], i["results_pct"]) for i in summarydata.values() ]
    print testing
    percentages = [ i["results_pct"] for i in summarydata.values() ]
    totalpct = reduce(operator.add, percentages, 0.0)
    totalindicators = len(percentages)
    totalscore = totalpct/totalindicators

    return totalscore, totalindicators
    

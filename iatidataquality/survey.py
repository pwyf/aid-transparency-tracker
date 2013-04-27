
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)

from iatidataquality import app
from iatidataquality import db

import os
import sys

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from iatidq import dqindicators, dqsurveys, dqorganisations

from iatidq.models import *

import unicodecsv
import json
import json

@app.route("/surveys/admin/")
def surveys_admin():
    workflows = dqsurveys.workflows()
    publishedstatuses=dqsurveys.publishedStatus()
    return render_template("surveys_admin.html", 
                           workflows=workflows,
                           publishedstatuses=publishedstatuses)

@app.route("/surveys/create/", methods=["GET", "POST"])
@app.route("/surveys/<organisation_code>/create/", methods=["GET", "POST"])
def create_survey(organisation_code=None):
    return "You're trying to create a survey"

def get_old_organisation_id(organisation_code='GB-1'):
    old_organisation_file = 'tests/2012_2013_organisation_mapping.csv'

    old_organisation_data = unicodecsv.DictReader(file(old_organisation_file))
    for row in old_organisation_data:
        if row['2013_id'] == organisation_code:
            return row['2012_id']

def get_old_indicators():
    old_indicators_file = 'tests/2012_indicators.csv'
    old_indicators_data = unicodecsv.DictReader(file(old_indicators_file))

    indicator_data = {}
    for row in old_indicators_data:
        if ((row["question_number"]) and (row["2013_indicator_name"])):
            indicator_data[int(row["question_number"])] = row["2013_indicator_name"]
    return indicator_data
    
def get_organisation_results(organisation_code, newindicators):
    old_organisation_id = get_old_organisation_id(organisation_code)
    indicators = get_old_indicators()

    old_results_file = 'tests/2012_results.csv'
    old_results_data = unicodecsv.DictReader(file(old_results_file))

    data = {}

    for d in old_results_data:
        if (d["target_id"] == old_organisation_id):
            try:
                question_id = int(d["question_id"])
                d["newindicator_id"] = indicators[(int(d["question_id"]))]
                data[indicators[(int(d["question_id"]))]] = d
            except KeyError:
                pass
    for indicator in newindicators:
        try:
            print data[indicator.name]
        except KeyError:
            data[indicator.name] = {
                'result': ''
            }
    return data

@app.route("/organisations/<organisation_code>/survey/")
def organisation_survey(organisation_code=None):
    organisation = dqorganisations.organisations(organisation_code)
    survey = dqsurveys.getSurvey(organisation_code)
    return render_template("survey.html", 
                           organisation=organisation,
                           survey=survey)

@app.route("/organisations/<organisation_code>/survey/create/", methods=["GET", "POST"])
def organisation_survey_create(organisation_code=None):
    if request.method=='POST':
        indicators = request.form.getlist('indicator')
        if 'save' in request.form:
            operation = "save"
        elif 'submit' in request.form:
            operation = "submit"
        organisation = dqorganisations.organisations(organisation_code)
        
        #FIXME: basic survey setup needs to go elsewhere

        publishedstatus = [{'name': 'Always',
          'class': 'success'},
         {'name': 'Sometimes',
          'class': 'warning'},
         {'name': 'Not published',
          'class': 'important'}]
        
        for ps in publishedstatus:
            dqsurveys.addPublishedStatus({
                    'name': ps["name"],
                    'publishedstatus_class': ps["class"]
                    })
        
        workflowType = dqsurveys.addWorkflowType({'name': 'creation'})
        workflow = dqsurveys.addWorkflow({
                    'name': 'Researcher',
                    'leadsto': workflowType.id,
                    'workflow_type': workflowType.id
                    })
        currentworkflow_id = workflow.id
        currentworkflow_deadline = datetime.utcnow()

        organisationsurvey = dqsurveys.createSurvey({
                    'organisation_id': organisation.id, 
                    'currentworkflow_id': currentworkflow_id,
                    'currentworkflow_deadline': currentworkflow_deadline,
                    'indicators': indicators
                    })

        for indicator in indicators:
            data = {
                'organisationsurvey_id': organisationsurvey.id,
                'indicator_id': indicator,
                'workflow_id': currentworkflow_id,
                'published_status': request.form.get(indicator+"-published"),
                'published_source': request.form.get(indicator+"-source"),
                'published_comment': request.form.get(indicator+"-comments"),   
                'published_accepted': None
            }
            surveydata = dqsurveys.addSurveyData(data)
        flash('Successfully submitted survey data', 'success')
        return redirect(url_for("organisations", organisation_code=organisation_code))
    else:
        organisation = Organisation.query.filter_by(
            organisation_code=organisation_code).first_or_404()

        indicators = dqindicators.indicators("pwyf2013")
        org_indicators = dqorganisations._organisation_indicators_split(
        organisation, 2)["zero"]
        twentytwelvedata=get_organisation_results(organisation_code, indicators)
        publishedstatuses = dqsurveys.publishedStatus()

        publication_status= {
                        '4': {
                            'text': 'Always published',
                            'class': 'success'
                        },
                        '3':  {
                            'text': 'Sometimes published',
                            'class': 'warning'
                        },
                        '2':  {
                            'text': 'Collected',
                            'class': 'important'
                        },
                        '1':  {
                            'text': 'Not collected',
                            'class': 'inverse'
                        },
                        '0':  {
                            'text': 'Unknown',
                            'class': ''
                        },
                        "": {
                            'text': '',
                            'class': ''
                        }
                    }
        return render_template("survey_create.html", 
                               organisation=organisation,
                               indicators=indicators,
                               org_indicators = org_indicators,
                               twentytwelvedata=twentytwelvedata,
                               publication_status=publication_status,
                               publishedstatuses=publishedstatuses)

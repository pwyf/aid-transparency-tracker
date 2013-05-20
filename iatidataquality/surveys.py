
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file

from flask.ext.login import current_user
from iatidataquality import app
from iatidataquality import db

import os
import sys
import unicodecsv

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from iatidq import dqindicators, dqsurveys, dqorganisations, dqusers
from iatidq.models import *

import usermanagement

@app.route("/surveys/admin/")
@usermanagement.perms_required()
def surveys_admin():
    surveys = dqsurveys.surveys()
    workflows = dqsurveys.workflows()
    publishedstatuses=dqsurveys.publishedStatus()
    admin = usermanagement.check_perms('admin')
    loggedinuser = current_user

    return render_template("surveys/surveys_admin.html", 
                           **locals())

@app.route("/surveys/create/", methods=["GET", "POST"])
@app.route("/surveys/<organisation_code>/create/", methods=["GET", "POST"])
def create_survey(organisation_code=None):
    return "You're trying to create a survey"

def get_old_organisation_id(organisation_code='GB-1'):
    path = app.config["DATA_STORAGE_DIR"]
    old_organisation_file = os.path.join(path, '2012_2013_organisation_mapping.csv')

    old_organisation_data = unicodecsv.DictReader(file(old_organisation_file))
    for row in old_organisation_data:
        if row['2013_id'] == organisation_code:
            return row['2012_id']

def get_old_indicators():
    path = app.config["DATA_STORAGE_DIR"]
    old_indicators_file = os.path.join(path, '2012_indicators.csv')
    old_indicators_data = unicodecsv.DictReader(file(old_indicators_file))

    indicator_data = {}
    for row in old_indicators_data:
        if ((row["question_number"]) and (row["2013_indicator_name"])):
            indicator_data[int(row["question_number"])] = row["2013_indicator_name"]
    return indicator_data
    
def get_organisation_results(organisation_code, newindicators):
    old_organisation_id = get_old_organisation_id(organisation_code)
    indicators = get_old_indicators()

    path = app.config["DATA_STORAGE_DIR"]

    old_results_file = os.path.join(path, '2012_results.csv')
    old_results_data = unicodecsv.DictReader(file(old_results_file))

    data = {}

    for d in old_results_data:
        if d["target_id"] == old_organisation_id:
            try:
                question_id = int(d["question_id"])
                d["newindicator_id"] = indicators[question_id]
                data[indicators[question_id]] = d
            except KeyError:
                pass
    for indicator_name in newindicators:
        try:
            discard = data[indicator_name]
        except KeyError:
            data[indicator_name] = {
                'result': ''
            }
    return data

def completion_percentage(survey):
    stages = ['researcher', 'send', 'donorreview', 'pwyfreview',
              'donorcomments', 'pwyffinal', 'finalised']

    # can ValueError; used to raise NameError
    idx = stages.index(survey.Workflow.name)

    return float(idx + 1) / 7 * 100

@app.route("/organisations/<organisation_code>/survey/")
@usermanagement.perms_required('survey', 'view')
def organisation_survey(organisation_code=None):
    organisation = dqorganisations.organisations(organisation_code)
    # make sure survey exists
    dqsurveys.getOrCreateSurvey({'organisation_id':organisation.id})

    survey = dqsurveys.getSurvey(organisation_code)
    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)
    workflows = dqsurveys.workflows()
    pct_complete = completion_percentage(survey)
    users = dqusers.surveyPermissions(organisation_code)
    admin = usermanagement.check_perms('admin')
    loggedinuser = current_user
       
    return render_template("surveys/survey.html", 
                           **locals())

def getTimeRemainingNotice(deadline):
    remaining = deadline.date() - datetime.utcnow().date()

    if remaining.days > 1:
        return "You have %d days to submit your response." % remaining.days
    else:
        return "Today is the last day for making any changes to your survey."

def __survey_process(organisation, workflow, request, 
                     organisationsurvey, published_accepted):

    indicators = request.form.getlist('indicator')
    print "INDICATORS: ", indicators

    workflow_id = workflow.Workflow.id
    currentworkflow_deadline = organisationsurvey.currentworkflow_deadline

    for indicator in indicators:

        if request.form.get(indicator + "-ordinal_value"):
            published_format= dqsurveys.publishedFormat('document').id
            ordinal_value = request.form.get(indicator + "-ordinal_value")
        elif request.form.get(indicator + "-noformat"):
            published_format= dqsurveys.publishedFormat('document').id
            ordinal_value = None
        else:
            published_format = request.form.get(indicator + "-publishedformat")
            ordinal_value = None

        data = {
            'organisationsurvey_id': organisationsurvey.id,
            'indicator_id': indicator,
            'workflow_id': workflow_id,
            'published_status': request.form.get(indicator+"-published"),
            'published_source': request.form.get(indicator+"-source"),
            'published_comment': request.form.get(indicator+"-comments"),
            'published_format': published_format,
            'published_accepted': published_accepted(indicator),
            'ordinal_value': ordinal_value
        }
        surveydata = dqsurveys.addSurveyData(data)
    
    if 'submit' in request.form:
        if workflow.Workflow.id == organisationsurvey.currentworkflow_id:
        # save data, change currentworkflow_id to leadsto
            dqsurveys.advanceSurvey(organisationsurvey)
            flash('Successfully submitted survey data', 'success')
        else:
            flash("Your survey data was updated.", 'warning')
    else:
        time_remaining_notice = getTimeRemainingNotice(
            organisationsurvey.currentworkflow_deadline)

        flash('Note: your survey has not yet been submitted. '
              + time_remaining_notice, 'warning')

none = lambda i: None
add_agree = lambda indicator: request.form.get(indicator + "-agree")

def _survey_process_collect(organisation, workflow, 
                            request, organisationsurvey):
    return __survey_process(organisation, workflow, 
                            request, organisationsurvey, none)

def _survey_process_review(organisation, workflow, 
                           request, organisationsurvey):
    return __survey_process(organisation, workflow, 
                            request, organisationsurvey, none)

def _survey_process_finalreview(organisation, workflow,
                                request, organisationsurvey):
    return __survey_process(organisation, workflow, request, 
                            organisationsurvey, 
                            add_agree)

def _survey_process_comment(organisation, workflow, 
                            request, organisationsurvey):
    return __survey_process(organisation, workflow, 
                            request, organisationsurvey, 
                            add_agree)

def _survey_process_send(organisation, workflow, request, organisationsurvey):
    indicators = request.form.getlist('indicator')

    #FIXME: need to actually send

    dqsurveys.advanceSurvey(organisationsurvey)
    flash('Successfully sent survey to donor.', 'success')

def get_old_publication_status():
    pses = [
        ('4', 'Always published', 'success'),
        ('3', 'Sometimes published', 'warning'),
        ('2', 'Collected', 'important'),
        ('1', 'Not collected', 'inverse'),
        ('',  'Unknown', '')
        ]
    struct = lambda ps: (ps[0], {
            "text": ps[1], 
            "class": ps[2] 
            })
    return dict(map(struct, pses))


id_tuple = lambda p: (p.id, p)

def organisation_survey_view(organisation_code, workflow, 
                             workflow_name, organisationsurvey, 
                             allowed_to_edit):
    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    # the next line may be being called for its side effects
    dqsurveys.getSurveyData(organisation_code, workflow_name)

    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)

    indicators = dqindicators.indicators("2013 Index")
    org_indicators = dqorganisations._organisation_indicators_split(
        organisation, 2)

    twentytwelvedata=get_organisation_results(
        organisation_code, 
        [i[1]["indicator"]["name"] for i in org_indicators["zero"].items()]
        )

    publishedstatuses = dict(map(id_tuple, dqsurveys.publishedStatus()))
    publishedformats  = dict(map(id_tuple, dqsurveys.publishedFormat()))

    old_publication_status = get_old_publication_status()

    admin = usermanagement.check_perms('admin')
    loggedinuser = current_user

    return render_template(
        "surveys/_survey_%s.html" % workflow.WorkflowType.name,
        **locals())

@app.route("/organisations/<organisation_code>/survey/<workflow_name>/", methods=["GET", "POST"])
def organisation_survey_edit(organisation_code=None, workflow_name=None):
    
    workflow = dqsurveys.workflows(workflow_name)
    if not workflow:
        flash('That workflow does not exist.', 'error')
        return abort(404)

    organisation = dqorganisations.organisations(organisation_code)
    organisationsurvey = dqsurveys.getOrCreateSurvey({
                'organisation_id': organisation.id
                })

    def allowed(method):
        permission_name = "survey_" + workflow_name
        permission_value = {'organisation_code': organisation_code}
        return usermanagement.check_perms(permission_name,
                                          method,
                                          permission_value)
    allowed_to_edit = allowed("edit")
    allowed_to_view = allowed("view")

    def no_permission():
        flash("Sorry, you do not have permission to view that survey", 'error')
        if request.referrer is not None:
            redir_to = request.referrer
        else:
            redir_to = url_for('home')
        return redirect(redir_to)
    
    if not allowed_to_view:
        return no_permission()

    if request.method != 'POST':
        return organisation_survey_view(organisation_code, workflow, workflow_name, organisationsurvey, allowed_to_edit)
    else:
        if not allowed_to_edit:
            return no_permission()

        handlers = {
            "collect": _survey_process_collect,
            "send": _survey_process_send,
            "review": _survey_process_review,
            "comment": _survey_process_comment,
            "finalreview": _survey_process_finalreview
            }

        workflow_name = workflow.WorkflowType.name

        if workflow_name == "send":
            if workflow.Workflow.id == organisationsurvey.currentworkflow_id:
                _survey_process_send(
                    organisation_code, workflow, request, organisationsurvey)
            else:
                flash("Not possible to send survey to donor because it's "
                      "not at the current stage in the workflow. "
                      "Maybe you didn't submit the data, or maybe you "
                      "already sent it to the donor?", 'error')
        elif workflow_name in handlers:
            handlers[workflow_name](
                organisation, workflow, request, organisationsurvey)
        elif workflow_name == 'finalised':
            return "finalised"
        return redirect(url_for("organisations", 
                                organisation_code=organisation_code))


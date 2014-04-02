
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

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from iatidq import dqindicators, dqorganisations, dqusers, donorresponse
import iatidq.survey.data as dqsurveys
import iatidq.survey.mapping
from iatidq.models import *

import usermanagement
from iatidq import util

@app.route("/surveys/admin/")
@usermanagement.perms_required()
def surveys_admin():
    surveys = dqsurveys.surveys()
    workflows = dqsurveys.workflowsAll()
    publishedstatuses=dqsurveys.publishedStatus()
    admin = usermanagement.check_perms('admin')
    loggedinuser = current_user

    return render_template("surveys/surveys_admin.html", 
                           **locals())

@app.route("/surveys/create/", methods=["GET", "POST"])
@app.route("/surveys/<organisation_code>/create/", methods=["GET", "POST"])
def create_survey(organisation_code=None):
    return "You're trying to create a survey"

def completion_percentage(survey):
    stages = ['researcher', 'send', 'donorreview', 'pwyfreview',
              'cso', 'donorcomments', 'pwyffinal', 'finalised']

    # can ValueError; used to raise NameError
    idx = stages.index(survey.Workflow.name)

    return float(idx + 1) / 8 * 100

@app.route("/organisations/<organisation_code>/survey/repair/")
@usermanagement.perms_required('survey', 'view')
def organisation_survey_repair(organisation_code):
    status = dqsurveys.repairSurveyData(organisation_code)
    if status['changes'] == True:
        indicators = ", ".join(status['changed_indicators'])
        flash('Survey successfully repaired indicators '+indicators, 'success')
    else:
        flash('Survey could not be repaired', 'error')
    return redirect(url_for('organisation_survey', organisation_code=organisation_code))
    
@app.route("/organisations/<organisation_code>/survey/")
@usermanagement.perms_required('survey', 'view')
def organisation_survey(organisation_code=None):
    organisation = dqorganisations.organisations(organisation_code)
    # make sure survey exists
    dqsurveys.getOrCreateSurvey({'organisation_id':organisation.id})

    survey = dqsurveys.getSurvey(organisation_code)
    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)
    workflows = dqsurveys.workflowsAll()
    pct_complete = completion_percentage(survey)
    users = dqusers.surveyPermissions(organisation_code)
    admin = usermanagement.check_perms('admin')
    loggedinuser = current_user
    checksurveyOK = dqsurveys.checkSurveyData(organisation_code)

    return render_template("surveys/survey.html", 
                           **locals())

def getTimeRemainingNotice(deadline):
    # Skip this for now
    return ""
    remaining = deadline.date() - datetime.utcnow().date()

    if remaining.days > 1:
        return "You have %d days to submit your response." % remaining.days
    else:
        return "Today is the last day for making any changes to your survey."

def __survey_process(organisation, workflow, request, 
                     organisationsurvey, published_accepted):

    indicators = dqindicators.indicators(app.config["INDICATOR_GROUP"])
    form_indicators = map(int, request.form.getlist('indicator'))

    workflow_id = workflow.Workflow.id
    currentworkflow_deadline = organisationsurvey.currentworkflow_deadline

    for indicator in indicators:
        data = {
            'organisationsurvey_id': organisationsurvey.id,
            'indicator_id': str(indicator.id),
            'workflow_id': workflow_id,
        }

        if indicator.id not in form_indicators:
            # It's an IATI indicator...
            data['published_status'] = dqsurveys.publishedStatusByName('always').id
            data['published_format'] = dqsurveys.publishedFormatByName('iati').id
        else:
            data['published_status'] = request.form.get(str(indicator.id)+"-published")

            if indicator.indicator_noformat:
                data['published_format'] = dqsurveys.publishedFormatByName('document').id
            else:
                data['published_format'] = request.form.get(str(indicator.id) + "-publishedformat")      

            if indicator.indicator_ordinal:
                data['ordinal_value'] = request.form.get(str(indicator.id) + "-ordinal_value")
            else:
                data['ordinal_value'] = None

        data['published_comment'] = request.form.get(str(indicator.id)+"-comments")
        data['published_source'] = request.form.get(str(indicator.id)+"-source")
        data['published_accepted'] = published_accepted(str(indicator.id))
        
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
        ('',  'Unknown', ''),
        ('iati', 'Published to IATI', 'success'),
        ('always', 'Always published', 'success'),
        ('sometimes', 'Sometimes published', 'warning'),
        ('not published', 'Not published', 'important'),
        ]
    struct = lambda ps: (ps[0], {
            "text": ps[1], 
            "class": ps[2] 
            })
    return dict(map(struct, pses))

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

id_tuple = lambda p: (p.id, p)

def organisation_survey_view(organisation_code, workflow, 
                             workflow_name, organisationsurvey, 
                             allowed_to_edit):
    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    # the next line may be being called for its side effects
    dqsurveys.getSurveyData(organisation_code, workflow_name)

    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)
    try:
        print surveydata['cso']
    except Exception:
        pass

    indicators = dqindicators.indicators(app.config["INDICATOR_GROUP"])
    org_indicators = dqorganisations._organisation_indicators_split(
        organisation, 2)

    twentytwelvedata = iatidq.survey.mapping.get_organisation_results(
        organisation_code, 
        [i[1]["indicator"]["name"] for i in org_indicators["zero"].items()]
        )

    publishedstatuses = dict(map(id_tuple, dqsurveys.publishedStatus()))
    publishedformats  = dict(map(id_tuple, dqsurveys.publishedFormatAll()))
    years = get_ordinal_values_years()
    year_data = dict(years)
    years.pop()
    donorresponses = donorresponse.RESPONSE_IDS

    old_publication_status = get_old_publication_status()

    admin = usermanagement.check_perms('admin')
    loggedinuser = current_user

    org_indicators['commitment'] = util.resort_sqlalchemy_indicator(org_indicators['commitment'])
    org_indicators['zero'] = util.resort_dict_indicator(org_indicators['zero'])

    return render_template(
        "surveys/_survey_%s.html" % workflow.WorkflowType.name,
        **locals())

@app.route("/organisations/<organisation_code>/survey/<workflow_name>/", methods=["GET", "POST"])
def organisation_survey_edit(organisation_code=None, workflow_name=None):
    
    workflow = dqsurveys.workflowByName(workflow_name)
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
        # If not logged in, redirect to login page
        
        if not current_user.is_authenticated():
            flash('You must log in to access that page.', 'error')
            return redirect(url_for('login', next=request.path))

        # Otherwise, redirect to previous page and warn user
        # they don't have permissions to access the survey.
        flash("Sorry, you do not have permission to view that survey", 'error')
        if request.referrer is not None:
            redir_to = request.referrer
        else:
            redir_to = url_for('home')
        return redirect(redir_to)
    
    if not allowed_to_view:
        return no_permission()

    if request.method != 'POST':
        return organisation_survey_view(
            organisation_code, workflow, 
            workflow_name, organisationsurvey, allowed_to_edit)

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



#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db, app

from sqlalchemy import func


import iatidq.summary

import iatidq.models as models
import csv
import iatidq.util as util
import unicodecsv
import datetime
import iatidq.dqindicators as dqindicators
import iatidq.dqorganisations as dqorganisations

class NoSuchSurvey(Exception): pass

def getIDorNone(sqlalchemy_object):
    if sqlalchemy_object is not None:
        return sqlalchemy_object.Workflow.id
    else:
        return None

def getSurveyById(organisation_id):
    return models.OrganisationSurvey.query.filter_by(
        organisation_id=organisation_id).first()

def getOrCreateSurvey(data):
    checkS = getSurveyById(data["organisation_id"])

    if checkS:
        return checkS
    with db.session.begin():
        newS = models.OrganisationSurvey()

        workflow = workflowByName('researcher')
        currentworkflow_id = workflow.Workflow.id
        deadline_days = datetime.timedelta(days=workflow.Workflow.duration)

        currentworkflow_deadline = datetime.datetime.utcnow()+deadline_days

        newS.setup(
            organisation_id = data["organisation_id"],
            currentworkflow_id = currentworkflow_id,
            currentworkflow_deadline = currentworkflow_deadline
            )
        db.session.add(newS)
    return newS

def addSurveyData(data):
    checkSD = models.OrganisationSurveyData.query.filter_by(
        organisationsurvey_id=data["organisationsurvey_id"], 
        workflow_id=data["workflow_id"], 
        indicator_id=data["indicator_id"]).first()

    with db.session.begin():
        if not checkSD:
            newSD = models.OrganisationSurveyData()
            newSD.setup(
                organisationsurvey_id = data["organisationsurvey_id"],
                workflow_id = data["workflow_id"],
                indicator_id = data["indicator_id"],
                published_status = data["published_status"],
                published_source = data["published_source"],
                published_comment = data["published_comment"],
                published_accepted = data["published_accepted"],
                published_format = data.get("published_format"),
                ordinal_value = data.get("ordinal_value")
                )
            db.session.add(newSD)
            return newSD
        else:
            checkSD.organisationsurvey_id = data["organisationsurvey_id"],
            checkSD.workflow_id = data["workflow_id"],
            checkSD.indicator_id = data["indicator_id"],
            checkSD.published_status = data["published_status"],
            checkSD.published_source = data["published_source"],
            checkSD.published_comment = data["published_comment"],
            checkSD.published_accepted = data["published_accepted"],
            checkSD.published_format = data.get("published_format"),
            checkSD.ordinal_value = data.get("ordinal_value")
            db.session.add(checkSD)
            return checkSD

def deleteSurveyData(organisation_code):
    with db.session.begin():
        for result in models.OrganisationSurveyData.query.join(
            models.OrganisationSurvey
            ).join(
            models.Organisation
            ).filter(
            models.Organisation.organisation_code==organisation_code).all():

            db.session.delete(result)
    with db.session.begin():
        survey = models.OrganisationSurvey.query.join(
            models.Organisation
            ).filter(
            models.Organisation.organisation_code==organisation_code).first()
        if not survey:
            raise NoSuchSurvey
        db.session.delete(survey) 


def publishedStatus():
    checkPS = models.PublishedStatus.query.all()
    return checkPS

def publishedStatusByName(name):
    checkPS = models.PublishedStatus.query.filter(
        models.PublishedStatus.name == name
        ).first()
    return checkPS

def publishedFormatByName(name):
    checkPF = models.PublishedFormat.query.filter(
        models.PublishedFormat.name == name
        ).first()
    return checkPF

def publishedFormatAll():
    checkPF = models.PublishedFormat.query.filter(
        models.PublishedFormat.name != 'document'
        ).filter(
        models.PublishedFormat.name != 'iati'
        ).all()
    return checkPF

def publishedFormatsAll():
    checkPF = models.PublishedFormat.query.all()
    return checkPF

def surveys():
    surveys = db.session.query(models.OrganisationSurvey,
                               models.Workflow,
                               models.Organisation
            ).join(models.Workflow
            ).join(models.Organisation
            ).all()
    return surveys

def getSurvey(organisation_code):
    survey = db.session.query(models.OrganisationSurvey,
                              models.Workflow).filter(models.Organisation.organisation_code==organisation_code
            ).join(models.Workflow
            ).join(models.Organisation
            ).first()
    return survey

def getSurveyData(organisation_code, workflow_name):
    surveyData = db.session.query(models.OrganisationSurveyData,
                                  models.PublishedStatus,
                                  models.PublishedFormat
        ).filter(models.Organisation.organisation_code==organisation_code
        ).outerjoin(models.PublishedStatus
        ).outerjoin(models.PublishedFormat
        ).join(models.OrganisationSurvey
        ).join(models.Organisation
        ).all()        
    surveyDataByIndicator = dict(map(lambda x: (x.OrganisationSurveyData.indicator_id, x), surveyData))
    return surveyDataByIndicator

def getSurveyDataAllWorkflows(organisation_code):
    surveyData = db.session.query(models.OrganisationSurveyData,
                                  models.PublishedStatus,
                                  models.PublishedFormat,
                                  models.Workflow
                ).filter(models.Organisation.organisation_code==organisation_code
                ).outerjoin(models.PublishedStatus
                ).outerjoin(models.PublishedFormat
                ).join(models.OrganisationSurvey
                ).join(models.Organisation
                ).join(models.Workflow, (models.OrganisationSurveyData.workflow_id==models.Workflow.id)
                ).all()

    workflows = set(map(lambda x: x.Workflow.name, surveyData))
    indicators = set(map(lambda x: x.OrganisationSurveyData.indicator_id, surveyData))
    out = {}
    for w in workflows:
        out[w] = {}
        for i in indicators:
            out[w][i] = {}
    for data in surveyData:
        out[data.Workflow.name][data.OrganisationSurveyData.indicator_id] = data
    return out

def addPublishedFormat(data):
    checkPF = models.PublishedFormat.query.filter_by(name=data["name"]
                ).first()
    if checkPF:
        return checkPF
    with db.session.begin():
        newPF = models.PublishedFormat()
        newPF.setup(
            name = data["name"],
            title = data["title"],
            format_class = data["format_class"],
            format_value = data["format_value"]
            )
        db.session.add(newPF)
    return newPF

def addPublishedStatus(data):
    checkPS = models.PublishedStatus.query.filter_by(name=data["name"]
                ).first()
    if checkPS:
        return checkPS
    with db.session.begin():
        newPS = models.PublishedStatus()
        newPS.setup(
            name = data["name"],
            title = data["title"],
            publishedstatus_class = data["publishedstatus_class"],
            publishedstatus_value = data["publishedstatus_value"]
            )
        db.session.add(newPS)
    return newPS

def addWorkflowType(data):
    checkWT = models.WorkflowType.query.filter_by(name=data["name"]
                ).first()
    if checkWT:
        return checkWT
    with db.session.begin():
        newWT = models.WorkflowType()
        newWT.setup(
            name = data["name"]
            )
        db.session.add(newWT)
    return newWT

def addWorkflowType(data):
    checkWT = models.WorkflowType.query.filter_by(name=data["name"]
                ).first()
    if checkWT:
        return checkWT
    with db.session.begin():
        newWT = models.WorkflowType()
        newWT.setup(
            name = data["name"]
            )
        db.session.add(newWT)
    return newWT

def workflowByName(workflow_name):
    checkW = db.session.query(models.Workflow,
                              models.WorkflowType
                              ).filter_by(
        name=workflow_name
        ).join(models.WorkflowType, 
               models.WorkflowType.id==models.Workflow.workflow_type
               ).first()
    if checkW:
        return checkW
    return None

def workflowsAll():
    checkW = db.session.query(models.Workflow,
                              models.WorkflowType
                              ).join(
        models.WorkflowType, 
        models.WorkflowType.id==models.Workflow.workflow_type
        ).order_by(models.Workflow.id).all()
    if checkW:
        return checkW
    return None

def workflowTypeByName(workflowtype_name):
    checkWT = models.WorkflowType.query.filter_by(name=workflowtype_name
                                                  ).first()

    if checkWT:
        return checkWT
    return None

def workflow_by_id(workflow_id):
    checkW = db.session.query(models.Workflow
            ).filter_by(id=workflow_id
            ).first()
    return checkW

def advanceSurvey(organisationsurvey):
    # receives an OrganisationSurvey object
    # updates currentworkflow_id to leadsto value
    checkS=models.OrganisationSurvey.query.filter_by(id=organisationsurvey.id
            ).first()
    checkW = workflow_by_id(organisationsurvey.currentworkflow_id)
    if not (checkS and checkW):
        return False
    with db.session.begin():
        checkS.currentworkflow_id=checkW.leadsto
        db.session.add(checkS)
    # FIXME
    # return None instead of False - the test for this is potentially 
    # misleading

def addWorkflow(data):
    checkW = models.Workflow.query.filter_by(name=data["name"]
                ).first()
    if checkW:
        return checkW
    with db.session.begin():
        newW = models.Workflow()
        newW.setup(
            name = data["name"],
            leadsto = data["leadsto"],
            workflow_type = data["workflow_type"],
            duration = data["duration"],
            title = data["title"]
            )
        db.session.add(newW)
    return newW

def updateWorkflow(data):
    checkW = models.Workflow.query.filter_by(name=data["name"]
                ).first()
    if not checkW:
        return None
    with db.session.begin():
        checkW.name = data["name"],
        checkW.title = data["title"],
        checkW.workflow_type = data["workflow_type"],
        checkW.leadsto = data["leadsto"],
        checkW.duration = data["duration"]
        db.session.add(checkW)
    return checkW

def repairSurveyData(organisation_code):
    # for each currently active stage of the workflow
    # check if there is an indicator at each stage of the workflow
    # if not, then create one
    changes = False
    changed_indicators = []

    allindicators = dqindicators.indicators(app.config["INDICATOR_GROUP"])
    allindicators = map(lambda x: x.id, allindicators)
  
    organisation = dqorganisations.organisations(organisation_code)
    org_indicators = dqorganisations._organisation_indicators_split(organisation, 2)["zero"]

    survey = getSurvey(organisation_code).OrganisationSurvey

    survey_data = getSurveyDataAllWorkflows(organisation_code)
    for workflow_name, v in survey_data.items():
        workflow = workflowByName(workflow_name)
        survey_indicators = v.keys()
        for indicator, indicatordata in org_indicators.items():
            if indicator not in survey_indicators:
                print "NOT FOUND:", indicator
                data = {
                    'organisationsurvey_id' : survey.id,
                    'workflow_id' : workflow.Workflow.id,
                    'indicator_id' : indicator,
                    'published_status' : None,
                    'published_source' : None,
                    'published_comment' : None,
                    'published_accepted' : None,
                    'published_format' : None,
                    'ordinal_value' : None
                }
                addSurveyData(data)
                changes = True
                changed_indicators.append(indicatordata["indicator_name"])
            else:
                print "FOUND:", indicator
    return {'changes': changes, 'changed_indicators': changed_indicators}

def checkSurveyData(organisation_code):
    # for each currently active stage of the workflow
    # check if there is an indicator at each stage of the workflow
    # if not, then create one

    allindicators = dqindicators.indicators(app.config["INDICATOR_GROUP"])
    allindicators = map(lambda x: x.id, allindicators)
  
    organisation = dqorganisations.organisations(organisation_code)
    org_indicators = dqorganisations._organisation_indicators_split(organisation, 2)["zero"].keys()

    survey = getSurvey(organisation_code).OrganisationSurvey

    survey_data = getSurveyDataAllWorkflows(organisation_code)
    for workflow_name, v in survey_data.items():
        workflow = workflowByName(workflow_name)
        survey_indicators = v.keys()
        for indicator in org_indicators:
            if indicator not in survey_indicators:
                return False
    return True 


def get_survey_data_and_workflow(organisation_survey, surveydata):
    # When provided with a particular organisation survey,
    # this function takes the current workflow of that survey,
    # and returns the relevant PWYF stage plus the existing
    # donor stage name
    data = {
        "donorreview": ("researcher", 'donorreview'),
        "pwyfreview": ("researcher", 'donorreview'),
        "cso": ("pwyfreview", 'donorreview'),
        "pwyffinal": ("pwyfreview", 'donorcomments'),
        "donorcomments": ("pwyffinal", 'donorcomments'),
        "finalised": ("pwyffinal", 'finalised')
        }
           
    if organisation_survey:
        workflow_name = organisation_survey.Workflow.name
        if workflow_name in data:
            key, phase = data[workflow_name]
            return (surveydata[key], phase)
    return (None, None)

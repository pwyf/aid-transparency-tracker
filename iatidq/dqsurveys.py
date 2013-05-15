
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

from sqlalchemy import func

import summary

import models
import csv
import util
import unicodecsv
import datetime

def getIDorNone(sqlalchemy_object):
    if sqlalchemy_object is not None:
        return sqlalchemy_object.Workflow.id
    else:
        return None

def setupSurvey():
    the_publishedstatuses = [
     {'name': 'always',
      'title': 'Always',
      'publishedstatus_class': 'success',
      'publishedstatus_value': 1 },
     {'name': 'sometimes',
      'title': 'Sometimes',
      'publishedstatus_class': 'warning',
      'publishedstatus_value': 0},
     {'name': 'not published',
      'title': 'Not published',
      'publishedstatus_class': 'important',
      'publishedstatus_value': 0}]

    for the_publishedstatus in the_publishedstatuses:
        addPublishedStatus(the_publishedstatus)

    the_publishedformat = [{
      'name': 'machine-readable',
      'title': 'Machine-readable (CSV, Excel)',
      'format_class': 'success',
      'format_value': 1.0 },
     {'name': 'website',
      'title': 'Website',
      'format_class': 'warning',
      'format_value': 0.6666},
     {'name': 'pdf',
      'title': 'PDF',
      'format_class': 'important',
      'format_value': 0.3333},
     {'name': 'document',
      'title': 'Document',
      'format_class': 'success',
      'format_value': 1.0}]

    for the_publishedformat in the_publishedformat:
        addPublishedFormat(the_publishedformat)

    # workflowtypes define what sort of template is
    # displayed to the user at that workflow stage

    the_workflowTypes = [
    {'name': 'collect',
     'title': 'Initial data collection'},
    {'name': 'send',
     'title': 'Send to next step'},
    {'name': 'review',
     'title': 'Review initial assessment'},
    {'name': 'finalreview',
     'title': "Review donor's review"},
    {'name': 'comment',
     'title': 'Agree/disagree and provide comments on current assessment'},
    {'name': 'agreereview',
     'title': 'Review all comments and reviews and make final decision'},
    {'name': 'finalised',
     'title': 'Survey finalised'}
    ]
    for the_workflowType in the_workflowTypes:    
        addWorkflowType(the_workflowType)
    
    # Workflows need to be created and then 
    # updated with the leadsto attribute.
    # They define what happens to the survey
    # at each step.

    the_workflows = [
    {'name': 'researcher',
     'title': 'Researcher',
     'workflow_type': workflowTypes('collect').id,
     'leadsto': getIDorNone(workflows('send')),
     'duration': 14},
    {'name': 'send',
     'title': 'Send to donor',
     'workflow_type': workflowTypes('send').id,
     'leadsto': getIDorNone(workflows('donorreview')),
     'duration': 2},
    {'name': 'donorreview',
     'title': 'Donor review',
     'workflow_type': workflowTypes('review').id,
     'leadsto': getIDorNone(workflows('pwyfreview')),
     'duration': 21},
    {'name': 'pwyfreview',
     'title': 'PWYF review',
     'workflow_type': workflowTypes('review').id,
     'leadsto': getIDorNone(workflows('donorcomments')),
     'duration': 14},
    {'name': 'donorcomments',
     'title': 'Donor comments',
     'workflow_type': workflowTypes('comment').id,
     'leadsto': getIDorNone(workflows('pwyffinal')),
     'duration': 7},
    {'name': 'pwyffinal',
     'title': 'PWYF final review',
     'workflow_type': workflowTypes('finalreview').id,
     'leadsto': getIDorNone(workflows('finalised')),
     'duration': 14},
    {'name': 'finalised',
     'title': 'Survey finalised',
     'workflow_type': workflowTypes('finalised').id,
     'leadsto': None,
     'duration': None},
    {'name': 'cso',
     'title': 'CSO review',
     'workflow_type': workflowTypes('comment').id,
     'leadsto': None,
     'duration': None}
    ]
    for the_workflow in the_workflows:
        addWorkflow(the_workflow)

    # This will correct leadsto values
    for the_workflow in the_workflows:
        updateWorkflow(the_workflow)

def getOrCreateSurvey(data):
    checkS = models.OrganisationSurvey.query.filter_by(organisation_id=data["organisation_id"]).first()
    if not checkS:
        with db.session.begin():
            newS = models.OrganisationSurvey()

            workflow = workflows('researcher')
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
    else:
        return checkS

def addSurveyData(data):
    checkSD = models.OrganisationSurveyData.query.filter_by(
        organisationsurvey_id=data["organisationsurvey_id"], 
        workflow_id=data["workflow_id"], 
        indicator_id=data["indicator_id"]).first()

    if not checkSD:
        with db.session.begin():
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
        with db.session.begin():
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
        db.session.delete(survey) 


def publishedStatus():
    checkPS = models.PublishedStatus.query.all()
    return checkPS

def publishedFormat(name=None):
    if name is not None:
        checkPF = models.PublishedFormat.query.filter(
                models.PublishedFormat.name == name
                ).first()
    else:
        checkPF = models.PublishedFormat.query.filter(
                models.PublishedFormat.name != 'document'
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

def getSurveyData(organisation_code, workflow_name=None):
    if workflow_name:
        surveyData = db.session.query(models.OrganisationSurveyData,
                                      models.PublishedStatus,
                                      models.PublishedFormat
        ).filter(models.Organisation.organisation_code==organisation_code
        ).filter(models.Workflow.name==workflow_name
        ).outerjoin(models.PublishedStatus
        ).outerjoin(models.PublishedFormat
        ).join(models.OrganisationSurvey
        ).join(models.Organisation
        ).join(models.Workflow, (models.OrganisationSurveyData.workflow_id==models.Workflow.id)
        ).all()
    else:
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
    if not checkPF:
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
    else:
        return checkPF

def addPublishedStatus(data):
    checkPS = models.PublishedStatus.query.filter_by(name=data["name"]
                ).first()
    if not checkPS:
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
    else:
        return checkPS

def addWorkflowType(data):
    checkWT = models.WorkflowType.query.filter_by(name=data["name"]
                ).first()
    if not checkWT:
        with db.session.begin():
            newWT = models.WorkflowType()
            newWT.setup(
                name = data["name"]
                )
            db.session.add(newWT)
        return newWT
    else:
        return checkWT

def addWorkflowType(data):
    checkWT = models.WorkflowType.query.filter_by(name=data["name"]
                ).first()
    if not checkWT:
        with db.session.begin():
            newWT = models.WorkflowType()
            newWT.setup(
                name = data["name"]
                )
            db.session.add(newWT)
        return newWT
    else:
        return checkWT

def workflows(workflow_name=None):
    if workflow_name:
        checkW = db.session.query(models.Workflow,
                                  models.WorkflowType
            ).filter_by(name=workflow_name
            ).join(models.WorkflowType, models.WorkflowType.id==models.Workflow.workflow_type
            ).first()
    else:
        checkW = db.session.query(models.Workflow,
                                  models.WorkflowType
            ).join(models.WorkflowType, models.WorkflowType.id==models.Workflow.workflow_type
            ).order_by(models.Workflow.id).all()
    if checkW:
        return checkW
    else:
        return None

def workflowTypes(workflowtype_name=None):
    if workflowtype_name:
        checkWT = models.WorkflowType.query.filter_by(name=workflowtype_name
            ).first()
    else:
        checkWT = models.WorkflowType.query.all()
    if checkWT:
        return checkWT
    else:
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
    if checkS and checkW:
        with db.session.begin():
            checkS.currentworkflow_id=checkW.leadsto
            db.session.add(checkS)
    else:
        return False

def addWorkflow(data):
    checkW = models.Workflow.query.filter_by(name=data["name"]
                ).first()
    if not checkW:
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
    else:
        return checkW

def updateWorkflow(data):
    checkW = models.Workflow.query.filter_by(name=data["name"]
                ).first()
    if checkW:
        with db.session.begin():
            checkW.name = data["name"],
            checkW.title = data["title"],
            checkW.workflow_type = data["workflow_type"],
            checkW.leadsto = data["leadsto"],
            checkW.duration = data["duration"]
            db.session.add(checkW)
        return checkW
    else:
        return None

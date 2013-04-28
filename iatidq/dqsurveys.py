
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

def getIDorNone(sqlalchemy_object):
    if sqlalchemy_object is not None:
        return sqlalchemy_object.Workflow.id
    else:
        return None

def setupSurvey():
    the_publishedstatuses = [{'name': 'Always',
      'publishedstatus_class': 'success'},
     {'name': 'Sometimes',
      'publishedstatus_class': 'warning'},
     {'name': 'Not published',
      'publishedstatus_class': 'important'}]

    for the_publishedstatus in the_publishedstatuses:
        addPublishedStatus(the_publishedstatus)

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
        newS = models.OrganisationSurvey()

        workflow = workflows('collect')
        currentworkflow_id = workflow.id
        deadline_days = datetime.timedelta(days=workflow.duration)

        currentworkflow_deadline = datetime.utcnow()+deadline_days

        newS.setup(
            organisation_id = data["organisation_id"],
            currentworkflow_id = currentworkflow_id,
            currentworkflow_deadline = currentworkflow_deadline
        )
        db.session.add(newS)
        db.session.commit()
        return newS
    else:
        return checkS

def addSurveyData(data):
    checkSD = models.OrganisationSurveyData.query.filter_by(organisationsurvey_id=data["organisationsurvey_id"], workflow_id=data["workflow_id"], indicator_id=data["indicator_id"]).first()
    if not checkSD:
        newSD = models.OrganisationSurveyData()
        newSD.setup(
            organisationsurvey_id = data["organisationsurvey_id"],
            workflow_id = data["workflow_id"],
            indicator_id = data["indicator_id"],
            published_status = data["published_status"],
            published_source = data["published_source"],
            published_comment = data["published_comment"],
            published_accepted = data["published_accepted"]
        )
        db.session.add(newSD)
        db.session.commit()
        return newSD
    else:
        return False

def publishedStatus():
    checkPS = models.PublishedStatus.query.all()
    return checkPS

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

def getSurveyData(organisation_code):
    surveyData = models.OrganisationSurveyData.query.filter(models.Organisation.organisation_code==organisation_code
            ).join(models.OrganisationSurvey
            ).join(models.Organisation
            ).all()
    surveyDataByIndicator = dict(map(lambda x: (x.indicator_id, x), surveyData))
    return surveyDataByIndicator

def addPublishedStatus(data):
    checkPS = models.PublishedStatus.query.filter_by(name=data["name"]
                ).first()
    if not checkPS:
        newPS = models.PublishedStatus()
        newPS.setup(
            name = data["name"],
            publishedstatus_class = data["publishedstatus_class"]
        )
        db.session.add(newPS)
        db.session.commit()
        return newPS
    else:
        return checkPS

def addWorkflowType(data):
    checkWT = models.WorkflowType.query.filter_by(name=data["name"]
                ).first()
    if not checkWT:
        newWT = models.WorkflowType()
        newWT.setup(
            name = data["name"]
        )
        db.session.add(newWT)
        db.session.commit()
        return newWT
    else:
        return checkWT

def addWorkflowType(data):
    checkWT = models.WorkflowType.query.filter_by(name=data["name"]
                ).first()
    if not checkWT:
        newWT = models.WorkflowType()
        newWT.setup(
            name = data["name"]
        )
        db.session.add(newWT)
        db.session.commit()
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
            ).all()
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
        checkS.currentworkflow_id=checkW.leadsto
        db.session.add(checkS)
        db.session.commit()
    else:
        return False

def addWorkflow(data):
    checkW = models.Workflow.query.filter_by(name=data["name"]
                ).first()
    if not checkW:
        newW = models.Workflow()
        newW.setup(
            name = data["name"],
            leadsto = data["leadsto"],
            workflow_type = data["workflow_type"],
            duration = data["duration"]
        )
        db.session.add(newW)
        db.session.commit()
        return newW
    else:
        return checkW

def updateWorkflow(data):
    checkW = models.Workflow.query.filter_by(name=data["name"]
                ).first()
    if checkW:
        checkW.name = data["name"],
        checkW.leadsto = data["leadsto"],
        checkW.workflow_type = data["workflow_type"],
        checkW.duration = data["duration"]
        db.session.add(checkW)
        db.session.commit()
        return checkW
    else:
        return None

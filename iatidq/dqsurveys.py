
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

def createSurvey(data):
    checkS = models.OrganisationSurvey.query.filter_by(organisation_id=data["organisation_id"]).first()
    if not checkS:
        newS = models.OrganisationSurvey()
        newS.setup(
            organisation_id = data["organisation_id"],
            currentworkflow_id = data["currentworkflow_id"],
            currentworkflow_deadline = data["currentworkflow_deadline"]
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

def addWorkflow(data):
    checkW = models.Workflow.query.filter_by(name=data["name"]
                ).first()
    if not checkW:
        newW = models.Workflow()
        newW.setup(
            name = data["name"],
            leadsto = data["leadsto"],
            workflow_type = data["workflow_type"]
        )
        db.session.add(newW)
        db.session.commit()
        return newW
    else:
        return checkW

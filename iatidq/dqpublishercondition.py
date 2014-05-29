
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db
import models

def configure_organisation_condition(pc, request):
    with db.session.begin():
        pc.description = request.form['description']
        pc.organisation_id = int(request.form['organisation_id'])
        pc.test_id = int(request.form['test_id'])
        pc.operation = int(request.form['operation'])
        pc.condition = request.form['condition']
        pc.condition_value = request.form['condition_value']
        pc.file = request.form['file']
        pc.line = int(request.form['line'])
        pc.active = bool(request.form['active'])
        db.session.add(pc)

def get_publisher_condition(pc_id):
    return db.session.query(
            models.OrganisationCondition.id,
            models.OrganisationCondition.description,
            models.OrganisationCondition.operation,
            models.OrganisationCondition.condition,
            models.OrganisationCondition.condition_value,
            models.Organisation.organisation_name.label("organisation_name"),
            models.Organisation.organisation_code.label("organisation_code"),
            models.Organisation.id.label("organisation_id"),
            models.Test.name.label("test_name"),    
            models.Test.description.label("test_description"),
            models.Test.id.label("test_id")
            ).filter_by(id=pc_id
                        ).join(models.Organisation, models.Test).first()

def get_publisher_conditions():
    return db.session.query(
            models.OrganisationCondition.id,
            models.OrganisationCondition.description,
            models.Organisation.organisation_name.label("organisation_name"),
            models.Organisation.organisation_code.label("organisation_code"),
            models.Organisation.id.label("organisation_id"),
            models.Test.name.label("test_name"),    
            models.Test.description.label("test_description"),
            models.Test.id.label("test_id")
            ).order_by(
            models.OrganisationCondition.id
            ).join(models.Organisation, models.Test
                   ).all()

def get_publisher_feedback():
    return db.session.query(
        models.OrganisationConditionFeedback,
        models.Organisation
        ).join(models.Organisation
        ).all()

def delete_publisher_condition(id):
    pc = db.session.query(
        models.OrganisationCondition
        ).filter(
        models.OrganisationCondition.id==id
        ).first()
    with db.session.begin():
        db.session.delete(pc)

def delete_publisher_feedback(feedback):
    with db.session.begin():
        for fb in feedback:
            db.session.delete(fb.OrganisationConditionFeedback)

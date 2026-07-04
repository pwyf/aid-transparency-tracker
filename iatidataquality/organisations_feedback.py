
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import render_template, flash, request, redirect, url_for
from flask_login import current_user

from . import usermanagement
from iatidq import dqorganisations, models


def organisation_feedback(organisation_code=None):
    if (organisation_code is not None):
        organisation = models.Organisation.where(organisation_code=organisation_code).first()
        if (request.method == "POST"):
            for condition in request.form.getlist('feedback'):
                data = {
                        'organisation_id': organisation.id,
                        'uses': request.form['uses'+condition],
                        'element': request.form['element'+condition],
                        'where': request.form['where'+condition]
                }
                result = dqorganisations.addFeedback(data)
                if result:
                    flash('Successfully added condition.', 'success')
                else:
                    flash("This condition has already been added.", 'warning')

        existing_feedback = models.OrganisationConditionFeedback.query.filter_by(
            organisation_id=organisation.id
        ).all()
        return render_template(
            "organisation_feedback.html",
            organisation=organisation,
            existing_feedback=existing_feedback,
            admin=usermanagement.check_perms('admin'),
            loggedinuser=current_user)
    else:
        flash('No organisation supplied', 'danger')
        return redirect(url_for('get_organisations'))


def delete_org_feedback(organisation_code, feedback_id):
    organisation = models.Organisation.where(organisation_code=organisation_code).first()
    if organisation is None:
        flash('Organisation not found', 'danger')
        return redirect(url_for('get_organisations'))
    feedback = models.OrganisationConditionFeedback.query.filter_by(
        id=feedback_id, organisation_id=organisation.id
    ).first()
    if feedback is None:
        flash('Condition not found', 'danger')
    else:
        dqorganisations.deleteFeedback(feedback_id)
        flash('Condition deleted.', 'success')
    return redirect(url_for('organisation_feedback', organisation_code=organisation_code))

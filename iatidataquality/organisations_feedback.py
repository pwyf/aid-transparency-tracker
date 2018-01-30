
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import render_template, flash, request, redirect, url_for
from flask_login import current_user

from . import app, usermanagement
from iatidq import dqorganisations, models


@app.route("/organisations/<organisation_code>/feedback/", methods=['POST', 'GET'])
@usermanagement.perms_required('organisation_feedback', 'create')
def organisations_feedback(organisation_code=None):
    if (organisation_code is not None):
        organisation = models.Organisation.where(organisation_code=organisation_code).first()
        if (request.method=="POST"):
            for condition in request.form.getlist('feedback'):
                data = {
                        'organisation_id': organisation.id,
                        'uses': request.form['uses'+condition],
                        'element': request.form['element'+condition],
                        'where': request.form['where'+condition]
                }
                if dqorganisations.addFeedback(data):
                    flash('Successfully added condition.', 'success')
                else:
                    flash("Couldn't add condition.", 'danger')

        return render_template("organisation_feedback.html",
             organisation=organisation,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)
    else:
        flash('No organisation supplied', 'danger')
        return redirect(url_for('organisations'))


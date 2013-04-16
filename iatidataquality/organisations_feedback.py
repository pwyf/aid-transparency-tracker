
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file
import StringIO
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
from sqlalchemy import func
from datetime import datetime

from iatidataquality import app
from iatidataquality import db

import os
import sys
import json

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from iatidq import models, dqdownload, dqregistry, dqindicators, dqorganisations, dqpackages
import aggregation

import StringIO
import unicodecsv
import tempfile
import spreadsheet

test_list_location = "tests/activity_tests.csv"

@app.route("/organisations/<organisation_code>/feedback/", methods=['POST', 'GET'])
def organisations_feedback(organisation_code=None):
    if (organisation_code is not None):
        organisation = dqorganisations.organisations(organisation_code)
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
                    flash("Couldn't add condition.", 'error')
        
        return render_template("organisation_feedback.html", organisation=organisation)
    else:
        flash('No organisation supplied', 'error')
        return redirect(url_for('organisations'))


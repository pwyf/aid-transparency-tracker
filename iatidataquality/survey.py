
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

from iatidq import dqorganisations, dqindicators
import aggregation

from iatidq.models import *

import StringIO
import unicodecsv

def get_old_organisation_id(organisation_code='GB-1'):
    old_organisation_file = 'tests/2012_2013_organisation_mapping.csv'

    old_organisation_data = unicodecsv.DictReader(file(old_organisation_file))
    for row in old_organisation_data:
        if row['2013_id'] == organisation_code:
            return row['2012_id']

def get_old_indicators():
    old_indicators_file = 'tests/2012_indicators.csv'
    old_indicators_data = unicodecsv.DictReader(file(old_indicators_file))

    indicator_data = {}
    for row in old_indicators_data:
        if ((row["question_number"]) and (row["2013_indicator_name"])):
            indicator_data[int(row["question_number"])] = row["2013_indicator_name"]
    return indicator_data
    
def get_organisation_results(organisation_code, newindicators):
    old_organisation_id = get_old_organisation_id(organisation_code)
    indicators = get_old_indicators()

    old_results_file = 'tests/2012_results.csv'
    old_results_data = unicodecsv.DictReader(file(old_results_file))

    data = {}

    for d in old_results_data:
        if (d["target_id"] == old_organisation_id):
            try:
                question_id = int(d["question_id"])
                d["newindicator_id"] = indicators[(int(d["question_id"]))]
                data[indicators[(int(d["question_id"]))]] = d
            except KeyError:
                pass
    for indicator in newindicators:
        try:
            print data[indicator.name]
        except KeyError:
            data[indicator.name] = {
                'result': ''
            }
    return data

@app.route("/organisations/<organisation_code>/survey/create/", methods=["GET", "POST"])
def organisation_survey(organisation_code=None):
    if request.method=='POST':
        return "You're trying to submit data"
    else:
        organisation = Organisation.query.filter_by(
            organisation_code=organisation_code).first_or_404()

        indicators = dqindicators.indicators("pwyf2013")
        twentytwelvedata=get_organisation_results(organisation_code, indicators)

        publication_status= {
                        '4': {
                            'text': 'Always published',
                            'class': 'success'
                        },
                        '3':  {
                            'text': 'Sometimes published',
                            'class': 'warning'
                        },
                        '2':  {
                            'text': 'Collected',
                            'class': 'important'
                        },
                        '1':  {
                            'text': 'Not collected',
                            'class': 'inverse'
                        },
                        '0':  {
                            'text': 'Unknown',
                            'class': ''
                        },
                        "": {
                            'text': '',
                            'class': ''
                        }
                    }

        return render_template("organisation_survey_create.html", 
                               organisation=organisation,
                               indicators=indicators,
                               twentytwelvedata=twentytwelvedata,
                               publication_status=publication_status)

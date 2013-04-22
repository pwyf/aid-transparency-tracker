
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

from iatidq import dqtests, dqaggregationtypes

import StringIO
import unicodecsv

@app.route("/aggregationtypes/")
@app.route("/aggregationtypes/<aggregationtype_id>/")
def aggregationtypes(aggregationtype_id=None):
    ats=dqaggregationtypes.aggregationTypes()
    return render_template("aggregation_types.html", aggregationtypes=ats)

@app.route("/aggregationtypes/new/", methods=['POST', 'GET'])
@app.route("/aggregationtypes/<aggregationtype_id>/edit/", methods=['POST', 'GET'])
def aggregationtypes_edit(aggregationtype_id=None):
    def get_data():
        fields = ['name', 'description', 'test_id', 'test_result']
        return dict([ (f, request.form.get(f)) for f in fields ])
    
    if aggregationtype_id:
        if request.method=='POST':
            data = get_data()
            if data['test_id']=="":
                data['test_id'] = None
            aggregationtype = \
                dqaggregationtypes.updateAggregationType(aggregationtype_id, 
                                                         data)

            if aggregationtype:
               flash('Successfully updated your aggregation type.', 'success')
            else:
               aggregationtype = {}
               flash('Could not update your aggregation type.', 'error')
        else:
            aggregationtype=dqaggregationtypes.aggregationTypes(
                aggregationtype_id)
    else:
        aggregationtype = {}
        if request.method=='POST':
            data = get_data()
            if data['test_id']=="":
                data['test_id'] = None
            aggregationtype = dqaggregationtypes.addAggregationType(data)

            if aggregationtype:
               flash('Successfully added your aggregation type.', 'success')
            else:
               aggregationtype = {}
               flash('Could not add your aggregation type.', 'error')

    tests = dqtests.tests()
    return render_template("aggregation_types_edit.html", 
                           aggregationtype=aggregationtype, tests=tests)

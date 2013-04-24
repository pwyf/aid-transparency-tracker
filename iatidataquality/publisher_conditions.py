
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import render_template, flash, request, Markup, \
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

from iatidq import dqdownload, dqregistry, dqindicators, dqorganisations, dqpackages
from iatidq.models import *

import StringIO
import unicodecsv
import tempfile
import spreadsheet

def get_pc(pc_id):
    return db.session.query(
        OrganisationCondition.id,
        OrganisationCondition.description,
        OrganisationCondition.operation,
        OrganisationCondition.condition,
        OrganisationCondition.condition_value,
        Organisation.organisation_name.label("organisation_name"),
        Organisation.organisation_code.label("organisation_code"),
        Organisation.id.label("organisation_id"),
        Test.name.label("test_name"),    
        Test.description.label("test_description"),
        Test.id.label("test_id")
        ).filter_by(id=pc_id
                    ).join(Organisation, Test).first()

def get_pcs():
    return db.session.query(
        OrganisationCondition.id,
        OrganisationCondition.description,
        Organisation.organisation_name.label("organisation_name"),
        Organisation.organisation_code.label("organisation_code"),
        Organisation.id.label("organisation_id"),
        Test.name.label("test_name"),    
        Test.description.label("test_description"),
        Test.id.label("test_id")
        ).order_by(
        OrganisationCondition.id
        ).join(Organisation, Test
               ).all()
        
@app.route("/organisation_conditions/")
@app.route("/organisation_conditions/<id>/")
def organisation_conditions(id=None):
    if id is not None:
        pc = get_pc(id)
        return render_template("organisation_condition.html", pc=pc)
    else:
        pcs = get_pcs()
        return render_template("organisation_conditions.html", pcs=pcs)

def configure_organisation_condition(pc):
    pc.description = request.form['description']
    pc.organisation_id = int(request.form['organisation_id'])
    pc.test_id = int(request.form['test_id'])
    pc.operation = int(request.form['operation'])
    pc.condition = request.form['condition']
    pc.condition_value = request.form['condition_value']
    pc.file = request.form['file']
    pc.line = int(request.form['line'])
    pc.active = bool(request.form['active'])

def update_organisation_condition(pc_id):
    pc = OrganisationCondition.query.filter_by(id=pc_id).first_or_404()
    configure_organisation_condition(pc)
    db.session.add(pc)
    db.session.commit()

@app.route("/organisation_conditions/<id>/edit/", methods=['GET', 'POST'])
def organisation_conditions_editor(id=None):
    organisations = Organisation.query.order_by(
        Organisation.organisation_code).all()
    tests = Test.query.order_by(Test.id).all()
    if request.method == 'POST':
        if request.form['password'] == app.config["SECRET_PASSWORD"]:
            update_organisation_condition(id)
            flash('Updated', "success")
            return redirect(url_for('organisation_conditions_editor', id=pc.id))
        else:
            flash('Incorrect password', "error")
    else:
        pc = OrganisationCondition.query.filter_by(id=id).first_or_404()
        return render_template("organisation_condition_editor.html", 
                               pc=pc, organisations=organisations, tests=tests)

@app.route("/organisation_conditions/new/", methods=['GET', 'POST'])
def organisation_conditions_new(id=None):
    organisations = Organisation.query.order_by(
        Organisation.organisation_code).all()
    tests = Test.query.order_by(Test.id).all()

    template_args = dict(
        pc={},
        organisations=organisations, 
        tests=tests
        )

    if (request.method == 'POST'):
        pc = OrganisationCondition()
        configure_organisation_condition(pc)
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            db.session.add(pc)
            db.session.commit()
            flash('Created new condition', "success")
            return redirect(url_for('organisation_conditions_editor', id=pc.id))
        else:
            flash('Incorrect password', "error")
            template_args["pc"] = pc
    else:
        return render_template("organisation_condition_editor.html", 
                               **template_args)

def ipc_step2():
    step = '2'
    if request.method != 'POST':
        return

    from iatidq import dqimportpublisherconditions
    if not (request.form['password'] == app.config["SECRET_PASSWORD"]):
        flash('Wrong password', "error")
        return render_template("import_organisation_conditions.html")

    def get_results():
        if request.form.get('local'):
            return dqimportpublisherconditions.importPCsFromFile()
        else:
            url = request.form['url']
            return dqimportpublisherconditions.importPCsFromUrl(url)

    results = get_results()

    if results:
        flash('Parsed conditions', "success")
        return render_template(
            "import_organisation_conditions_step2.html", 
            results=results, step=step)
    else:
        flash('There was an error importing your conditions', "error")
        return redirect(url_for('import_organisation_conditions'))

def import_pc_row(row):
    def pc_form_value(key):
        form_key = 'pc[%s][%s]' % (row, key)
        return request.form[form_key]

    organisation_id = pc_form_value('organisation_id')
    test_id = pc_form_value('test_id')
    operation = pc_form_value('operation')
    condition = pc_form_value('condition')
    condition_value = pc_form_value('condition_value')

    pc = OrganisationCondition.query.filter_by(
        organisation_id=organisation_id, test_id=test_id, 
        operation=operation, condition=condition, 
        condition_value=condition_value).first()

    if (pc is None):
        pc = OrganisationCondition()
        
    pc.organisation_id=organisation_id
    pc.test_id=test_id
    pc.operation = operation
    pc.condition = condition
    pc.condition_value = condition_value
    pc.description = pc_form_value('description')
    db.session.add(pc)

def ipc_step3():
    [ import_pc_row(row) for row in request.form.getlist('include') ]
    db.session.commit()
    flash('Successfully updated organisation conditions', 'success')
    return redirect(url_for('organisation_conditions'))

@app.route("/organisation_conditions/import/step<step>", methods=['GET', 'POST'])
@app.route("/organisation_conditions/import/", methods=['GET', 'POST'])
def import_organisation_conditions(step=None):
    # Step=1: form; submit to step2
    # 
    if (step == '2'):
        return ipc_step2()
    elif (step=='3'):
        return ipc_step3()
    else:
        return render_template("import_organisation_conditions.html")

@app.route("/organisation_conditions/export/")
def export_organisation_conditions():
    conditions = db.session.query(
        OrganisationCondition.description).distinct().all()
    conditionstext = ""
    for i, condition in enumerate(conditions):
        if (i != 0):
            conditionstext = conditionstext + "\n"
        conditionstext = conditionstext + condition.description

    strIO = StringIO.StringIO()
    strIO.write(str(conditionstext))
    strIO.seek(0)
    return send_file(strIO,
                     attachment_filename="organisation_structures.txt",
                     as_attachment=True)

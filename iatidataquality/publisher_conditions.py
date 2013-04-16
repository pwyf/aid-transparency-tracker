
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
import aggregation

import StringIO
import unicodecsv
import tempfile
import spreadsheet

def get_pc(pc_id):
    return db.session.query(
        PublisherCondition.id,
        PublisherCondition.description,
        PublisherCondition.operation,
        PublisherCondition.condition,
        PublisherCondition.condition_value,
        PackageGroup.title.label("packagegroup_name"),
        PackageGroup.id.label("packagegroup_id"),
        Test.name.label("test_name"),    
        Test.description.label("test_description"),
        Test.id.label("test_id")
        ).filter_by(id=pc_id
                    ).join(PackageGroup, Test).first()

def get_pcs():
    return db.session.query(
        PublisherCondition.id,
        PublisherCondition.description,
        PackageGroup.title.label("packagegroup_name"),
        PackageGroup.id.label("packagegroup_id"),
        Test.name.label("test_name"),    
        Test.description.label("test_description"),
        Test.id.label("test_id")
        ).order_by(
        PublisherCondition.id
        ).join(PackageGroup, Test
               ).all()
        
@app.route("/publisher_conditions/")
@app.route("/publisher_conditions/<id>/")
def publisher_conditions(id=None):
    if id is not None:
        pc = get_pc(id)
        return render_template("publisher_condition.html", pc=pc)
    else:
        pcs = get_pcs()
        return render_template("publisher_conditions.html", pcs=pcs)

def configure_publisher_condition(pc):
    pc.description = request.form['description']
    pc.publisher_id = int(request.form['publisher_id'])
    pc.test_id = int(request.form['test_id'])
    pc.operation = int(request.form['operation'])
    pc.condition = request.form['condition']
    pc.condition_value = request.form['condition_value']
    pc.file = request.form['file']
    pc.line = int(request.form['line'])
    pc.active = int(request.form['active'])

def update_publisher_condition(pc_id):
    pc = PublisherCondition.query.filter_by(id=pc_id).first_or_404()
    configure_publisher_condition(pc)
    db.session.add(pc)
    db.session.commit()

@app.route("/publisher_conditions/<id>/edit/", methods=['GET', 'POST'])
def publisher_conditions_editor(id=None):
    publishers = PackageGroup.query.order_by(
        PackageGroup.id).all()
    tests = Test.query.order_by(Test.id).all()
    if request.method == 'POST':
        if request.form['password'] == app.config["SECRET_PASSWORD"]:
            update_publisher_condition(id)
            flash('Updated', "success")
            return redirect(url_for('publisher_conditions_editor', id=pc.id))
        else:
            flash('Incorrect password', "error")
    else:
        pc = PublisherCondition.query.filter_by(id=id).first_or_404()
        return render_template("publisher_condition_editor.html", 
                               pc=pc, publishers=publishers, tests=tests)

@app.route("/publisher_conditions/new/", methods=['GET', 'POST'])
def publisher_conditions_new(id=None):
    publishers = PackageGroup.query.order_by(
        PackageGroup.id).all()
    tests = Test.query.order_by(Test.id).all()

    template_args = dict(
        pc={},
        publishers=publishers, 
        tests=tests
        )

    if (request.method == 'POST'):
        pc = PublisherCondition()
        configure_publisher_condition(pc)
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            db.session.add(pc)
            db.session.commit()
            flash('Created new condition', "success")
            return redirect(url_for('publisher_conditions_editor', id=pc.id))
        else:
            flash('Incorrect password', "error")
            template_args["pc"] = pc
    else:
        return render_template("publisher_condition_editor.html", 
                               **template_args)

def ipc_step2():
    step = '2'
    if (request.method == 'POST'):
        from iatidq import dqimportpublisherconditions
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            if (request.form.get('local')):
                results = dqimportpublisherconditions.importPCsFromFile()
            else:
                url = request.form['url']
                results = dqimportpublisherconditions.importPCsFromUrl(url)
            if (results):
                flash('Parsed tests', "success")
                return render_template(
                    "import_publisher_conditions_step2.html", 
                    results=results, step=step)
            else:
                results = None
                flash('There was an error importing your tests', "error")
                return redirect(url_for('import_publisher_conditions'))
        else:
            flash('Wrong password', "error")
            return render_template("import_publisher_conditions.html")

def ipc_step3():
    out = []
    for row in request.form.getlist('include'):
        publisher_id = request.form['pc['+row+'][publisher_id]']
        test_id = request.form['pc['+row+'][test_id]']
        operation = request.form['pc['+row+'][operation]']
        condition = request.form['pc['+row+'][condition]']
        condition_value = request.form['pc['+row+'][condition_value]']
        pc = PublisherCondition.query.filter_by(
            publisher_id=publisher_id, test_id=test_id, 
            operation=operation, condition=condition, 
            condition_value=condition_value).first()
        if (pc is None):
            pc = PublisherCondition()
        pc.publisher_id=publisher_id
        pc.test_id=test_id
        pc.operation = operation
        pc.condition = condition
        pc.condition_value = condition_value
        pc.description = request.form['pc['+row+'][description]']
        db.session.add(pc)
    db.session.commit()
    flash('Successfully updated publisher conditions', 'success')
    return redirect(url_for('publisher_conditions'))

@app.route("/publisher_conditions/import/step<step>", methods=['GET', 'POST'])
@app.route("/publisher_conditions/import/", methods=['GET', 'POST'])
def import_publisher_conditions(step=None):
    # Step=1: form; submit to step2
    # 
    if (step == '2'):
        return ipc_step2()
    elif (step=='3'):
        return ipc_step3()
    else:
        return render_template("import_publisher_conditions.html")

@app.route("/publisher_conditions/export/")
def export_publisher_conditions():
    conditions = db.session.query(
        PublisherCondition.description).distinct().all()
    conditionstext = ""
    for i, condition in enumerate(conditions):
        if (i != 0):
            conditionstext = conditionstext + "\n"
        conditionstext = conditionstext + condition.description

    strIO = StringIO.StringIO()
    strIO.write(str(conditionstext))
    strIO.seek(0)
    return send_file(strIO,
                     attachment_filename="publisher_structures.txt",
                     as_attachment=True)

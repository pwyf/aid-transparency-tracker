
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import current_user

from iatidataquality import app
from iatidataquality import db

from iatidq import dqdownload, dqregistry, dqindicators, dqorganisations, dqpackages, dqpublishercondition
from iatidq.models import *

import StringIO

import usermanagement

@app.route("/organisation_conditions/clear/")
@usermanagement.perms_required()
def organisationfeedback_clear():
    feedback = dqpublishercondition.get_publisher_feedback()
    dqpublishercondition.delete_publisher_feedback(feedback)
    flash('All remaining publisher feedback was successfully cleared', 'warning')
    return redirect(url_for('organisation_conditions'))
        
@app.route("/organisation_conditions/")
@app.route("/organisation_conditions/<id>/")
@usermanagement.perms_required()
def organisation_conditions(id=None):
    if id is not None:
        pc = dqpublishercondition.get_publisher_condition(id)
        return render_template("organisation_condition.html", pc=pc,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)
    else:
        pcs = dqpublishercondition.get_publisher_conditions()
        feedbackconditions = dqpublishercondition.get_publisher_feedback()
        text = ""
        for i, condition in enumerate(feedbackconditions):
            if i>0: text += "\n"
            text += condition.Organisation.organisation_code + " does not use "
            text += condition.OrganisationConditionFeedback.element + " at "
            text += condition.OrganisationConditionFeedback.where
        return render_template("organisation_conditions.html", pcs=pcs,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user,
             feedbackconditions=text)
        
@app.route("/organisation_conditions/<int:id>/delete/")
@usermanagement.perms_required()
def organisation_condition_delete(id=None):
    pc = dqpublishercondition.delete_publisher_condition(id)
    flash('Deleted that condition', "success")
    return redirect(url_for('organisation_conditions'))

@app.route("/organisation_conditions/import_feedback/", methods=['POST'])
@usermanagement.perms_required()
def import_feedback():
    from iatidq import dqimportpublisherconditions

    def get_results():
        if request.form.get('feedbacktext'):
            text = request.form.get('feedbacktext')
            return dqimportpublisherconditions.importPCsFromText(text)

    results = get_results()

    if results:
        flash('Parsed conditions', "success")
        return render_template(
            "import_organisation_conditions_step2.html",
            results=results,
            step=2,
            admin=usermanagement.check_perms('admin'),
            loggedinuser=current_user)
    else:
        flash('There was an error importing your conditions', "error")
        return redirect(url_for('import_organisation_conditions'))

def update_organisation_condition(pc_id):
    pc = OrganisationCondition.query.filter_by(id=pc_id).first_or_404()
    dqpublishercondition.configure_organisation_condition(pc, request)

@app.route("/organisation_conditions/<id>/edit/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def organisation_conditions_editor(id=None):
    organisations = Organisation.query.order_by(
        Organisation.organisation_code).all()
    tests = Test.query.order_by(Test.id).all()
    if request.method == 'POST':
        update_organisation_condition(id)
        flash('Updated', "success")
        return redirect(url_for('organisation_conditions_editor', id=pc.id))
    else:
        pc = OrganisationCondition.query.filter_by(id=id).first_or_404()
        return render_template("organisation_condition_editor.html", 
                               pc=pc, 
                               organisations=organisations, 
                               tests=tests,
                               admin=usermanagement.check_perms('admin'),
                               loggedinuser=current_user)

@app.route("/organisation_conditions/new/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def organisation_conditions_new(id=None):
    organisations = Organisation.query.order_by(
        Organisation.organisation_code).all()
    tests = Test.query.order_by(Test.id).all()

    template_args = dict(
        pc={},
        organisations=organisations, 
        tests=tests,
        admin=usermanagement.check_perms('admin'),
        loggedinuser=current_user
        )

    if (request.method == 'POST'):
        pc = OrganisationCondition()
        dqpublishercondition.configure_organisation_condition(pc, request)
        flash('Created new condition', "success")
        return redirect(url_for('organisation_conditions_editor', id=pc.id))
    else:
        return render_template("organisation_condition_editor.html", 
                               **template_args)

def ipc_step2():
    step = '2'
    if request.method != 'POST':
        return

    from iatidq import dqimportpublisherconditions

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
            results=results, 
            step=step,
            admin=usermanagement.check_perms('admin'),
            loggedinuser=current_user)
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

    with db.session.begin():
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
    flash('Successfully updated organisation conditions', 'success')
    return redirect(url_for('organisation_conditions'))

@app.route("/organisation_conditions/import/step<step>", methods=['GET', 'POST'])
@app.route("/organisation_conditions/import/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def import_organisation_conditions(step=None):
    # Step=1: form; submit to step2
    # 
    if (step == '2'):
        return ipc_step2()
    elif (step=='3'):
        return ipc_step3()
    else:
        return render_template("import_organisation_conditions.html",
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

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

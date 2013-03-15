
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

from sqlalchemy import func
from datetime import datetime

from iatidataquality import app
from iatidataquality import db


import os
import sys
current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from iatidq import models, dqdownload, dqregistry, dqindicators
import aggregation

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/tests/")
@app.route("/tests/<id>/")
def tests(id=None):
    if (id is not None):
        test = models.Test.query.filter_by(id=id).first_or_404()
        return render_template("test.html", test=test)
    else:
        tests = models.Test.query.order_by(models.Test.id).all()
        return render_template("tests.html", tests=tests)

@app.route("/tests/<id>/edit/", methods=['GET', 'POST'])
def tests_editor(id=None):
    if (request.method == 'POST'):
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            test = models.Test.query.filter_by(id=id).first_or_404()
            test.name = request.form['name']
            test.description = request.form['description']
            test.test_level = request.form['test_level']
            test.active = request.form['active']
            test.test_group = request.form['test_group']
            db.session.add(test)
            db.session.commit()
            flash('Updated', "success")
            return render_template("test_editor.html", test=test)
        else:
            flash('Incorrect password', "error")
            test = models.Test.query.filter_by(id=id).first_or_404()
            return render_template("test_editor.html", test=test)
    else:
        test = models.Test.query.filter_by(id=id).first_or_404()
        return render_template("test_editor.html", test=test)

@app.route("/tests/new/", methods=['GET', 'POST'])
def tests_new(id=None):
    if (request.method == 'POST'):
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            test = models.Test()
            test.setup(
                name = request.form['name'],
                description = request.form['description'],
                test_group = request.form['test_group'],
                test_level = request.form['test_level'],
                active = request.form['active']
                )
            db.session.add(test)
            db.session.commit()
            flash('Updated', "success")
            return render_template("test_editor.html", test=test)
        else:
            flash('Incorrect password', "error")
            return render_template("test_editor.html", test={})
    else:
        return render_template("test_editor.html", test={})

@app.route("/publisher_conditions/")
@app.route("/publisher_conditions/<id>/")
def publisher_conditions(id=None):
    if (id is not None):
        pc = db.session.query(models.PublisherCondition.id,
                               models.PublisherCondition.description,
                               models.PublisherCondition.operation,
                               models.PublisherCondition.condition,
                               models.PublisherCondition.condition_value,
                               models.PackageGroup.title.label("packagegroup_name"),
                               models.PackageGroup.id.label("packagegroup_id"),
                               models.Test.name.label("test_name"),    
                               models.Test.description.label("test_description"),
                               models.Test.id.label("test_id")
                            ).filter_by(id=id
                            ).join(models.PackageGroup, models.Test).first()
        return render_template("publisher_condition.html", pc=pc)
    else:
        pcs = db.session.query(models.PublisherCondition.id,
                               models.PublisherCondition.description,
                               models.PackageGroup.title.label("packagegroup_name"),
                               models.PackageGroup.id.label("packagegroup_id"),
                               models.Test.name.label("test_name"),    
                               models.Test.description.label("test_description"),
                               models.Test.id.label("test_id")
                            ).order_by(models.PublisherCondition.id
                            ).join(models.PackageGroup, models.Test
                            ).all()
        return render_template("publisher_conditions.html", pcs=pcs)

@app.route("/publisher_conditions/<id>/edit/", methods=['GET', 'POST'])
def publisher_conditions_editor(id=None):
    publishers = models.PackageGroup.query.order_by(
        models.PackageGroup.id).all()
    tests = models.Test.query.order_by(models.Test.id).all()
    if (request.method == 'POST'):
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            pc = models.PublisherCondition.query.filter_by(id=id).first_or_404()
            pc.description = request.form['description']
            pc.publisher_id = int(request.form['publisher_id'])
            pc.test_id = int(request.form['test_id'])
            pc.operation = int(request.form['operation'])
            pc.condition = request.form['condition']
            pc.condition_value = request.form['condition_value']
            pc.file = request.form['file']
            pc.line = int(request.form['line'])
            pc.active = int(request.form['active'])
            db.session.add(pc)
            db.session.commit()
            flash('Updated', "success")
            return redirect(url_for('publisher_conditions_editor', id=pc.id))
        else:
            flash('Incorrect password', "error")
            pc = models.PublisherCondition.query.filter_by(id=id).first_or_404()
            return render_template("publisher_condition_editor.html", 
                                   pc=pc, publishers=publishers, tests=tests)
    else:
        pc = models.PublisherCondition.query.filter_by(id=id).first_or_404()
        return render_template("publisher_condition_editor.html", 
                               pc=pc, publishers=publishers, tests=tests)

@app.route("/publisher_conditions/new/", methods=['GET', 'POST'])
def publisher_conditions_new(id=None):
    publishers = models.PackageGroup.query.order_by(
        models.PackageGroup.id).all()
    tests = models.Test.query.order_by(models.Test.id).all()
    if (request.method == 'POST'):
        pc = models.PublisherCondition()
        pc.description = request.form['description']
        pc.publisher_id = int(request.form['publisher_id'])
        pc.test_id = int(request.form['test_id'])
        pc.operation = int(request.form['operation'])
        pc.condition = request.form['condition']
        pc.condition_value = request.form['condition_value']
        pc.file = request.form['file']
        pc.line = int(request.form['line'])
        pc.active = int(request.form['active'])
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            db.session.add(pc)
            db.session.commit()
            flash('Created new condition', "success")
            return redirect(url_for('publisher_conditions_editor', id=pc.id))
        else:
            flash('Incorrect password', "error")
            return render_template("publisher_condition_editor.html", 
                                   pc=pc, publishers=publishers, tests=tests)
    else:
        return render_template("publisher_condition_editor.html", 
                               pc={}, publishers=publishers, tests=tests)

@app.route("/publishers/")
def publishers():
    p_groups = models.PackageGroup.query.order_by(
        models.PackageGroup.name).all()

    pkgs = models.Package.query.order_by(models.Package.package_name).all()
    return render_template("publishers.html", p_groups=p_groups, pkgs=pkgs)

@app.route("/publishers/<id>/detail")
def publisher_detail(id=None):
    p_group = models.PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Package.package_group == p_group.id
            ).order_by(models.Package.package_name).all()

    """try:"""
    aggregate_results = db.session.query(models.Indicator,
                                     models.Test,
                                     models.AggregateResult.results_data,
                                     models.AggregateResult.results_num,
                                     models.AggregateResult.result_hierarchy,
                                     models.AggregateResult.package_id,
                                     func.max(models.AggregateResult.runtime_id)
        ).filter(models.PackageGroup.id==p_group.id
        ).group_by(models.Indicator,
                   models.AggregateResult.result_hierarchy, 
                   models.Test, 
                   models.AggregateResult.package_id,
                   models.AggregateResult.results_data,
                   models.AggregateResult.results_num
        ).join(models.IndicatorTest
        ).join(models.Test
        ).join(models.AggregateResult
        ).join(models.Package
        ).join(models.PackageGroup
        ).all()

    pconditions = models.PublisherCondition.query.filter_by(
        publisher_id=p_group.id).all()

    aggregate_results = aggregation.agr_results(aggregate_results, 
                                                conditions=pconditions, 
                                                mode="publisher")
    latest_runtime=1
    """except Exception, e:
        latest_runtime = None
        aggregate_results = None"""

    return render_template("publisher.html", p_group=p_group, pkgs=pkgs, 
                           results=aggregate_results, runtime=latest_runtime)

@app.route("/publishers/<id>/")
def publisher(id=None):
    p_group = models.PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Package.package_group == p_group.id
            ).order_by(models.Package.package_name).all()

    """try:"""
    aggregate_results = db.session.query(models.Indicator,
                                     models.Test,
                                     models.AggregateResult.results_data,
                                     models.AggregateResult.results_num,
                                     models.AggregateResult.result_hierarchy,
                                     models.AggregateResult.package_id,
                                     func.max(models.AggregateResult.runtime_id)
        ).filter(models.PackageGroup.id==p_group.id
        ).group_by(models.AggregateResult.result_hierarchy, 
                   models.Test, 
                   models.AggregateResult.package_id,
                   models.Indicator,
                   models.AggregateResult.results_data,
                   models.AggregateResult.results_num,
                   models.AggregateResult.package_id
        ).join(models.IndicatorTest
        ).join(models.Test
        ).join(models.AggregateResult
        ).join(models.Package
        ).join(models.PackageGroup
        ).all()

    pconditions = models.PublisherCondition.query.filter_by(
        publisher_id=p_group.id).all()

    aggregate_results = aggregation.agr_results(aggregate_results, 
                                                conditions=pconditions, 
                                                mode="publisher_indicators")
    latest_runtime=1
    """except Exception, e:
        latest_runtime = None
        aggregate_results = None"""

    return render_template("publisher_indicators.html", p_group=p_group, pkgs=pkgs, 
                           results=aggregate_results, runtime=latest_runtime)

@app.route("/registry/refresh/")
def registry_refresh():
    dqregistry.refresh_packages()
    return "Refreshed"

@app.route("/registry/download/")
def registry_download():
    dqdownload.run()
    return "Downloading"

@app.route("/packages/manage/", methods=['GET', 'POST'])
def packages_manage():
    if (request.method == 'POST'):
        if ("refresh" in request.form):
            dqregistry.refresh_packages()
            flash("Refreshed packages from Registry", "success")
        else:
            data = []
            for package in request.form.getlist('package'):
                try:
                    request.form["active_"+package]
                    active=True
                except Exception:
                    active=False
                data.append((package, active))
            dqregistry.activate_packages(data)
            flash("Updated packages", "success")
        return redirect(url_for('packages_manage'))
    else:
        pkgs = models.Package.query.order_by(models.Package.package_name).all()
        return render_template("packages_manage.html", pkgs=pkgs)

@app.route("/packages/")
@app.route("/packages/<id>/")
@app.route("/packages/<id>/runtimes/<runtime_id>/")
def packages(id=None, runtime_id=None):
    if (id is None):
        if (request.method == 'POST'):
            for package in request.form.getlist('package'):
                p = models.Package.query.filter_by(package_name=package).first()
                try:
                    request.form["active_"+package]
                    p.active=True
                except Exception:
                    p.active=False
                db.session.add(p)
            db.session.commit()
            flash("Updated packages", "success")
            return redirect(url_for('packages'))
        else:
            pkgs = models.Package.query.filter_by(active=True).order_by(
                models.Package.package_name).all()
            return render_template("packages.html", pkgs=pkgs)

    # Get package data
    p = db.session.query(models.Package,
        models.PackageGroup
		).filter(models.Package.package_name == id
        ).join(models.PackageGroup).first()

    if (p is None):
        p = db.session.query(models.Package
		).filter(models.Package.package_name == id
        ).first()
        pconditions = {}
    else:
        # Get publisher-specific conditions.

        pconditions = models.PublisherCondition.query.filter_by(
            publisher_id=p[1].id).all()

    # Get list of runtimes
    try:
        runtimes = db.session.query(models.Result.runtime_id,
                                    models.Runtime.runtime_datetime
            ).filter(models.Result.package_id==p[0].id
            ).distinct(
            ).join(models.Runtime
            ).all()
    except Exception:
        return abort(404)

    if (runtime_id):
        # If a runtime is specified in the request, get the data

        latest_runtime = db.session.query(models.Runtime,
            ).filter(models.Runtime.id==runtime_id
            ).first()
        latest = False
    else:
        # Select the highest runtime; then get data for that one

        latest_runtime = db.session.query(models.Runtime
            ).filter(models.Result.package_id==p[0].id
            ).join(models.Result
            ).order_by(models.Runtime.id.desc()
            ).first()
        latest = True
    if (latest_runtime):
        aggregate_results = db.session.query(models.Indicator,
                                             models.Test,
                                             models.AggregateResult.results_data,
                                             models.AggregateResult.results_num,
                                             models.AggregateResult.result_hierarchy
                ).filter(models.AggregateResult.package_id==p[0].id,
                         models.AggregateResult.runtime_id==latest_runtime.id
                ).group_by(models.AggregateResult.result_hierarchy, 
                           models.Test,
                           models.AggregateResult.results_data,
                           models.AggregateResult.results_num,
                           models.Indicator
                ).join(models.IndicatorTest
                ).join(models.Test
                ).join(models.AggregateResult
                ).all()

        flat_results = aggregate_results

        aggregate_results = aggregation.agr_results(aggregate_results, 
                                                    pconditions)
    else:
        aggregate_results = None
        pconditions = None
        flat_results = None
        latest_runtime = None
 
    return render_template("package.html", p=p, runtimes=runtimes, 
                           results=aggregate_results, 
                           latest_runtime=latest_runtime, latest=latest, 
                           pconditions=pconditions, flat_results=flat_results)

@app.route("/tests/import/", methods=['GET', 'POST'])
def import_tests():
    if (request.method == 'POST'):
        import dqimporttests
        if (request.form['password'] == app.config["SECRET_PASSWORD"]):
            if (request.form.get('local')):
                result = dqimporttests.importTests()
            else:
                url = request.form['url']
                level = int(request.form['level'])
                result = dqimporttests.importTests(url, level, False)
            if (result==True):
                flash('Imported tests', "success")
            else:
                flash('There was an error importing your tests', "error")
        else:
            flash('Wrong password', "error")
        return render_template("import_tests.html")
    else:
        return render_template("import_tests.html")

@app.route("/publisher_conditions/import/step<step>", methods=['GET', 'POST'])
@app.route("/publisher_conditions/import/", methods=['GET', 'POST'])
def import_publisher_conditions(step=None):
    # Step=1: form; submit to step2
    # 
    if (step == '2'):
        if (request.method == 'POST'):
            from iatidq import dqimportpublisherconditions
            if (request.form['password'] == app.config["SECRET_PASSWORD"]):
                if (request.form.get('local')):
                    results = dqimportpublisherconditions.importPCs()
                else:
                    url = request.form['url']
                    results = dqimportpublisherconditions.importPCs(url, False)
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
    elif (step=='3'):
        out = []
        for row in request.form.getlist('include'):
            publisher_id = request.form['pc['+row+'][publisher_id]']
            test_id = request.form['pc['+row+'][test_id]']
            operation = request.form['pc['+row+'][operation]']
            condition = request.form['pc['+row+'][condition]']
            condition_value = request.form['pc['+row+'][condition_value]']
            pc = models.PublisherCondition.query.filter_by(
                publisher_id=publisher_id, test_id=test_id, 
                operation=operation, condition=condition, 
                condition_value=condition_value).first()
            if (pc is None):
                pc = models.PublisherCondition()
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
    else:
        return render_template("import_publisher_conditions.html")

@app.route("/publisher_conditions/export/")
def export_publisher_conditions():
    conditions = db.session.query(
        models.PublisherCondition.description).distinct().all()
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

@app.route("/aggregate_results/<package_id>/<runtime>")
def display_aggregate_results(package_id, runtime):
    dqprocessing.aggregate_results(runtime, package_id)
    db.session.commit()
    return "ok"

@app.route("/indicators/")
def indicatorgroups():
    indicatorgroups = dqindicators.indicatorGroups()
    return render_template("indicatorgroups.html", indicatorgroups=indicatorgroups)

@app.route("/indicators/import/")
def indicators_import():
    if dqindicators.importIndicators():
        flash('Successfully imported your indicators', 'success')
    else:
        flash('Could not import your indicators', 'error')
    return redirect(url_for('indicatorgroups'))
    

@app.route("/indicators/<indicatorgroup>/edit/", methods=['GET', 'POST'])
def indicatorgroups_edit(indicatorgroup=None):
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description']
        }
        indicatorgroup = dqindicators.updateIndicatorGroup(indicatorgroup, data)
        flash('Successfully updated IndicatorGroup', 'success')
    else:
        indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)
    return render_template("indicatorgroups_edit.html", indicatorgroup=indicatorgroup)

@app.route("/indicators/<indicatorgroup>/delete/")
def indicatorgroups_delete(indicatorgroup=None):
    indicatorgroup = dqindicators.deleteIndicatorGroup(indicatorgroup)
    flash('Successfully deleted IndicatorGroup', 'success')
    return redirect(url_for('indicatorgroups'))

@app.route("/indicators/new/", methods=['GET', 'POST'])
def indicatorgroups_new():
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description']
        }
        indicatorgroup = dqindicators.addIndicatorGroup(data)
        if indicatorgroup:
            flash('Successfully added IndicatorGroup.', 'success')
        else:
            flash("Couldn't add IndicatorGroup. Maybe one already exists with the same name?", 'error')
    else:
        indicatorgroup = None
    return render_template("indicatorgroups_edit.html", indicatorgroup=indicatorgroup)

@app.route("/indicators/<indicatorgroup>/")
def indicators(indicatorgroup=None):
    indicators = dqindicators.indicators(indicatorgroup)
    indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)
    return render_template("indicators.html", indicatorgroup=indicatorgroup, indicators=indicators)

@app.route("/indicators/<indicatorgroup>/new/", methods=['GET', 'POST'])
def indicators_new(indicatorgroup=None):
    indicatorgroups = dqindicators.indicatorGroups()
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'indicatorgroup_id': request.form['indicatorgroup_id']
        }
        indicator = dqindicators.addIndicator(data)
        if indicator:
            flash('Successfully added Indicator.', 'success')
        else:
            flash("Couldn't add Indicator. Maybe one already exists with the same name?", 'error')
    else:
        indicator = None
    return render_template("indicator_edit.html", indicatorgroups=indicatorgroups, indicator=indicator)

@app.route("/indicators/<indicatorgroup>/<indicator>/edit/", methods=['GET', 'POST'])
def indicators_edit(indicatorgroup=None, indicator=None):
    indicatorgroups = dqindicators.indicatorGroups()
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'indicatorgroup_id': request.form['indicatorgroup_id']
        }
        indicator = dqindicators.updateIndicator(indicatorgroup, indicator, data)
        flash('Successfully updated Indicator', 'success')
    else:
        indicator = dqindicators.indicators(indicatorgroup, indicator)
    return render_template("indicator_edit.html", indicatorgroups=indicatorgroups, indicator=indicator)

@app.route("/indicators/<indicatorgroup>/<indicator>/delete/")
def indicators_delete(indicatorgroup=None, indicator=None):
    indicator = dqindicators.deleteIndicator(indicatorgroup, indicator)
    flash('Successfully deleted Indicator', 'success')
    return redirect(url_for('indicators', indicatorgroup=indicatorgroup))

@app.route("/indicators/<indicatorgroup>/<indicator>/", methods=['GET', 'POST'])
def indicatortests(indicatorgroup=None, indicator=None):
    alltests = dqindicators.allTests()
    indicator = dqindicators.indicators(indicatorgroup, indicator)
    indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)
    if (request.method == 'POST'):
        for test in request.form.getlist('test'):
            data = {
                    'indicator_id': indicator.id,
                    'test_id': test
            }
            if dqindicators.addIndicatorTest(data):
                flash('Successfully added test to your indicator.', 'success');
            else:
                flash("Couldn't add test to your indicator.", 'error');
    indicatortests = dqindicators.indicatorTests(indicator.name)
    return render_template("indicatortests.html", indicatorgroup=indicatorgroup, indicator=indicator, indicatortests=indicatortests, alltests=alltests)

@app.route("/indicators/<indicatorgroup>/<indicator>/<indicatortest>/delete/")
def indicatortests_delete(indicatorgroup=None, indicator=None, indicatortest=None):
    if dqindicators.deleteIndicatorTest(indicatortest):
        flash('Successfully removed test from indicator ' + indicator + '.', 'success')
    else:
        flash('Could not remove test from indicator ' + indicator + '.', 'success')        
    return redirect(url_for('indicatortests', indicatorgroup=indicatorgroup, indicator=indicator))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


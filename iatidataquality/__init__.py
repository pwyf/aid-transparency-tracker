from flask import Flask, render_template, flash, request, Markup, session, redirect, url_for, escape, Response, abort, send_file
import StringIO
from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy import func
from datetime import datetime

from db import *

import models, api, dqfunctions, dqprocessing, dqruntests, dqdownload, dqregistry

def DATA_STORAGE_DIR():
    return app.config["DATA_STORAGE_DIR"]

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
    publishers = models.PackageGroup.query.order_by(models.PackageGroup.id).all()
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
            return render_template("publisher_condition_editor.html", pc=pc, publishers=publishers, tests=tests)
    else:
        pc = models.PublisherCondition.query.filter_by(id=id).first_or_404()
        return render_template("publisher_condition_editor.html", pc=pc, publishers=publishers, tests=tests)

@app.route("/publisher_conditions/new/", methods=['GET', 'POST'])
def publisher_conditions_new(id=None):
    publishers = models.PackageGroup.query.order_by(models.PackageGroup.id).all()
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
            return render_template("publisher_condition_editor.html", pc=pc, publishers=publishers, tests=tests)
    else:
        return render_template("publisher_condition_editor.html", pc={}, publishers=publishers, tests=tests)

@app.route("/publishers/")
def publishers():
    p_groups = models.PackageGroup.query.order_by(models.PackageGroup.name).all()

    pkgs = models.Package.query.order_by(models.Package.package_name).all()
    return render_template("publishers.html", p_groups=p_groups, pkgs=pkgs)

@app.route("/publishers/<id>/")
def publisher(id=None):
    p_group = models.PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Package.package_group == p_group.id
            ).order_by(models.Package.package_name).all()

    latest_runtime = db.session.query(models.Runtime
        ).filter(models.PackageGroup.id==p_group.id
        ).join(models.Result,
               models.Package,
               models.PackageGroup,
        ).order_by(models.Runtime.id.desc()
        ).first()
    
    if latest_runtime:
        aggregate_results = db.session.query(models.Test,
                                             models.AggregateResult.results_data,
                                             models.AggregateResult.results_num,
                                             models.AggregateResult.result_hierarchy,
                                             models.AggregateResult.package_id
                ).filter(models.Package.package_group==p_group.id,
                         models.AggregateResult.runtime_id==latest_runtime.id
                ).group_by(models.AggregateResult.result_hierarchy, models.Test.id, models.AggregateResult.package_id
                ).join(models.AggregateResult,
                       models.Package
                ).all()

        pconditions = models.PublisherCondition.query.filter_by(publisher_id=p_group.id).all()

        aggregate_results = dqfunctions.agr_results(aggregate_results, conditions=pconditions, mode="publisher")
    else:
        latest_runtime = None
        aggregate_results = None

    return render_template("publisher.html", p_group=p_group, pkgs=pkgs, results=aggregate_results, runtime=latest_runtime)

@app.route("/registry/refresh/")
def registry_refresh():
    dqregistry.refresh_packages()
    return "Refreshed"

@app.route("/registry/download/")
def registry_download():
    dqdownload.run()
    return "Downloading"

@app.route("/packages/", methods=['GET', 'POST'])
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
            pkgs = models.Package.query.order_by(models.Package.package_name).all()
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

        pconditions = models.PublisherCondition.query.filter_by(publisher_id=p[1].id).all()

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

    aggregate_results = db.session.query(models.Test,
                                         models.AggregateResult.results_data,
                                         models.AggregateResult.results_num,
                                         models.AggregateResult.result_hierarchy
            ).filter(models.AggregateResult.package_id==p[0].id,
                     models.AggregateResult.runtime_id==latest_runtime.id
            ).group_by(models.AggregateResult.result_hierarchy, models.Test
            ).join(models.AggregateResult
            ).all()

    flat_results = aggregate_results

    aggregate_results = dqfunctions.agr_results(aggregate_results, pconditions)
 
    return render_template("package.html", p=p, runtimes=runtimes, results=aggregate_results, latest_runtime=latest_runtime, latest=latest, pconditions=pconditions, flat_results=flat_results)

@app.route("/runtests/new/")
def run_new_tests():
    res = dqruntests.start_testing()
    
    flash('Running tests; this may take some time.', "success")
    return render_template("runtests.html", tasks=res)

@app.route("/runtests/")
def check_tests(id=None):
    return render_template("checktests.html")

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
            import dqimportpublisherconditions
            if (request.form['password'] == app.config["SECRET_PASSWORD"]):
                if (request.form.get('local')):
                    results = dqimportpublisherconditions.importPCs()
                else:
                    url = request.form['url']
                    results = dqimportpublisherconditions.importPCs(url, False)
                if (results):
                    flash('Parsed tests', "success")
                    return render_template("import_publisher_conditions_step2.html", results=results, step=step)
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
            pc = models.PublisherCondition.query.filter_by(publisher_id=publisher_id, test_id=test_id, operation=operation, condition=condition, condition_value=condition_value).first()
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
    conditions = db.session.query(models.PublisherCondition.description).all()
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

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

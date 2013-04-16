
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

@app.route("/packages/manage/", methods=['GET', 'POST'])
def packages_manage():
    if request.method == 'POST':
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

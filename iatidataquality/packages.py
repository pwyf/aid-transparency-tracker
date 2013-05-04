
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

from iatidq import dqdownload, dqregistry, dqindicators, dqorganisations, dqpackages, summary

from iatidq.models import *

import usermanagement

@app.route("/packages/manage/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def packages_manage():
    if request.method != 'POST':
        pkgs = Package.query.order_by(Package.package_name).all()
        return render_template("packages_manage.html", pkgs=pkgs)

    if "refresh" in request.form:
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


def package_aggregation(p, latest_runtime):
    return db.session.query(
        Indicator,
        Test,
        AggregateResult.results_data,
        AggregateResult.results_num,
        AggregateResult.result_hierarchy
        ).filter(
        AggregateResult.package_id==p[0].id,
        AggregateResult.runtime_id==latest_runtime.id
        ).group_by(
            AggregateResult.result_hierarchy, 
            Test,
            AggregateResult.results_data,
            AggregateResult.results_num,
            Indicator
            ).join(
            IndicatorTest
            ).join(
                Test
                ).join(
                AggregateResult
                ).all()
                   
@app.route("/packages/")
@app.route("/packages/<package_name>/")
@app.route("/packages/<package_name>/runtimes/<runtime_id>/")
def packages(package_name=None, runtime_id=None):
    if package_name is None:
        packages = Package.query.filter_by(active=True).order_by(
            Package.package_name).all()
        return render_template("packages.html", packages=packages)

    # Get package data
    package = db.session.query(Package,
                         PackageGroup
                         ).filter(Package.package_name == package_name
                                  ).outerjoin(PackageGroup).first()

    def get_pconditions():
        return {}
        # Publisher conditions have been removed in favour
        #  of organisation conditions. need to consider how to
        #  possibly include this again here.
        """if p is None:
            p = db.session.query(Package).\
                filter(Package.package_name == id).first()
            return {}
        else:
        # Get publisher-specific conditions.
            return PublisherCondition.query.filter_by(
                publisher_id=p[1].id).all()"""

    pconditions = get_pconditions()

    # Get list of runtimes
    try:
        runtimes = db.session.query(AggregateResult.runtime_id,
                                    Runtime.runtime_datetime
            ).filter(AggregateResult.package_id==package.Package.id
            ).distinct(
            ).join(Runtime
            ).all()
    except Exception:
        return abort(404)

    def get_latest_runtime():
        if runtime_id:
            # If a runtime is specified in the request, get the data
            return (db.session.query(Runtime
                        ).filter(Runtime.id==runtime_id
                        ).first(), False)
        else:
            # Select the highest runtime; then get data for that one
            runtime = db.session.query(Runtime,
                                    func.max(Runtime.id)
                    ).join(AggregateResult
                    ).group_by(Runtime.id
                    ).filter(AggregateResult.package_id==package.Package.id
                    ).first()
            return runtime.Runtime, True

    latest_runtime, latest = get_latest_runtime()

    if latest_runtime:
        aggregate_results = package_aggregation(package, latest_runtime)

        aggregate_results = summary.agr_results(aggregate_results, 
                                                    pconditions)
    else:
        aggregate_results = None
        pconditions = None
        flat_results = None
        latest_runtime = None

    organisations = dqpackages.packageOrganisations(package.Package.id)
 
    return render_template("package.html", package=package, runtimes=runtimes, 
                           results=aggregate_results, 
                           latest_runtime=latest_runtime, latest=latest, 
                           pconditions=pconditions,
organisations=organisations)


#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import current_user

from iatidataquality import app
from iatidataquality import db

from iatidq import dqdownload, dqregistry, dqindicators, dqorganisations, dqpackages, summary, dqaggregationtypes, dqusers

from iatidq.models import *

import usermanagement

def integerise(data):
    try:
        return int(data)
    except ValueError:
        return None
    except TypeError:
        return None

@app.route("/packages/manage/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def packages_manage():
    if request.method != 'POST':
        pkgs = Package.query.order_by(Package.package_name).all()
        return render_template("packages_manage.html", 
             pkgs=pkgs,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

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

def package_aggregation(p, latest_runtime, aggregation_type):
    return db.session.query(
        Indicator,
        Test,
        AggregateResult.results_data,
        AggregateResult.results_num,
        AggregateResult.result_hierarchy,
        AggregateResult.package_id
        ).filter(
        AggregateResult.package_id==p[0].id,
        AggregateResult.runtime_id==latest_runtime.id,
        AggregateResult.aggregateresulttype_id==aggregation_type
        ).group_by(
            AggregateResult.result_hierarchy, 
            Test,
            AggregateResult.package_id,
            Indicator,
            AggregateResult.results_data,
            AggregateResult.results_num,
            AggregateResult.package_id
            ).join(IndicatorTest
            ).join(Test
            ).join(AggregateResult
            ).all()
                   
@app.route("/packages/new/", methods=['POST', 'GET'])
@app.route("/packages/<package_name>/edit/", methods=['POST', 'GET'])
def packages_edit(package_name=None):
    if request.method=='GET':
        if package_name is not None:
            package = dqpackages.packages_by_name(package_name)
            # Get only first organisation (this is a hack,
            # but unlikely we will need to add a package
            # to more than one org)
            try:
                package_org_id = dqpackages.packageOrganisations(package.id)[0].Organisation.id
            except IndexError:
                package_org_id=None
            if package.man_auto=='auto':
                flash("That package is not a manual package, so it can't be edited.", 'error')
                return redirect(url_for('packages'))
        else:
            package ={}
            package_org_id = ""
        organisations=dqorganisations.organisations()
        return render_template("package_edit.html", 
             package=package,
             package_org_id = package_org_id,
             organisations=organisations,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)
    else:
        if 'active' in request.form:
            active = True
        else:
            active = False

        data = {
            'package_name' : request.form.get('package_name'),
            'package_title' : request.form.get('package_title'),
            'source_url' : request.form.get('source_url'),
            'man_auto' : 'man',
            'active': active,
            'hash': request.form.get('hash')
        }
        package_org_id=request.form.get('organisation')
        if package_name is not None:
            pkg = dqpackages.packages_by_name(package_name)
            data['package_id'] = pkg.id
            package = dqpackages.updatePackage(data)
            mode = 'updated'
        else:
            data['package_name'] = 'manual_' + data['package_name']
            package = dqpackages.addPackage(data)
            mode = 'added'
        if package:
            if (package_org_id is not None) and (package_org_id != ""):
                pkorg = dqorganisations.addOrganisationPackage({
                    'organisation_id': package_org_id,
                    'package_id': package.id,
                    'condition': None
                })
            # TODO: attach package to organisation
            flash("Successfully "+mode+" package.", 'success')
            return redirect(url_for('packages_edit', package_name=package.package_name))
        else:
            flash("There was an error, and the package could not be "+mode+".", "error")
            organisations=dqorganisations.organisations()
            data['package_name'] = request.form.get('package_name')
        return render_template("package_edit.html", 
             package=data,
             package_org_id = package_org_id,
             organisations=organisations,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

@app.route("/packages/")
@app.route("/packages/<package_name>/")
@app.route("/packages/<package_name>/runtimes/<runtime_id>/")
def packages(package_name=None, runtime_id=None):
    if package_name is None:
        packages = Package.query.filter_by(active=True).order_by(
            Package.package_name).all()
        return render_template("packages.html", 
             packages=packages,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

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

    #pconditions = get_pconditions()
    pconditions = {}

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

    try:
        latest_runtime, latest = get_latest_runtime()
    except Exception:
        latest_runtime = None
        latest = None

    aggregation_type=integerise(request.args.get('aggregation_type', 2))
    all_aggregation_types = dqaggregationtypes.aggregationTypes()

    if latest_runtime:
        aggregate_results = package_aggregation(package, latest_runtime, aggregation_type)

        aggregate_results = summary.agr_results(aggregate_results, 
                                                   pconditions, 
                                                mode="publisher")
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
                           organisations=organisations,
                           all_aggregation_types=all_aggregation_types,
                           aggregation_type=aggregation_type,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user)

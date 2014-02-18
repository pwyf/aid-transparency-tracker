
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
from sqlalchemy import func
from datetime import datetime
from flask.ext.login import current_user
import usermanagement

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

import StringIO
import unicodecsv
import tempfile
import spreadsheet

@app.route("/publishers/")
def publishers():
    p_groups = PackageGroup.query.order_by(
        PackageGroup.name).all()

    pkgs = Package.query.order_by(Package.package_name).all()
    return render_template("packagegroups.html", p_groups=p_groups, 
             pkgs=pkgs,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

def _publisher_detail_ungrouped(p_group):
    return db.session.query(Indicator,
                                     Test.id,
                                     AggregateResult.results_data,
                                     AggregateResult.results_num,
                                     AggregateResult.result_hierarchy,
                                     AggregateResult.package_id,
                                     func.max(AggregateResult.runtime_id)
        ).filter(PackageGroup.id==p_group.id)

## FIXME: major duplication of code deteceted
def _publisher_detail(p_group):
    aggregate_results = _publisher_detail_ungrouped(p_group)\
        .group_by(Indicator,
                   AggregateResult.result_hierarchy, 
                   Test.id, 
                   AggregateResult.package_id,
                   AggregateResult.results_data,
                   AggregateResult.results_num
        ).join(IndicatorTest
        ).join(Test
        ).join(AggregateResult
        ).join(Package
        ).join(PackageGroup
        ).all()

    """pconditions = PublisherCondition.query.filter_by(
        publisher_id=p_group.id).all()"""
    # Publisherconditions have been removed in favour
    #  of organisation conditions
    pconditions = {}

    s = summary.PublisherSummary(aggregate_results, conditions=pconditions)
    return s.summary()

@app.route("/publishers/<id>/detail")
def publisher_detail(id=None):
    p_group = PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(Package
            ).filter(Package.package_group == p_group.id
            ).order_by(Package.package_name).all()

    aggregate_results = _publisher_detail(p_group)

    return render_template("publisher.html", p_group=p_group, pkgs=pkgs, 
                           results=aggregate_results,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

@app.route("/publishers/<id>/detail.json")
def publisher_detail_json(id=None):
    p_group = PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(Package
            ).filter(Package.package_group == p_group.id
            ).order_by(Package.package_name).all()

    aggregate_results = _publisher_detail(p_group)
    latest_runtime=1
    """except Exception, e:
        latest_runtime = None
        aggregate_results = None"""

    return json.dumps(aggregate_results, indent=2)

@app.route("/publishers/<id>/detail.csv")
def publisher_detail_csv(id=None):
    p_group = PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(Package
            ).filter(Package.package_group == p_group.id
            ).order_by(Package.package_name).all()

    aggregate_results = _publisher_detail(p_group)
    latest_runtime=1
    """except Exception, e:
        latest_runtime = None
        aggregate_results = None"""

    print >>sys.stderr, aggregate_results.keys()
    print "---"

    def gen_csv():
        s = StringIO.StringIO()
        w = unicodecsv.writer(s)
        for k, v in aggregate_results[1].iteritems():
            s.seek(0)
            w.writerow((k, v["test"]["description"]))
            s.seek(0)
            yield s.read()

    return Response(gen_csv(), mimetype="text/csv")

@app.route("/publishers/<id>/detail.xls")
def publisher_detail_xls(id=None):
    p_group = PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(Package
            ).filter(Package.package_group == p_group.id
            ).order_by(Package.package_name).all()

    aggregate_results = _publisher_detail(p_group)
    latest_runtime=1
    """except Exception, e:
        latest_runtime = None
        aggregate_results = None"""

    print >>sys.stderr, aggregate_results.keys()
    print "---"

    filename = tempfile.mktemp()
    try:
        spreadsheet.workbook_from_aggregation(filename, aggregate_results)
        with file(filename) as f:
            data = f.read()
            return Response(data, mimetype='application/vnd.ms-excel')
    finally:
        if os.path.exists(filename):
            os.unlink(filename)

def publisher_summary(publisher_id, p_group):
    aggregate_results = _publisher_detail_ungrouped(p_group)\
        .group_by(AggregateResult.result_hierarchy, 
                   Test.id, 
                   AggregateResult.package_id,
                   Indicator,
                   AggregateResult.results_data,
                   AggregateResult.results_num,
                   AggregateResult.package_id
        ).join(IndicatorTest
        ).join(Test
        ).join(AggregateResult
        ).join(Package
        ).join(PackageGroup
        ).all()

    pconditions = {}

    s = summary.PublisherIndicatorsSummary(aggregate_results, 
                                           conditions=pconditions)
    return s.summary()


@app.route("/publishers/<publisher_id>/")
def publisher(publisher_id=None):
    p_group = PackageGroup.query.filter_by(name=publisher_id).first_or_404()

    pkgs = db.session.query(Package
            ).filter(Package.package_group == p_group.id
            ).order_by(Package.package_name).all()

    aggregate_results = publisher_summary(publisher_id, p_group)

    latest_runtime=1

    return render_template("publisher_indicators.html", 
                           p_group=p_group, pkgs=pkgs, 
                           results=aggregate_results, runtime=latest_runtime,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user)


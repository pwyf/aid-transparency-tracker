
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

from iatidq import models, dqdownload, dqregistry, dqindicators, dqorganisations, dqpackages
import aggregation

import StringIO
import unicodecsv
import tempfile
import spreadsheet

@app.route("/publishers/")
def publishers():
    p_groups = models.PackageGroup.query.order_by(
        models.PackageGroup.name).all()

    pkgs = models.Package.query.order_by(models.Package.package_name).all()
    return render_template("packagegroups.html", p_groups=p_groups, pkgs=pkgs)

def _publisher_detail(p_group):
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

    db.session.commit()
    return aggregation.agr_results(aggregate_results, 
                                   conditions=pconditions, 
                                   mode="publisher")

@app.route("/publishers/<id>/detail")
def publisher_detail(id=None):
    p_group = models.PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Package.package_group == p_group.id
            ).order_by(models.Package.package_name).all()

    aggregate_results = _publisher_detail(p_group)
    latest_runtime=1

    txt = render_template("publisher.html", p_group=p_group, pkgs=pkgs, 
                           results=aggregate_results, runtime=latest_runtime)
    return txt

@app.route("/publishers/<id>/detail.json")
def publisher_detail_json(id=None):
    p_group = models.PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Package.package_group == p_group.id
            ).order_by(models.Package.package_name).all()

    aggregate_results = _publisher_detail(p_group)
    latest_runtime=1
    """except Exception, e:
        latest_runtime = None
        aggregate_results = None"""

    return json.dumps(aggregate_results, indent=2)

@app.route("/publishers/<id>/detail.csv")
def publisher_detail_csv(id=None):
    p_group = models.PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Package.package_group == p_group.id
            ).order_by(models.Package.package_name).all()

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
    p_group = models.PackageGroup.query.filter_by(name=id).first_or_404()

    pkgs = db.session.query(models.Package
            ).filter(models.Package.package_group == p_group.id
            ).order_by(models.Package.package_name).all()

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


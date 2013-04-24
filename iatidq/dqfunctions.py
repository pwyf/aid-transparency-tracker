
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import json
import urllib2
import sys
import itertools

from iatidq import db
import models

RESULT_FAILURE = 0
RESULT_SUCCESS = 1

FIELD_TEST = 0
FIELD_STATUS = 1
FIELD_HIERARCHY = 2
FIELD_RESULT = 3
FIELD_PACKAGE = 4
FIELD_ORGANISATION = 5

def prepend(prefix, tup):
    return tuple([prefix] + list(tup))

def _aggregate_percentages(data, dims):
    dims_dict = dict(dims)

    def setmap(lam):
        return set(map(lam, data))

    dim_names = [ i[0] for i in dims ]

    def generate_dimension(dimension_name):
        return setmap(dims_dict[dimension_name])

    dimension_lists = map(generate_dimension, dim_names)

    def lookups(x):
        return tuple([ dims_dict[i](x) for i in dim_names ])

    breakdown = lambda x: (
        prepend(x[FIELD_STATUS], lookups(x)),
        x[FIELD_RESULT]
        )

    d = dict(map(breakdown, data))
    out = []

    def calc_percentages(dimensions):
        fail    = d.get(prepend(RESULT_FAILURE, dimensions), 0)
        success = d.get(prepend(RESULT_SUCCESS, dimensions),.0)

        if 0 == fail + success:
            return None
        percentage = int((float(success)/(fail+success)) * 100)

        data = {
            "percentage_passed": percentage,
            "total_results": fail+success,
            }
        for i, dim in enumerate(dim_names):
            data[dim] = dimensions[i]
        return data

    out = map(calc_percentages, itertools.product(*dimension_lists))
    out = filter(lambda i: i is not None, out)

    return out

def aggregate_percentages(data):
    # Aggregates results data for a specific runtime.

    dims = [
        ("package_id", lambda x: x[FIELD_PACKAGE]),
        ("test_id",    lambda x: x[FIELD_TEST].id),
        ("hierarchy",  lambda x: x[FIELD_HIERARCHY])
        ]

    return _aggregate_percentages(data, dims)

def aggregate_percentages_org(data):
    # Aggregates results data for a specific runtime.

    dims = [
        ("package_id", lambda x: x[FIELD_PACKAGE]),
        ("test_id",    lambda x: x[FIELD_TEST].id),
        ("hierarchy",  lambda x: x[FIELD_HIERARCHY]),
        ("organisation_id", lambda x: x[FIELD_ORGANISATION])
        ]

    return _aggregate_percentages(data, dims)

def add_test_status(package_id, status_id, commit=True):
    pstatus = models.PackageStatus()
    pstatus.package_id = package_id
    pstatus.status = status_id
    db.session.add(pstatus)
    if (commit):
        db.session.commit()

def clear_revisions():
    for pkg in models.Package.query.filter(
        models.Package.package_revision_id!=None, 
        models.Package.active == True
        ).all():

        pkg.package_revision_id = None
        
        db.session.add(pkg)
    db.session.commit()

def packages_from_registry(registry_url):
    offset = 0
    while True:
        data = urllib2.urlopen(registry_url % (offset), timeout=60).read()
        print (registry_url % (offset))
        data = json.loads(data)

        if len(data["results"]) < 1:
            break          

        for pkg in data["results"]:
            yield pkg

        offset += 1000

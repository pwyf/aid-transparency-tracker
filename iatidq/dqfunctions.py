
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import json
import urllib2

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

def aggregate_percentages(data):
    # Aggregates results data for a specific runtime.

    packages = set(map(lambda x: (x[FIELD_PACKAGE]), data))
    hierarchies = set(map(lambda x: (x[FIELD_HIERARCHY]), data))
    tests = set(map(lambda x: (x[FIELD_TEST].id), data))

    d = dict(map(lambda x: ((x[FIELD_STATUS],
                             x[FIELD_TEST].id,
                             x[FIELD_HIERARCHY],
                             x[FIELD_PACKAGE]),(x[FIELD_RESULT])), data))
    out = []
    for p in packages:
        for t in tests:
            for h in hierarchies:
                fail    = d.get((RESULT_FAILURE, t, h, p), 0)
                success = d.get((RESULT_SUCCESS, t, h, p),.0)

                if 0 == fail + success:
                    continue
                percentage = int((float(success)/(fail+success)) * 100)

                data = {}
                data = {
                    "test_id": t,
                    "percentage_passed": percentage,
                    "total_results": fail+success,
                    "hierarchy": h,
                    "package_id": p
                }
                out.append(data)
    return out

def aggregate_percentages_org(data):
    # Aggregates results data for a specific runtime.

    packages = set(map(lambda x: (x[FIELD_PACKAGE]), data))
    hierarchies = set(map(lambda x: (x[FIELD_HIERARCHY]), data))
    tests = set(map(lambda x: (x[FIELD_TEST].id), data))
    organisations = set(map(lambda x: (x[FIELD_ORGANISATION]), data))

    d = dict(map(lambda x: ((x[FIELD_STATUS],
                             x[FIELD_TEST].id,
                             x[FIELD_HIERARCHY],
                             x[FIELD_PACKAGE],
                             x[FIELD_ORGANISATION]),(x[FIELD_RESULT])), data))
    out = []
    for p in packages:
        for t in tests:
            for h in hierarchies:
                for o in organisations:
                    fail    = d.get((RESULT_FAILURE, t, h, p, o), 0)
                    success = d.get((RESULT_SUCCESS, t, h, p, o), 0)

                    if 0 == fail + success:
                        continue
                    percentage = int((float(success)/(fail+success)) * 100)

                    data = {}
                    data = {
                        "test_id": t,
                        "percentage_passed": percentage,
                        "total_results": fail+success,
                        "hierarchy": h,
                        "package_id": p,
                        "organisation_id": o
                        }
                    out.append(data)
    return out

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

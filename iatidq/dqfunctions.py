
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

def aggregate_percentages(data):
    # Aggregates results data for a specific runtime.

    packages = set(map(lambda x: (x[4]), data))
    hierarchies = set(map(lambda x: (x[2]), data))
    tests = set(map(lambda x: (x[0].id), data))

    d = dict(map(lambda x: ((x[0].id,x[1],x[2],x[4]),(x[3])), data))
    out = []
    for p in packages:
        for t in tests:
            for h in hierarchies:
                try: fail = d[(t,0,h,p)]
                except: fail = 0
                try: success = d[(t,1,h,p)]
                except: success = 0
                try:
                    percentage = int((float(success)/(fail+success)) * 100)
                except ZeroDivisionError:
                    # Don't return data to DB if there are no results
                    continue
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

    packages = set(map(lambda x: (x[4]), data))
    hierarchies = set(map(lambda x: (x[2]), data))
    tests = set(map(lambda x: (x[0].id), data))
    organisations = set(map(lambda x: (x[5]), data))

    d = dict(map(lambda x: ((x[0].id,x[1],x[2],x[4],x[5]),(x[3])), data))
    out = []
    for p in packages:
        for t in tests:
            for h in hierarchies:
                for o in organisations:
                    try: fail = d[(t,0,h,p,o)]
                    except: fail = 0
                    try: success = d[(t,1,h,p,o)]
                    except: success = 0
                    try:
                        percentage = int((float(success)/(fail+success)) * 100)
                    except ZeroDivisionError:
                        # Don't return data to DB if there are no results
                        continue
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

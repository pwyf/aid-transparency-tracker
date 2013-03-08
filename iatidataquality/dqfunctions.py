
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import json
import urllib2

from iatidataquality import db
import models

def aggregate_percentages(data):
    # Aggregates results data for a specific runtime.

    packages = set(map(lambda x: (x[4]), data))
    hierarchies = set(map(lambda x: (x[2]), data))
    tests = set(map(lambda x: (x[0].id, x[0].description, x[0].test_group), data))
    
    d = dict(map(lambda x: ((x[0].id,x[1],x[2],x[4]),(x[3])), data))
    out = []
    for p in packages:
        for t in tests:
            for h in hierarchies:
                try: fail = d[(t[0],0,h,p)]
                except: fail = 0
                try: success = d[(t[0],1,h,p)]
                except: success = 0
                try:
                    percentage = int((float(success)/(fail+success)) * 100)
                except ZeroDivisionError:
                    # Don't return data to DB if there are no results
                    continue
                data = {}
                data = {
                    "test_id": t[0],
                    "percentage_passed": percentage,
                    "total_results": fail+success,
                    "hierarchy": h,
                    "package_id": p
                }
                out.append(data)
    return out

def pkg_test_percentages(data):
    # Returns results data - % for each hierarchy for each test, for a specific package in a specific runtime.
    # Remove in future and revert to AggregateResult data.

    hierarchies = set(map(lambda x: (x[2]), data))
    tests = set(map(lambda x: (x[0].id, x[0].description, x[0].test_group), data))
    
    d = dict(map(lambda x: ((x[0].id,x[1],x[2]),(x[3])), data))
    out = {}
    for t in tests:
        for h in hierarchies:
            try: fail = d[(t[0],0,h)]
            except: fail = 0
            try: success = d[(t[0],1,h)]
            except: success = 0
            try:
                percentage = int((float(success)/(fail+success)) * 100)
            except ZeroDivisionError:
                percentage = 0
            data = {}
            data = {
                "id": t[0],
                "name": t[1],
                "percentage": percentage,
                "total_results": fail+success,
                "group": t[2]
            }
            try: out[h]
            except KeyError: out[h] = {}
            try: out[h][t]
            except KeyError: out[h][t] = {}
            out[h][t] = data
    return out

def _agr_results(data, conditions=None, mode=None):
    """
        data variable looks like this:
            models.Test,
            models.AggregateResult.results_data, ## percentage
            models.AggregateResult.results_num, ## total values
            models.AggregateResult.result_hierarchy

        conditions variable looks like this:
            models.PublisherCondition.query.filter_by(publisher_id=p[1].id).all()

            ======================================
            id = Column(Integer, primary_key=True)
            publisher_id = Column(Integer, ForeignKey('packagegroup.id'))
            test_id = Column(Integer, ForeignKey('test.id'))
            operation = Column(Integer) # show (1) or don't show (0) result
            condition = Column(UnicodeText) # activity level, hierarchy 2
            condition_value = Column(UnicodeText) # True, 2, etc.
            description = Column(UnicodeText)
            file = Column(UnicodeText)
            line = Column(Integer)
            active = Column(Boolean)
            ======================================
        mode can be:
            None = package-specific
            "publisher" = aggregate results for a whole publisher

        TODO:
            in publisher mode, allow weighting of data by package rather than number of activities.
    """

    hierarchies = set(map(lambda x: (x[3]), data))
    tests = set(map(lambda x: (x[0]["id"]), data))

    cdtns = None
    if conditions:
        cdtns = dict(map(lambda x: ((x.test_id, x.condition, x.condition_value, x.operation),(x.description)), conditions))
    
    if (mode=="publisher"):
        packages = set(map(lambda x: (x[4]), data))
        d = dict(map(lambda x: ((x[3], x[0]["id"], x[4]),(x)), data))
    else:
        d = dict(map(lambda x: ((x[3], x[0]["id"]),(x)), data))

    out = {}

    for h in hierarchies:
        
        for t in tests:
            if (mode=="publisher"):
                # aggregate data across multiple packages for a single publisher

                # for each package, add percentage for each
                total_pct = 0
                total_activities = 0
                total_packages = len(packages)
                for p in packages:
                    try:
                        ok_tdata = d[(h, t, p)]
                        total_pct += ok_tdata[1] #percentage
                        total_activities += ok_tdata[2] #total vals
                    except KeyError:
                        pass
                
                if (total_activities>0):
                    
                    tdata = {
                        "test": {
                            "id": ok_tdata[0]["id"],
                            "description": ok_tdata[0]["description"],
                            "test_group": ok_tdata[0]["test_group"]
                            },
                        "results_pct": int(float(total_pct/total_packages)),
                        "results_num": total_activities,
                        "result_hierarchy": total_activities
                        }
            else:
                # return data for this single package
                try:
                    tdata = d[(h, t)]
                except KeyError:
                    tdata = None

            try: out[h]
            except KeyError: out[h] = {}
            try: out[h][t]
            except KeyError: out[h][t] = {}
            try: 
                if tdata:
                    out[h][t]["test"] = tdata
                try:
                    out[h][t]["condition"] = cdtns[(t,'activity hierarchy', str(h), 0)]
                except KeyError:
                    # cdtns[...] doesn't exist
                    pass
                except UnboundLocalError:
                    # cdtns doesn't exist
                    pass
            except KeyError: del out[h][t]
            except UnboundLocalError: del out[h][t]
            try:
                if (out[h][t] == {}): del out[h][t]
            except KeyError:
                pass
    return out

def agr_results(data, conditions=None, mode=None):
    def replace_first(tupl, newval):
        return tuple([newval] + list(tupl)[1:])
    switch_first = lambda t: replace_first(t, t[0].as_dict())
    fixed_data = map(switch_first, data)
    results = _agr_results(fixed_data, conditions, mode)
    return results

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

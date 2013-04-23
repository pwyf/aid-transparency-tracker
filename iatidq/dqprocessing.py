
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db, dqfunctions, dqpackages
import models
from sqlalchemy import func

def add_hardcoded_result(test_id, runtime_id, package_id, result_data):
    result = models.Result()
    result.test_id = test_id 
    result.runtime_id = runtime_id
    result.package_id = package_id
    result.result_data = int(bool(result_data))
    db.session.add(result)

def aggregate_results(runtime, package_id):
        # for each package, get results for this runtime
        # compute % pass for each hierarchy and test
        # write to db
    check_existing_results = db.session.query(models.AggregateResult
            ).filter(models.AggregateResult.runtime_id==runtime
            ).filter(models.AggregateResult.package_id==package_id
            ).first()
    
    if check_existing_results:
        status = "Already aggregated"
        aresults = "None"
        return {"status": status, "data": aresults}

    def get_organisation_ids():
        return [ o.Organisation.id for o in 
                 dqpackages.packageOrganisations(package_id) ]

    status = "Updating"

    agg_types = models.AggregationType.query.all()
    if len(agg_types) == 0:
        return {"status": status, "data": []}

    organisation_ids = get_organisation_ids()

    for agg_type in agg_types:
        if len(organisation_ids) > 0:
            return aggregate_results_orgs(runtime, package_id, 
                                          organisation_ids, agg_type)
        else:
            return aggregate_results_single_org(runtime, package_id, agg_type)

def get_results(agg_type):
    results = models.Result.query.filter(
        models.Result.test_id == agg_type.id
        ).filter(
        models.Result.result_identifier == '1'
        ).all()
    
    return set([r.id for r in results])

def aggregate_results_single_org(runtime, package_id, agg_type):
    result_ids = get_results(agg_type)

    data = db.session.query(models.Test,
                models.Result.result_data,
                models.Result.result_hierarchy,
                func.count(models.Result.id),
                models.Result.package_id
        ).filter(models.Result.runtime_id==runtime
        ).filter(models.Result.package_id==package_id
        ).filter(models.Result.id.in_(result_ids)
        ).join(models.Result
        ).group_by(models.Result.package_id, 
                   models.Result.result_hierarchy, 
                   models.Test.id, 
                   models.Result.result_data
        ).all()

    aresults = dqfunctions.aggregate_percentages(data)
        
    for aresult in aresults:
        a = models.AggregateResult()
        a.runtime_id = runtime
        a.package_id = aresult["package_id"]
        a.test_id = aresult["test_id"]
        a.result_hierarchy = aresult["hierarchy"]
        a.results_data = aresult["percentage_passed"]
        a.results_num = aresult["total_results"]
        a.aggregateresulttype_id = agg_type.id
        db.session.add(a)
    
    return {"status": status, "data": aresults}

def aggregate_results_orgs(runtime, package_id, organisation_ids, agg_type):
    status = "Updating"
    result_ids = get_results(agg_type)

    data = db.session.query(models.Test,
                models.Result.result_data,
                models.Result.result_hierarchy,
                func.count(models.Result.id),
                models.Result.package_id,
                models.Result.organisation_id
        ).filter(models.Result.runtime_id==runtime
        ).filter(models.Result.package_id==package_id
        ).join(models.Result
        ).group_by(models.Result.package_id, 
                   models.Result.result_hierarchy, 
                   models.Result.organisation_id,
                   models.Test.id, 
                   models.Result.result_data
        ).all()

    aresults = dqfunctions.aggregate_percentages_org(data)
        
    for aresult in aresults:
        a = models.AggregateResult()
        a.runtime_id = runtime
        a.package_id = aresult["package_id"]
        a.test_id = aresult["test_id"]
        a.result_hierarchy = aresult["hierarchy"]
        a.results_data = aresult["percentage_passed"]
        a.results_num = aresult["total_results"]
        a.organisation_id = aresult["organisation_id"]
        db.session.add(a)
    
    return {"status": status, "data": aresults}

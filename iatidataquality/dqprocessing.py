
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidataquality import db, dqfunctions
import models
from sqlalchemy import func

def add_hardcoded_result(test_id, runtime_id, package_id, result_data):
    result = models.Result()
    result.test_id = test_id 
    result.runtime_id = runtime_id
    result.package_id = package_id
    if result_data:
        result.result_data = 1
    else:
        result.result_data = 0 
    db.session.add(result)

def aggregate_results(runtime, package_id):
        # for each package, get results for this runtime
        # compute % pass for each hierarchy and test
        # write to db
    check_existing_results = db.session.query(models.AggregateResult
            ).filter(models.AggregateResult.runtime_id==runtime
            ).filter(models.AggregateResult.package_id==package_id
            ).first()
    
    if (check_existing_results):
        status = "Already aggregated"
        aresults = "None"
    else:
        status = "Updating"
        data = db.session.query(models.Test,
                models.Result.result_data,
                models.Result.result_hierarchy,
                func.count(models.Result.id),
                models.Result.package_id
        ).filter(models.Result.runtime_id==runtime
        ).filter(models.Result.package_id==package_id
        ).join(models.Result
        ).group_by(models.Result.package_id, models.Result.result_hierarchy, models.Test, models.Result.result_data
        ).all()

        aresults = dqfunctions.aggregate_percentages(data)
        
        result_number = 0
        for aresult in aresults:
            a = models.AggregateResult()
            a.runtime_id = runtime
            a.package_id = aresult["package_id"]
            a.test_id = aresult["test_id"]
            a.result_hierarchy = aresult["hierarchy"]
            a.results_data = aresult["percentage_passed"]
            a.results_num = aresult["total_results"]
            db.session.add(a)
    
    return {"status": status, "data": aresults}

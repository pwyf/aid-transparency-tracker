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

def agr_results(data):
    hierarchies = set(map(lambda x: (x[3]), data))
    tests = set(map(lambda x: (x[0].id), data))
    
    d = dict(map(lambda x: ((x[3], x[0].id),(x)), data))
    out = {}
    for h in hierarchies:
        for t in tests:
            try: out[h]
            except KeyError: out[h] = {}
            try: out[h][t]
            except KeyError: out[h][t] = {}
            try: out[h][t] = d[(h, t)]
            except KeyError: del out[h][t]
    return out

def agr_publisher_results(data, activities=None):
    # TO DO: activities = True, aggregates percentage by number of activities in each file
    
    """
       data variable looks like this:
         models.Test,
         models.AggregateResult.results_data,
         models.AggregateResult.results_num,
         models.AggregateResult.result_hierarchy,
         models.AggregateResult.package_id
    """
    packages = set(map(lambda x: (x[4]), data))
    hierarchies = set(map(lambda x: (x[3]), data))
    tests = set(map(lambda x: (x[0].id), data))
    
    d = dict(map(lambda x: ((x[3], x[0].id, x[4]),(x)), data))
    out = {}
    for h in hierarchies:
        for t in tests:
            total_pct = 0
            total_activities = 0
            test_id = ""
            test_name = ""
            test_description = ""
            total_packages = len(packages)
            for p in packages:
                try:
                    total_pct = total_pct + d[(h, t, p)][1]
                    total_activities = total_activities + d[(h, t, p)][2]
                    test_id = d[(h, t, p)][0].id
                    test_name = d[(h, t, p)][0].name
                    test_description = d[(h, t, p)][0].description
                except KeyError:
                    pass
            if (total_activities>0):
                tdata = {
                        'percentage': int(float(total_pct)/(total_packages)),
                        'total_num': total_activities,
                        'test_id': test_id,
                        'test_name': test_name,
                        'test_description': test_description
                       }

                try: out[h]
                except KeyError: out[h] = {}
                try: out[h][t]
                except KeyError: out[h][t] = {}
                try: out[h][t] = tdata
                except KeyError: del out[h][t]
                if (out[h][t] == {}): del out[h][t]
    return out

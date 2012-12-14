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

def agr_results(data, conditions=None, mode=None):
    """
        data variable looks like this:
            models.Test,
            models.AggregateResult.results_data,
            models.AggregateResult.results_num,
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
    tests = set(map(lambda x: (x[0].id), data))

    if conditions:
        cdtns = dict(map(lambda x: ((x.test_id, x.condition, x.condition_value, x.operation),(x.description)), conditions))
    
    if (mode=="publisher"):
        packages = set(map(lambda x: (x[4]), data))
        d = dict(map(lambda x: ((x[3], x[0].id, x[4]),(x)), data))
    else:
        d = dict(map(lambda x: ((x[3], x[0].id),(x)), data))

    out = {}
    for h in hierarchies:
        for t in tests:
            if (mode=="publisher"):
                # aggregate data across multiple packages for a single publisher
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
            else:
                # return data for this single package
                try:
                    tdata = d[(h, t)]
                except KeyError:
                    pass
            try: out[h]
            except KeyError: out[h] = {}
            try: out[h][t]
            except KeyError: out[h][t] = {}
            try: 
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
    return out

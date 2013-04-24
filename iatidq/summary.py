
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

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
            models.Indicator,
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

    hierarchies = set(map(lambda x: (x[4]), data))
    tests = set(map(lambda x: (x[1].id), data))

    cdtns = None
    if conditions:
        cdtns = dict(map(lambda x: (
                    (x.test_id, x.condition, x.condition_value),
                    (x.operation, x.description)
                    ), conditions))
    
    if ((mode=="publisher") or (mode=="publisher_simple") or (mode=="publisher_indicators")):
        indicators = set(map(lambda x: (x[0]["id"], (x[0]["name"], x[0]["description"])), data))
        indicators_tests = list(set(map(lambda x: (x[0]["id"], x[1].id), data)))
        packages = set(map(lambda x: (x[5]), data))
        d = dict(map(lambda x: ((x[4], x[1].id, x[5]),(x)), data))
    else:
        d = dict(map(lambda x: ((x[4], x[1].id),(x)), data))

    out = {}


    for h in hierarchies:
        for t in tests:
            all_pcts = []
            tdata = {}
            if ((mode=="publisher") or (mode=="publisher_simple") or (mode=="publisher_indicators")):
                # aggregate data across multiple packages for a single publisher

                # for each package, add percentage for each
                total_pct = 0
                total_activities = 0
                total_packages = len(packages)

                # need below to only include packages that are in this hierarchy
                packages_in_hierarchy = 0
                for p in packages:
                    try:
                        ok_tdata = d[(h, t, p)]
                        total_pct += ok_tdata[2] #percentage
                        total_activities += ok_tdata[3] #total vals
                        packages_in_hierarchy +=1
                    except KeyError:
                        pass
                if (total_activities>0):
                    
                    tdata = {
                        "indicator": ok_tdata[0],
                        "test": {
                            "id": ok_tdata[1].id,
                            "description": ok_tdata[1].description,
                            "test_group": ok_tdata[1].test_group
                            },
                        "results_pct": int(float(total_pct/packages_in_hierarchy)),
                        "results_num": total_activities,
                        "result_hierarchy": total_activities
                        }
            else:
                # return data for this single package
                data = d.get((h, t), None)
                if data is not None:
                    tdata = {
                        "test": {
                            "id": data[1].id,
                            "description": data[1].description,
                            "test_group": data[1].test_group
                            },
                        "results_pct": data[2],
                        "results_num": data[3],
                        "result_hierarchy": data[4]
                        }
                else:
                    tdata = None

            if h not in out:
                out[h] = {}

            if t not in out[h]:
                out[h][t] = {}

            if tdata:
                out[h][t] = tdata
            if conditions:
                key = (t,'activity hierarchy', str(h)) 
                if key in cdtns:
                    out[h][t]["condition"] = cdtns[key]

            try:
                if (out[h][t] == {}): del out[h][t]
            except KeyError:
                pass
    if mode not in ["publisher_simple", "publisher_indicators"]:
        return out
    else:
        simple_out = {}
        hierarchies = set(out)
        tests = set()
        for h in hierarchies:
            tests.update(set(out[h]))
        for t in tests: 
            results_pct = 0.0
            results_num = 0.0
            results_weighted_pct_average_numerator = 0.0
            for hierarchy in hierarchies:
                try:
                    key = (t,'activity hierarchy', str(hierarchy)) 
                    try:
                        if ((cdtns) and (key in cdtns) and (cdtns[key][0]==0)):
                            continue
                    except KeyError:
                        pass
                    results_pct+= out[hierarchy][t]["results_pct"]
                    results_num+= out[hierarchy][t]["results_num"]
                    results_weighted_pct_average_numerator += (out[hierarchy][t]["results_pct"]*out[hierarchy][t]["results_num"])
                    okhierarchy = hierarchy
                except KeyError:
                    pass

            simple_out[t] = {
                    "indicator": out[okhierarchy][t]['indicator'],
                    "test": {
                        "id": out[okhierarchy][t]['test']["id"],
                        "description": out[okhierarchy][t]['test']["description"],
                        "test_group": out[okhierarchy][t]['test']["test_group"]
                        },
                    "results_pct": (results_weighted_pct_average_numerator/results_num),
                    "results_num": results_num
                    }
        if (mode=="publisher_indicators"):
            # get all tests which belong to a specific indicator
            # average the results for all tests in that indicator
            indicators_out = {}
            for indicator, indicatordata in indicators:
                indicators_out[indicator] = {}
                indicator_test_data = []
                results_pct = 0.0
                results_num = 0.0
                results_weighted_pct_average_numerator = 0.0
                for test, testdata in simple_out.items():
                    try:
                        testing = (indicator, test)
                        if (testing in indicators_tests):
                            results_pct+= simple_out[test]["results_pct"]
                            results_num+= simple_out[test]["results_num"]
                            results_weighted_pct_average_numerator += (simple_out[test]["results_pct"]*simple_out[test]["results_num"])
                            oktest = test
                            indicator_test_data.append(simple_out[test])
                    except KeyError:
                        pass
                indicators_out[indicator] = {
                    "indicator": {
                        "id": indicator,
                        "name": indicatordata[0],
                        "description": indicatordata[1]
                    },
                    "tests": indicator_test_data,
                    "results_pct": (results_weighted_pct_average_numerator/results_num),
                    "results_num": results_num
                    }
            return indicators_out        
            #for test, testdata in simple_out.items():
            #    indicators_out[testdata["indicator"]["id"]] = testdata
            #return indicators_out
        else:
            return simple_out

def agr_results(data, conditions=None, mode=None):
    def replace_first(tupl, newval):
        return tuple([newval] + list(tupl)[1:])
    switch_first = lambda t: replace_first(t, t[0].as_dict())
    fixed_data = map(switch_first, data)
    results = _agr_results(fixed_data, conditions, mode)
    return results

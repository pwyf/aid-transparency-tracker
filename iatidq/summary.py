
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import itertools

def reform_dict(d):
    def inner(k1):
        return dict([ (k2, d[(k1, k2)]) for k2 in 
                      map(lambda i: i[1], filter(lambda i: i[0] == k1, d.keys())) ])

    return dict([ (k1, inner(k1))
                   for k1 in set( k1 for k1, k2 in d.keys() ) ])

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


def publisher_indicators(indicators, indicators_tests, simple_out):
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

def publisher_simple(out, cdtns):
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

    return simple_out

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

    def gen_hierarchies():
        for i in set(map(lambda x: (x[4]), data)):
            yield i
    hierarchies = gen_hierarchies()

    def gen_tests():
        for i in set(map(lambda x: (x[1].id), data)):
            yield i
    tests = gen_tests()

    cdtns = None
    if conditions:
        cdtns = dict(map(lambda x: (
                    (x.test_id, x.condition, x.condition_value),
                    (x.operation, x.description)
                    ), conditions))
    
    def publisher_mode(mode):
        if mode in ["publisher", "publisher_simple", "publisher_indicators"]:
            return True
        return False
        
    if publisher_mode(mode):
        indicators = set(map(lambda x: (x[0]["id"], (x[0]["name"], x[0]["description"])), data))
        indicators_tests = list(set(map(lambda x: (x[0]["id"], x[1].id), data)))
        packages = set(map(lambda x: (x[5]), data))
        d = dict(map(lambda x: ((x[4], x[1].id, x[5]),(x)), data))
    else:
        d = dict(map(lambda x: ((x[4], x[1].id),(x)), data))

    out = {}

    def sum_for_publishers(h, t):
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

        if total_activities <= 0:
            return {}
            
        return {
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

    def sum_default(h, t):
        # return data for this single package
        data = d.get((h, t), None)
        if data is None:
            return None

        return {
            "test": {
                "id": data[1].id,
                "description": data[1].description,
                "test_group": data[1].test_group
                },
            "results_pct": data[2],
            "results_num": data[3],
            "result_hierarchy": data[4]
            }

    def summaries(summary_f):
        for h, t in itertools.product(hierarchies, tests):
            yield h, t, summary_f(h, t)

    def add_condition(i):
        h, t, tdata = i
        if conditions:
            key = (t, 'activity hierarchy', str(h))
            if key in cdtns:
                tdata["condition"] = cdtns[key]
        return h, t, tdata

    if publisher_mode(mode):
        summary = sum_for_publishers
    else:
        summary = sum_default

    summaries = (add_condition(i) for i in summaries(summary))

    tmp_out = dict([ ((h, t), tdata) for h, t, tdata in summaries ])
    out = reform_dict(tmp_out)

    if mode not in ["publisher_simple", "publisher_indicators"]:
        return out

    simple_out = publisher_simple(out, cdtns)

    if mode != "publisher_indicators":
        return simple_out

    return publisher_indicators(indicators, indicators_tests, simple_out)

def agr_results(data, conditions=None, mode=None):
    def replace_first(tupl, newval):
        return tuple([newval] + list(tupl)[1:])
    switch_first = lambda t: replace_first(t, t[0].as_dict())
    fixed_data = map(switch_first, data)
    results = _agr_results(fixed_data, conditions, mode)
    return results

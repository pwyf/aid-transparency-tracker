
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import operator
import itertools
import models # damn!
import pprint

class NoRelevantResults(Exception): pass

def reform_dict(d):
    def inner(k1):
        matches_first = lambda i: i[0] == k1
        return dict([ (k2, d[(k1, k2)]) for k2 in 
                      map(lambda i: i[1], filter(matches_first, d.keys())) ])

    return dict([ (k1, inner(k1))
                   for k1 in set( k1 for k1, k2 in d.keys() ) ])

def remove_empty_dicts(h):
    has_keys = lambda kvp: len(kvp[1])
    return dict([ 
            (K, dict(filter(has_keys, V.items()))) 
            for K, V in h.items() 
            ])


class TestInfo(object):
    def __init__(self, test_id, results_pct, results_num):
        test = models.Test.query.filter(models.Test.id == test_id).first()
        self.test_id = test_id
        self.test_name = test.name
        self.test_description = test.description
        self.test_group = test.test_group
        self.test_level = test.test_level
        self.results_pct = results_pct
        self.results_num = results_num

    def as_dict(self):
        return {
            "test": {
                "id": self.test_id,
                "name": self.test_name,
                "description": self.test_description,
                "test_group": self.test_group,
                "test_level": self.test_level
                },
            "results_pct": self.results_pct,
            "results_num": self.results_num
            }


class IndicatorInfo(object):
    def __init__(self, indicator_id):
        self.indicator_id = indicator_id
        self.ind = models.Indicator.query.filter(
            models.Indicator.id == self.indicator_id).first()

    def as_dict(self):
        return self.ind.as_dict()

    def as_dict_minus_group(self):
        tmp = self.ind.as_dict()
        del(tmp['indicatorgroup_id'])
        return tmp


def publisher_indicators(indicators, indicators_tests, simple_out):
    # get all tests which belong to a specific indicator
    # average the results for all tests in that indicator
    def per_indicator(indicator):
        indicator_test_data = []
        results_pct = 0.0
        results_num = 0.0
        results_weighted_pct_average_numerator = 0.0

        relevant = lambda test: (indicator, test) in indicators_tests

        for test in filter(relevant, simple_out.keys()):
            indic_info = simple_out[test]
            results_pct += indic_info["results_pct"]
            results_num += indic_info["results_num"]
            results_weighted_pct_average_numerator += (
                indic_info["results_pct"] * 
                indic_info["results_num"]
                )
            indicator_test_data.append(indic_info)

        return {
            "indicator": IndicatorInfo(indicator).as_dict_minus_group(),
            "tests": indicator_test_data,
            "results_pct": (results_weighted_pct_average_numerator/results_num),
            "results_num": results_num
            }
    
    return dict([ (i, per_indicator(i)) for i in indicators ])

def make_summary(test_id, results_pct, results_num):
    t = TestInfo(test_id, results_pct, results_num)
    return t.as_dict()

def publisher_simple(out, cdtns):
    hierarchies = set(out)
    tests = set()
    for h in hierarchies:
        tests.update(set(out[h]))

    def per_test(t):
        results_pct = 0.0
        results_num = 0.0
        results_weighted_pct_average_numerator = 0.0

        def relevant(hierarchy):
            key = (t,'activity hierarchy', str(hierarchy)) 

            if t not in out[hierarchy]:
                return False

            if not cdtns:
                return True

            if key not in cdtns:
                return True

            if cdtns[key][0] == 0:
                return False

            return True

        # This makes sure information about a test is returned.
        def get_okhierarchy(out, t):
            for h in out:
                if (t in out[h] and 'test' in out[h][t]):
                    return h
            raise NoRelevantResults(
                "Summary could not be generated for test %d" % t
                )

        for hierarchy in filter(relevant, hierarchies):
            test_info = out[hierarchy][t]
            
            results_pct += test_info["results_pct"]
            results_num += test_info["results_num"]
            results_weighted_pct_average_numerator += (
                test_info["results_pct"] * 
                test_info["results_num"]
                )

        if results_num == 0:
            raise NoRelevantResults("Results_num == 0 for test: %d" % t)

        # Result aggregation throws away hierarchies if there are 0 results.
        # This means some hierarchies won't have the 'test' dict. But, at
        # least one must, because we wouldn't be here otherwise.
        okhierarchy = get_okhierarchy(out, t)

        tmp = make_summary(
            out[okhierarchy][t]['test']["id"],
            (results_weighted_pct_average_numerator / results_num),
            results_num
            )
        tmp["indicator"] = out[okhierarchy][t]['indicator']
        return tmp

    return dict([ (t, per_test(t)) for t in tests ])


def sum_for_publishers(packages, d, h, t):
    # aggregate data across multiple packages for a single publisher ;
    # for each package, add percentage for each ;
    # need below to only include packages that are in this hierarchy

    relevant = lambda p: (h, t, p) in d
    relevant_data = map(lambda p: d[(h, t, p)], filter(relevant, packages))

    pct = lambda i: i[2]
    activities = lambda i: i[3]

    total_pct        = reduce(operator.add, map(pct,        relevant_data), 0)
    total_activities = reduce(operator.add, map(activities, relevant_data), 0)

    packages_in_hierarchy = len(relevant_data)

    if total_activities <= 0:
        return {}

    ok_tdata = relevant_data[-1] ## FIXME: this is obviously wrong

    test_id = ok_tdata[1]
         
    tmp = make_summary(
        test_id,
        int(float(total_pct/packages_in_hierarchy)),
        total_activities
        )
    tmp["indicator"] = IndicatorInfo(ok_tdata[0]).as_dict()
    tmp["result_hierarchy"] = total_activities
    return tmp



class Summary(object):
    def __init__(self, data, conditions=None, manual=False):
        self.data = data
        self.conditions = conditions
        self.manual = manual
        self._summary = self.calculate()

    def calculate(self):
        if self.manual:
            return self.aggregate()

        def replace_first(tupl, newval):
            return tuple([newval] + list(tupl)[1:])
        switch_first = lambda t: replace_first(t, t[0])
        self.data = map(switch_first, self.data)

        return self.aggregate()

    def summary(self):
        return self._summary

    def gen_hierarchies(self):
        for i in set(map(lambda x: (x[4]), self.data)):
            yield i

    def gen_tests(self):
        for i in set(map(lambda x: (x[1]), self.data)):
            yield i

    def get_conditions(self):
        if not self.conditions:
            return None

        return dict(map(lambda x: (
                    (x.test_id, x.condition, x.condition_value),
                    (x.operation, x.description)
                    ), self.conditions))

    def restructure_data(self):
        # (h, t, p) -> _
        # h: hierarchy
        # t: test
        # p: ???
        return lambda x: ((x[4], x[1], x[5]), (x))

    def setmap(self, lam):
        return set(map(lam, self.data))

    def get_indicator_data(self):
        ind_f = lambda x: x[0]
        return ind_f


    def aggregate(self):
        hierarchies = self.gen_hierarchies()
        tests = self.gen_tests()
        cdtns = self.get_conditions()
    
        d_f = self.restructure_data()

        d = dict(map(d_f, self.data))

        indicators = self.setmap(self.get_indicator_data())

        ind_test_f = lambda x: (x[0], x[1])
        indicators_tests = list(self.setmap(ind_test_f))

        pkg_f = lambda x: x[5]
        packages = self.setmap(pkg_f)

        summary = lambda h, t: sum_for_publishers(packages, d, h, t)

        return self.summarise_results(hierarchies, 
                                 tests, cdtns, indicators,
                                 indicators_tests, packages, d, summary)

    def summarise_results(self, hierarchies, 
                      tests, cdtns, indicators,
                      indicators_tests, packages, d, summary):

        def summaries(summary_f):
            for h, t in itertools.product(hierarchies, tests):
                yield h, t, summary_f(h, t)

        def add_condition(i):
            h, t, tdata = i
            if self.conditions:
                key = (t, 'activity hierarchy', str(h))
                if key in cdtns:
                    tdata["condition"] = cdtns[key]
            return h, t, tdata

        summaries = (add_condition(i) for i in summaries(summary))

        tmp_out = dict([ ((h, t), tdata) for h, t, tdata in summaries ])
        out = reform_dict(tmp_out)

        out = remove_empty_dicts(out)
        return self.add_indicator_info(out, cdtns, indicators,
                                       indicators_tests)

    def add_indicator_info(self, out, cdtns, indicators,
                           indicators_tests):
        return out


class PublisherSummary(Summary):
    pass


class PublisherIndicatorsSummary(PublisherSummary):
    def add_indicator_info(self, out, cdtns, indicators,
                           indicators_tests):

        simple_out = publisher_simple(out, cdtns)
        return publisher_indicators(indicators, indicators_tests, simple_out)

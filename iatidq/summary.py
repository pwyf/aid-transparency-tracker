
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
import sys
from iatidq import db

COL_INDICATOR = 0
COL_TEST = 1
COL_RESULTS_DATA = 2
COL_RESULTS_NUM = 3
COL_HIERARCHY = 4
COL_PACKAGE = 5

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
    def __init__(self):
        self.tests = dict([ (t.id, t) for t in
                            models.Test.query.all() ])

    def as_dict(self, test_id, results_raw_score, results_num, sampling_ok):
        test = self.tests[test_id]

        sampling_factor = {
            True: 1.0,
            False: 0.0
            }[sampling_ok]

        results_pct = results_raw_score * sampling_factor

        return {
            "test": {
                "id": test_id,
                "name": test.name,
                "description": test.description,
                "test_group": test.test_group,
                "test_level": test.test_level
                },
            "results_pct": results_pct,
            "results_num": results_num,
            "sampling_ok": sampling_ok,
            "results_raw_score": results_raw_score
            }


class IndicatorInfo(object):
    def __init__(self):
        self.inds = dict([ (i.id, i.as_dict()) for i in 
                           models.Indicator.query.all() ])

    def as_dict(self, indicator_id):
        return self.inds[indicator_id]

    def as_dict_minus_group(self, indicator_id):
        tmp = dict(self.inds[indicator_id]) # deep copy or you mutate >1 time
        del(tmp['indicatorgroup_id'])
        return tmp


def publisher_indicators(indicator_info, indicators, indicators_tests,
                         simple_out):
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
            "indicator": indicator_info.as_dict_minus_group(indicator),
            "tests": indicator_test_data,
            "results_pct": (results_weighted_pct_average_numerator/results_num),
            "results_num": results_num
            }
    
    return dict([ (i, per_indicator(i)) for i in indicators ])

def publisher_simple(all_test_info, out, cdtns):
    hierarchies = set(out)
    tests = set()
    for h in hierarchies:
        tests.update(set(out[h]))

    def per_test(t):
        results_pct = 0.0
        results_num = 0.0
        results_weighted_pct_average_numerator = 0.0

        def relevant(hierarchy):
            if t not in out[hierarchy]:
                return False

            return cdtns.is_relevant(t, hierarchy)

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

        tmp = all_test_info.as_dict(
            out[okhierarchy][t]['test']["id"],
            (results_weighted_pct_average_numerator / results_num),
            results_num,
            True
            )
        tmp["indicator"] = out[okhierarchy][t]['indicator']
        return tmp

    return dict([ (t, per_test(t)) for t in tests ])


class Summary(object):
    def __init__(self, data, conditions, manual=False):
        self.data = data
        self.conditions = conditions
        self.manual = manual
        self.indicators = IndicatorInfo()
        self.tests = TestInfo()
        self._summary = self.calculate()

    def calculate(self):
        if self.manual:
            return self.aggregate()

        def replace_first(tupl, newval):
            return tuple([newval] + list(tupl)[COL_TEST:])
        switch_first = lambda t: replace_first(t, t[COL_INDICATOR])
        self.data = map(switch_first, self.data)

        return self.aggregate()

    def summary(self):
        return self._summary

    def gen_hierarchies(self):
        for i in set(map(lambda x: (x[COL_HIERARCHY]), self.data)):
            yield i

    def gen_tests(self):
        for i in set(map(lambda x: (x[COL_TEST]), self.data)):
            yield i

    def restructure_data(self):
        return lambda x: ((x[COL_HIERARCHY], x[COL_TEST], x[COL_PACKAGE]), (x))

    def setmap(self, lam):
        return set(map(lam, self.data))

    def get_indicator_data(self):
        ind_f = lambda x: x[COL_INDICATOR]
        return ind_f

    def aggregate(self):
        hierarchies = self.gen_hierarchies()
        tests = self.gen_tests()
    
        d_f = self.restructure_data()

        d = dict(map(d_f, self.data))

        indicators = self.setmap(self.get_indicator_data())

        ind_test_f = lambda x: (x[COL_INDICATOR], x[COL_TEST])
        indicators_tests = list(self.setmap(ind_test_f))

        pkg_f = lambda x: x[COL_PACKAGE]
        packages = self.setmap(pkg_f)

        summary = lambda h, t: self.sum_for_publishers(packages, d, h, t)

        return self.summarise_results(hierarchies, 
                                 tests, indicators,
                                 indicators_tests, summary)

    def generate_summaries(self, hierarchies, tests, summary_f):
        for h, t in itertools.product(hierarchies, tests):
            yield h, t, summary_f(h, t)

    def summarise_results(self, hierarchies, 
                      tests, indicators,
                      indicators_tests, summary_f):

        def add_condition(i):
            h, t, tdata = i
            if self.conditions.has_condition(t, h):
                tdata["condition"] = self.conditions.get_condition(t, h)
            return h, t, tdata

        summaries = (add_condition(i) for i in self.generate_summaries(
                hierarchies, tests, summary_f))

        even_more_tmp_out = [ ((h, t), tdata) for h, t, tdata in summaries ]
        for i in even_more_tmp_out:
            pass # print >>sys.stderr, i
        tmp_out = dict(even_more_tmp_out)

        out = reform_dict(tmp_out)

        out = remove_empty_dicts(out)
        return self.add_indicator_info(out, indicators,
                                       indicators_tests)

    def add_indicator_info(self, out, indicators,
                           indicators_tests):
        return out

    def sum_for_publishers(self, packages, d, h, t):
        # aggregate data across multiple packages for a single publisher ;
        # for each package, add percentage for each ;
        # need below to only include packages that are in this hierarchy
    
        relevant = lambda p: (h, t, p) in d
        relevant_data = map(lambda p: d[(h, t, p)], filter(relevant, packages))

        ## FIXME
        # this is an appalling hack
        def indicator_for_test(test_id):
            return relevant_data[-1][0]

        pct = lambda i: i[COL_RESULTS_DATA]
        activities = lambda i: i[COL_RESULTS_NUM]

        total_pct        = reduce(operator.add, map(pct,        relevant_data), 0)
        total_activities = reduce(operator.add, map(activities, relevant_data), 0)

        packages_in_hierarchy = len(relevant_data)

        if total_activities <= 0:
            return {}

        indicator_id = indicator_for_test(t)

        tmp = self.tests.as_dict(
            t,
            float(total_pct/packages_in_hierarchy),
            total_activities,
            True
            )
        tmp["indicator"] = self.indicators.as_dict(indicator_id)
        return tmp


class PublisherSummary(Summary):
    pass


class NewPublisherSummary(PublisherSummary):
    def __init__(self, conditions, organisation_id, aggregation_type):
        self.conditions = conditions
        self.indicators = IndicatorInfo()
        self.tests = TestInfo()
        self._summary = self.calculate(organisation_id, aggregation_type)

    def calculate(self, organisation_id, aggregation_type):
        # make list of data; hand over to 
        # summarise_results(hierarchies, tests, indicators, 
        #                   indicators_tests, summary_f):
        conn = db.session.connection()

        sql = '''SELECT DISTINCT result_hierarchy
                   FROM aggregateresult
                   WHERE organisation_id = %d AND 
                         aggregateresulttype_id = %d;'''
        stmt = sql % (organisation_id, aggregation_type)
        hierarchies = [ h[0] for h in conn.execute(stmt) ]

        sql = '''SELECT DISTINCT indicator_id, test_id
                   FROM aggregateresult
                   JOIN indicatortest USING (test_id)
                   WHERE organisation_id = %d AND 
                         aggregateresulttype_id = %d;'''
        stmt = sql % (organisation_id, aggregation_type)
        indicators_tests = [ it for it in conn.execute(stmt) ]
        tests = [ it[1] for it in indicators_tests ]
        indicators = [ it[0] for it in indicators_tests ]

        indicator_lookup = dict([ (it[1], it[0]) for it in indicators_tests ])

        sql = '''SELECT result_hierarchy, test_id, AVG(results_data) AS pct,
                        SUM(results_num) AS total_activities
                   FROM aggregateresult
                   WHERE organisation_id = %d AND 
                         aggregateresulttype_id = %d
                   GROUP BY test_id, result_hierarchy;'''
        stmt = sql % (organisation_id, aggregation_type)
        data = dict([ ((ar[0], ar[1]), ar) for ar in (conn.execute(stmt)) ])
        conn.close()
        del(conn)

        def summary_f(hierarchy, test_id):
            key = (hierarchy, test_id)
            if key not in data:
                return {}

            aresult = data[key]
            sampling_ok = True
            indicator_id = indicator_lookup[test_id]

            tmp = self.tests.as_dict(test_id, aresult[2], aresult[3], 
                                     sampling_ok)
            tmp["indicator"] = self.indicators.as_dict(indicator_id)
            return tmp

        return self.summarise_results(hierarchies, tests, indicators, 
                                      indicators_tests, summary_f)


class PublisherIndicatorsSummary(NewPublisherSummary):
    def add_indicator_info(self, out, indicators,
                           indicators_tests):

        simple_out = publisher_simple(self.tests, out, self.conditions)
        return publisher_indicators(self.indicators, indicators, 
                                    indicators_tests, simple_out)


from models import *


class OrgConditions(object):
    def __init__(self, organisation_id):
        # None is passed as organisation_id for case of no conditions wanted
        if organisation_id is None:
            self._conditions = {}
            return

        cc = OrganisationCondition.query.filter_by(
            organisation_id=organisation_id
            ).all()
        self._conditions = dict(map(lambda x: (
                    (x.test_id, x.condition, x.condition_value),
                    (x.operation, x.description)
                    ), cc))

    def _key(self, test_id, hierarchy):
        return (test_id, 'activity hierarchy', str(hierarchy))

    def is_relevant(self, test_id, hierarchy):
        key = self._key(test_id, hierarchy)

        if not self._conditions:
            return True

        if key not in self._conditions:
            return True

        if self._conditions[key][0] == 0:
            return False

        return True

    def has_condition(self, test_id, hierarchy):
        key = self._key(test_id, hierarchy)
        return key in self._conditions

    def get_condition(self, test_id, hierarchy):
        key = self._key(test_id, hierarchy)
        return self._conditions[key]


class SummaryCreator(object):
    @property
    def summary(self):
        return self._summary

    @property
    def aggregate_results(self):
        return self._aggregate_results


class PublisherSummaryCreator(SummaryCreator):
    def __init__(self, organisation, aggregation_type):
        aggregate_results = db.session.query(
            Indicator.id,
            Test.id,
            AggregateResult.results_data,
            AggregateResult.results_num,
            AggregateResult.result_hierarchy,
            AggregateResult.package_id
            ).filter(
            AggregateResult.organisation_id==organisation.id
            ).filter(
                AggregateResult.aggregateresulttype_id == aggregation_type
            )

        aggregate_results2 = aggregate_results.group_by(
            Indicator.id,
            AggregateResult.result_hierarchy, 
            Test.id, 
            AggregateResult.package_id,
            AggregateResult.results_data,
            AggregateResult.results_num
        ).join(IndicatorTest
        ).join(Test
        ).join(AggregateResult
        ).join(Package
        ).join(OrganisationPackage
        ).join(Organisation
        ).all()

        pconditions = OrgConditions(organisation.id)

        self._aggregate_results = aggregate_results2
        
        self._summary = PublisherSummary(
            self._aggregate_results, conditions=pconditions)



class PackageSummaryCreator(SummaryCreator):
    def __init__(self, package, latest_runtime, aggregation_type):
        p = package

        self._aggregate_results = db.session.query(
            Indicator.id,
            Test.id,
            AggregateResult.results_data,
            AggregateResult.results_num,
            AggregateResult.result_hierarchy,
            AggregateResult.package_id
        ).filter(
            AggregateResult.package_id==p[0].id,
            AggregateResult.aggregateresulttype_id==aggregation_type
        ).group_by(
            AggregateResult.result_hierarchy, 
            Test.id,
            AggregateResult.package_id,
            Indicator.id,
            AggregateResult.results_data,
            AggregateResult.results_num
            ).join(IndicatorTest
            ).join(Test
            ).join(AggregateResult
            ).all()

        self._summary = PublisherSummary(self._aggregate_results, 
                                         OrgConditions(None)).summary()


class PublisherIndicatorsSummaryCreator(SummaryCreator):
    def __init__(self, organisation, aggregation_type):
        organisation_id = organisation.id
        pconditions = OrgConditions(organisation_id)

        self._summary = PublisherIndicatorsSummary(pconditions, 
                                                   organisation_id, 
                                                   aggregation_type)


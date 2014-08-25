
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
    """
    Takes dictionary with keys of the form (hierarchy, test)
    and returns a dict of dicts of the form
      {hierarchy1: {test1: ..., test2: ...}, hierarchy2: ...}
    """

    def inner(hier):
        HIER = 0
        TEST = 1
        matches_first = lambda ht: ht[HIER] == hier
        return dict([ (test, d[(hier, test)]) for test in 
                      map(lambda ht: ht[TEST], filter(matches_first, d.keys())) ])

    return dict([ (hier, inner(hier))
                   for hier in set( hier for hier, test in d.keys() ) ])

def remove_empty_dicts(d):
    has_keys = lambda kvp: len(kvp[1])
    return dict([ 
            (hier, dict(filter(has_keys, test_data.items()))) 
            for hier, test_data in d.items() 
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

        relevant = lambda test: (indicator, test) in indicators_tests
        tests = filter(relevant, simple_out.keys())

        for test in tests:
            indic_info = simple_out[test]
            results_pct += indic_info["results_pct"]
            results_num += indic_info["results_num"]
            indicator_test_data.append(indic_info)

        num_tests = len(tests)

        return {
            "indicator": indicator_info.as_dict_minus_group(indicator),
            "tests": indicator_test_data,
            "results_pct": (results_pct/num_tests),
            "results_num": results_num
            }
    
    return dict([ (i, per_indicator(i)) for i in indicators ])


# The value of this function is immediately consumed by the one above it;
# it's only used in that one place
def publisher_simple(all_test_info, out, cdtns, indicator_lookup, indicators,
                     sampling_data):
    hierarchies = set(out)
    tests = set()

    for h in hierarchies:
        tests.update(set(out[h]))

    def per_test(t):
        results_pct = 0.0 # why does this not get used?
        results_num = 0.0
        results_weighted_pct_average_numerator = 0.0

        def relevant(hierarchy):
            if t not in out[hierarchy]:
                return False

            return cdtns.is_relevant(t, hierarchy)

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

        sampling_ok = sampling_data[t]

        tmp = all_test_info.as_dict(
            t,
            (results_weighted_pct_average_numerator / results_num),
            results_num,
            sampling_ok
            )
        indicator_id = indicator_lookup[t]
        tmp["indicator"] = indicators.as_dict(indicator_id)
        return tmp

    return dict([ (t, per_test(t)) for t in tests ])


class Summary(object):
    def summary(self):
        return self._summary

    def generate_summaries(self, hierarchies, tests, summary_f):
        for h, t in itertools.product(hierarchies, tests):
            yield h, t, summary_f(h, t)

    def summarise_results(self, hierarchies, 
                      tests, indicators,
                      indicators_tests, indicator_lookup, 
                      summary_f):

        def add_condition(i):
            h, t, tdata = i
            if self.conditions.has_condition(t, h):
                tdata["condition"] = self.conditions.get_condition(t, h)
            return h, t, tdata

        summaries = (add_condition(i) for i in self.generate_summaries(
                hierarchies, tests, summary_f))

        tmp_out = dict([ ((h, t), tdata) for h, t, tdata in summaries ])

        out = reform_dict(tmp_out)

        out = remove_empty_dicts(out)
        return self.add_indicator_info(out, indicators,
                                       indicators_tests, indicator_lookup)

    def add_indicator_info(self, out, indicators,
                           indicators_tests, indicator_lookup):
        return out


class PublisherSummary(Summary):
    pass


class NewPublisherSummary(PublisherSummary):
    def __init__(self, conditions, organisation_id, aggregation_type):
        self.conditions = conditions
        self.indicators = IndicatorInfo()
        self.tests = TestInfo()
        self.sampling_data = self.get_sampling_data(organisation_id)

        join_clause = '''
            JOIN organisationpackage USING (package_id, organisation_id)
        '''

        where_clause = '''WHERE aggregateresult.organisation_id = %d AND 
                            aggregateresulttype_id = %d''' % (organisation_id,
                                                              aggregation_type)

        self._summary = self.calculate(join_clause, where_clause)

    def calculate(self, join_clause, where_clause):
        # make list of data; hand over to 
        # summarise_results(hierarchies, tests, indicators, 
        #                   indicators_tests, summary_f):
        conn = db.session.connection()

        sql = '''SELECT DISTINCT result_hierarchy
                   FROM aggregateresult
                   %s %s;'''
        stmt = sql % (join_clause, where_clause)
        hierarchies = [ h[0] for h in conn.execute(stmt) ]

        sql = '''SELECT DISTINCT indicator_id, test_id
                   FROM aggregateresult
                   JOIN indicatortest USING (test_id)
                   %s %s;'''
        stmt = sql % (join_clause, where_clause)
        indicators_tests = [ it for it in conn.execute(stmt) ]
        tests = [ it[1] for it in indicators_tests ]
        indicators = [ it[0] for it in indicators_tests ]

        indicator_lookup = dict([ (it[1], it[0]) for it in indicators_tests ])

        # The WITH-clause sets up "org_aresult" as though it were a table
        # resembling the results of the query in the clause; it contains
        # only the aggregate results relevant to the organisation and
        # aggregationtype under consideration

        # the joined SELECT subquery (named t1) gets us the right totals

        # the sum(results_data * results_num / total) calculation is
        # arithmetically equivalent to doing an average, since everything
        # is divided by the total

        sql = '''
            WITH org_aresult AS (
              SELECT result_hierarchy, test_id, results_data, results_num
              FROM aggregateresult
              %s %s
            )
            SELECT result_hierarchy,
                   test_id,
                   SUM(results_data * results_num::float / t1.total) AS pct,
                   SUM(results_num) AS total_activities
            FROM org_aresult
            JOIN (
              SELECT result_hierarchy, test_id, SUM(results_num) AS total
              FROM org_aresult
              GROUP BY result_hierarchy, test_id) AS t1
            USING (result_hierarchy, test_id)
            GROUP BY result_hierarchy, test_id;
        '''
        
        stmt = sql % (join_clause, where_clause)
        data = dict([ ((ar[0], ar[1]), ar) for ar in (conn.execute(stmt)) ])
        conn.close()
        del(conn)

        def summary_f(hierarchy, test_id):
            key = (hierarchy, test_id)
            if key not in data:
                return {}

            aresult = data[key]
            sampling_ok = self.sampling_data[test_id]
            indicator_id = indicator_lookup[test_id]

            tmp = self.tests.as_dict(test_id, aresult[2], aresult[3], 
                                     sampling_ok)
            tmp["indicator"] = self.indicators.as_dict(indicator_id)
            return tmp

        return self.summarise_results(hierarchies, tests, indicators, 
                                      indicators_tests, indicator_lookup,
                                      summary_f)

    def get_sampling_data(self, organisation_id):
        sql = '''SELECT test_id FROM sampling_failure
                   WHERE organisation_id = %s;'''
        failed_test_ids = [ row[0] for row in 
                            db.engine.execute(sql, (organisation_id,)) ]

        def ok(t):
            return t not in failed_test_ids

        return dict([ (t, ok(t)) for t in self.tests.tests.keys() ])


class NewPackageSummary(NewPublisherSummary):
    def __init__(self, conditions, package_id, aggregation_type):
        self.conditions = conditions
        self.indicators = IndicatorInfo()
        self.tests = TestInfo()
        self.sampling_data = self.get_sampling_data(None)

        join_clause = ""
        
        where_clause = '''WHERE package_id = %d AND 
                            aggregateresulttype_id = %d''' % (package_id,
                                                              aggregation_type)

        self._summary = self.calculate(join_clause, where_clause)

        

class PublisherIndicatorsSummary(NewPublisherSummary):
    def add_indicator_info(self, out, indicators,
                           indicators_tests, indicator_lookup):

        simple_out = publisher_simple(self.tests, out, self.conditions,
                                      indicator_lookup, self.indicators,
                                      self.sampling_data)
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
        organisation_id = organisation.id
        pconditions = OrgConditions(organisation_id)

        self._summary = NewPublisherSummary(pconditions, 
                                            organisation_id, 
                                            aggregation_type)


class PackageSummaryCreator(SummaryCreator):
    def __init__(self, package_id, latest_runtime, aggregation_type):
        

        self._summary = NewPackageSummary(OrgConditions(None),
                                          package_id, 
                                          aggregation_type).summary()


class PublisherIndicatorsSummaryCreator(SummaryCreator):
    def __init__(self, organisation, aggregation_type):
        organisation_id = organisation.id
        pconditions = OrgConditions(organisation_id)

        self._summary = PublisherIndicatorsSummary(pconditions, 
                                                   organisation_id, 
                                                   aggregation_type)

# The model for the big SQL query at the core of the class:

# select domain, sum(results_data * results_num::float/t1.total) 
# from example_summary join
#      (select domain, sum(results_num) as total 
#         from example_summary 
#         group by domain) as t1 
# using (domain) 
# group by example_summary.domain;

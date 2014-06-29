
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import itertools

RESULT_FAILURE = 0
RESULT_SUCCESS = 1

FIELD_TEST = 0
FIELD_STATUS = 1
FIELD_HIERARCHY = 2
FIELD_RESULT = 3
FIELD_PACKAGE = 4
FIELD_ORGANISATION = 5

def prepend(prefix, tup):
    return tuple([prefix] + list(tup))

def _aggregate_percentages(data, dims):
    """
    'dims' contains a list of tuples of field names and the lambdas
    used for extracting those fields from 'data'. These fields are
    treated as dimensions in an n-dimensional hypercube

    We generate list of the unique values in each considered dimension

    We project the hypercube onto the selected dimensions by calculating
    the cartesian product of these unique values, then mapping the
    calc_percentage function across it
    """

    def setmap(lam):
        return set(map(lam, data))

    def generate_dimension(dimension_name):
        return setmap(dims_dict[dimension_name])

    def lookups(x):
        return tuple([ dims_dict[i](x) for i in dim_names ])

    dims_dict = dict(dims)
    dim_names = [ i[0] for i in dims ]
    dimension_lists = map(generate_dimension, dim_names)
    breakdown = lambda x: (
        prepend(x[FIELD_STATUS], lookups(x)),
        x[FIELD_RESULT]
        )

    d = dict(map(breakdown, data))

    def calc_percentages(dimensions):
        fail    = d.get(prepend(RESULT_FAILURE, dimensions), 0)
        success = d.get(prepend(RESULT_SUCCESS, dimensions), 0)

        if 0 == fail + success:
            return None
        percentage = float(success) / (fail + success) * 100.0

        data = {
            "percentage_passed": percentage,
            "total_results": fail+success,
            }
        for i, dim in enumerate(dim_names):
            data[dim] = dimensions[i]
        return data

    out = map(calc_percentages, itertools.product(*dimension_lists))
    out = filter(lambda i: i is not None, out)

    return out

def aggregate_percentages(data):
    # Aggregates results data for a specific runtime.

    dims = [
        ("package_id", lambda x: x[FIELD_PACKAGE]),
        ("test_id",    lambda x: x[FIELD_TEST]),
        ("hierarchy",  lambda x: x[FIELD_HIERARCHY])
        ]

    return _aggregate_percentages(data, dims)

def aggregate_percentages_org(data):
    # Aggregates results data for a specific runtime.

    dims = [
        ("package_id", lambda x: x[FIELD_PACKAGE]),
        ("test_id",    lambda x: x[FIELD_TEST]),
        ("hierarchy",  lambda x: x[FIELD_HIERARCHY]),
        ("organisation_id", lambda x: x[FIELD_ORGANISATION])
        ]

    return _aggregate_percentages(data, dims)

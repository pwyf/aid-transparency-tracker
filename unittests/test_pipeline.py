#!/usr/bin/python

#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2014  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import os
import sys

import nose
import pytest

import iatidq
from iatidq import models, test_level
from iatidataquality import app, db

app.config.from_pyfile(os.path.join("..", "config_test.py"))

def log(s):
    return
    print(s, file=sys.stderr)

def setup_func():
    db.drop_all()
    db.create_all()

def __setup_organisations(pkg_id):
    org_data = [
        ('UK, DFID', 'GB-1',
         '''participating-org[@role="Extending"][@ref="GB-1"]'''),
        ('World Bank', '44002',
         '''participating-org[@role="Extending"][@ref="44002"]'''),
        ]
    for name, code, cond in org_data:
        organisation = iatidq.dqorganisations.addOrganisation(
            {'organisation_name': name,
             'organisation_code': code})
        iatidq.dqorganisations.addOrganisationPackage(
            {'organisation_id': organisation.id,
             'package_id': pkg_id,
             'condition': cond})

def teardown_func():
    pass

def get_packagegroups_by_name(name):
    return models.PackageGroup.query.filter(
        models.PackageGroup.name==name).all()

def get_packages_by_name(name):
    return models.Package.query.filter(
        models.Package.package_name==name).all()

@pytest.mark.xfail
@nose.with_setup(setup_func, teardown_func)
def test_refresh():
    publisher = 'dfid'
    country = 'tz'
    package_name = '-'.join([publisher, country])

    # check there's nothing in the db
    pgs = get_packagegroups_by_name(publisher)
    assert len(pgs) == 0
    pkgs = get_packages_by_name(package_name)
    assert len(pkgs) == 0

    # do refresh
    iatidq.dqregistry.refresh_package_by_name(package_name)

    # check there's something in the db
    pgs = get_packagegroups_by_name(publisher)
    assert len(pgs) == 1
    pg = pgs[0]
    assert pg.name == publisher

    pkgs = get_packages_by_name(package_name)
    assert len(pkgs) == 1
    pkg = pkgs[0]
    assert pkg.package_name == package_name

def create_aggregation_types(options):
    print("Adding an aggregation type for all data")
    all_ag = iatidq.dqaggregationtypes.addAggregationType({'name':'All data',
                                                'description': '',
                                                'test_id': None,
                                                'test_result':'1'})
    assert all_ag
    print("Adding an aggregation type for current data")
    currentdata_test = iatidq.dqtests.test_by_test_name(
        "activity-date[@type='start-planned']/@iso-date or transaction-date/@iso-date (for each transaction) is less than 13 months ago?"
        )
    iatidq.dqaggregationtypes.addAggregationType({'name':'Current data',
                                                'description': '',
                                                'test_id':currentdata_test.id,
                                                'test_result':'1'})
    return all_ag

def _test_example_tests(publisher, country):
    package_name = '-'.join([publisher, country])
    xml_filename = os.path.join("unittests", "artefacts", "xml", package_name + '.xml')

    # check there's nothing in the db
    #pgs = get_packagegroups_by_name(publisher)
    #assert len(pgs) == 0
    #pkgs = get_packages_by_name(package_name)
    #assert len(pkgs) == 0

    # do refresh
    #iatidq.dqregistry.refresh_package_by_name(package_name)
    iatidq.setup.setup_packages_minimal()

    iatidq.dqimporttests.hardcodedTests()

    # load foxpath tests
    os.chdir(parent)
    iatidq.dqimporttests.importTestsFromFile(
        "tests/sample_tests.csv",
        test_level.ACTIVITY)

    print("Importing indicators")
    iatidq.dqindicators.importIndicatorsFromFile(
        "test_pwyf2013",
        "tests/sample_tests.csv")

    iatidq.dqindicators.importIndicatorDescriptionsFromFile("2018index",
                                                            "tests/indicators.csv")
    log("Importing codelists")
    #iatidq.dqcodelists.importCodelists()
    #log("Refreshing package data from Registry")
    #iatidq.dqregistry.refresh_packages()


    log("about to start testing")

    test_functions = iatidq.dqparsetests.test_functions()
    codelists = iatidq.dqcodelists.generateCodelists()

    # FIXME: THIS IS A TOTAL HACK
    with db.session.begin():
        models.Result.query.delete()
        models.AggregateResult.query.delete()
        models.AggregationType.query.delete()

    all_ag = create_aggregation_types({})


    runtime = iatidq.testrun.start_new_testrun()

    results = models.Result.query.all()
    assert len(results) == 0

    pkg = get_packages_by_name(package_name)[0]

    log(pkg.package_name)

    package_id = pkg.id
    ## this is a hack on a stick
    #if publisher == 'unitedstates':
    #    setup_organisations(package_id)
    iatidq.setup.setup_organisations_minimal()

    assert iatidq.test_queue.check_file(test_functions,
               codelists,
               xml_filename,
               runtime.id,
               pkg.id)

    results = models.Result.query.all()
    assert len(results) > 0
    print(len(results), file=sys.stderr)

    aggtest_results = models.AggregateResult.query.filter(
        models.AggregateResult.aggregateresulttype_id == all_ag.id
        ).all()
    for result in aggtest_results:
        assert result.runtime_id == runtime.id
        assert result.package_id == pkg.id

    resultful_tests = [
        'valid_xml',
        'description/text() exists?',
        'description/text() has more than 40 characters?',
        'description/@type exists?',
        'title/text() exists?',
        'title/text() has more than 10 characters?',
        """activity-date[@type='start-planned']/@iso-date or transaction-date/@iso-date (for each transaction) is less than 13 months ago?"""
        ]

    expected_test_ids = [ i.id for i in models.Test.query.filter(
        models.Test.name.in_(resultful_tests)).all() ]

    observed_test_ids = [ i.test_id for i in aggtest_results ]

    print("expected test ids: ", expected_test_ids)
    print("observed test ids: ", observed_test_ids)
    assert set(expected_test_ids) == set(observed_test_ids)




@nose.with_setup(setup_func, teardown_func)
@pytest.mark.parametrize("publisher, country", [
    ('worldbank', '789'),
    ('dfid', 'ph')
])
def _test_samples(publisher, country):
    _test_example_tests(publisher, country)

if __name__ == '__main__':
    setup_func()
    test_example_tests()


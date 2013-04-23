#!/usr/bin/python

import os
import sys
import csv

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import iatidq
import iatidq.dqparsetests
import iatidq.dqregistry
import iatidq.dqimporttests
import iatidq.dqindicators
import iatidq.test_queue
import iatidq.dqcodelists

from iatidq import db
import lxml.etree

import nose
import nose.tools
import sys

from iatidq.models import *

def log(s):
    return
    print >>sys.stderr, s

def setup_func():
    print >>sys.stderr, "setting up"
    iatidq.db.drop_all()
    iatidq.db.create_all()
    print  >>sys.stderr, "about to commit in setup"
    db.session.commit()
    print  >>sys.stderr, "committed"

def teardown_func():
    db.session.commit()
    pass

def get_packagegroups_by_name(name):
    return iatidq.models.PackageGroup.query.filter(
        PackageGroup.name==name).all()

def get_packages_by_name(name):
    return iatidq.models.Package.query.filter(
        Package.package_name==name).all()

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

def _test_example_tests():
    publisher = 'worldbank'
    country = 'tz'
    package_name = '-'.join([publisher, country])

    # check there's nothing in the db
    pgs = get_packagegroups_by_name(publisher)
    assert len(pgs) == 0
    pkgs = get_packages_by_name(package_name)
    assert len(pkgs) == 0

    # do refresh
    iatidq.dqregistry.refresh_package_by_name(package_name)

    iatidq.dqimporttests.hardcodedTests()

    # load foxpath tests
    os.chdir(parent)
    iatidq.dqimporttests.importTestsFromFile(
        filename="tests/sample_tests.csv")

    print "Importing indicators"
    iatidq.dqindicators.importIndicatorsFromFile(
        "test_pwyf2013",
        "tests/sample_tests.csv")

    iatidq.dqindicators.importIndicatorDescriptionsFromFile("pwyf2013", 
                                                            "tests/indicators.csv")
    log("Importing codelists")
    #iatidq.dqcodelists.importCodelists()
    #log("Refreshing package data from Registry")
    #iatidq.dqregistry.refresh_packages()


    log("about to start testing")
 
    from iatidq.dqparsetests import test_functions as tf
    test_functions = tf()
    from iatidq import dqcodelists
    codelists = dqcodelists.generateCodelists()

    from iatidq.testrun import start_new_testrun
    runtime = start_new_testrun()

    results = iatidq.models.Result.query.all()
    assert len(results) == 0

    pkg = get_packages_by_name('worldbank-tz')[0]

    log(pkg.package_name)

    assert iatidq.test_queue.check_file(test_functions, 
               codelists,
               "unittests/artefacts/worldbank-tz.xml",
               runtime.id,
               pkg.id,
               context=None)

    results = iatidq.models.Result.query.all()
    assert len(results) > 0
    print >>sys.stderr, len(results)

    aggtest_results = iatidq.models.AggregateResult.query.all()
    for result in aggtest_results:
        assert result.runtime_id == runtime.id
        assert result.package_id == pkg.id
    
    resultful_tests = [
        'valid_xml',
        'description/text() exists?',
        'description/text() has more than 40 characters?',
        'description/@type exists?',
        'title/text() exists?',
        'title/text() has more than 10 characters?'
        ]

    expected_test_ids = [ i.id for i in iatidq.models.Test.query.filter(
        Test.name.in_(resultful_tests)).all() ]
    
    observed_test_ids = [ i.test_id for i in aggtest_results ]

    print expected_test_ids
    print observed_test_ids
    assert set(expected_test_ids) == set(observed_test_ids)

@nose.with_setup(setup_func, teardown_func)
def test_example_tests():
    return _test_example_tests()

if __name__ == '__main__':
    setup_func()
    test_example_tests()

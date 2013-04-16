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

from iatidq.models import *

def setup_func():
    iatidq.db.drop_all()
    iatidq.db.create_all()
    db.session.commit()

def teardown_func():
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

@nose.with_setup(setup_func, teardown_func)
def test_example_tests():
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
        filename="tests/iati2foxpath_tests.csv")
    print "Importing indicators"
    iatidq.dqindicators.importIndicatorsFromFile(
        "test_pwyf2013",
        "tests/iati2foxpath_tests.csv")

    iatidq.dqindicators.importIndicatorDescriptionsFromFile("pwyf2013", 
                                                            "tests/indicators.csv")
    print "Importing codelists"
    iatidq.dqcodelists.importCodelists()
    print "Refreshing package data from Registry"
    dqregistry.refresh_packages()



 
    from iatidq.dqparsetests import test_functions as tf
    test_functions = tf()
    from iatidq import dqcodelists
    codelists = dqcodelists.generateCodelists()

#    for t in iatidq.models.Test.query.all():
#        print t

    from iatidq.testrun import start_new_testrun
    runtime = start_new_testrun()

    results = iatidq.models.Result.query.all()
    assert len(results) == 0

    pkg = get_packages_by_name('worldbank-tz')[0]

    iatidq.test_queue.check_file(test_functions, 
               codelists,
               "pkgdata-worldbank-tz.json",
               runtime.id,
               pkg.id,
               context=None)

    assert len(results) > 0

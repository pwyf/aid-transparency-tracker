#!/usr/bin/env python

#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

""" This script is to quickly get started with this tool, by:
        1) creating DB
        2) populating the list of packages from the Registry (will download basic data about all packages)
        3) setting 3 to "active"
"""
#import warnings
#warnings.filterwarnings('error')

import iatidq

from iatidq import models, dqregistry 
import iatidq.dqfunctions
import iatidq.dqimporttests
import iatidq.dqdownload
import iatidq.dqcodelists
import iatidq.dqruntests
import iatidq.dqindicators
import iatidq.dqpublishers

import optparse
import sys

which_packages = [
    (u'worldbank-tz', True),
    (u'unops-tz', True),
    (u'dfid-tz', True)
    ]

def run(refresh=False, minimal=False):
    if refresh:
        if minimal:
            for package_name, _ in which_packages:
                dqregistry.refresh_package_by_name(package_name)
        else:
            dqregistry.refresh_packages()
    dqregistry.activate_packages(which_packages, clear_revision_id=True)

def main():
    p = optparse.OptionParser()
    p.add_option("--refresh", dest="refresh", action="store_true",
                 help="Refresh")
    p.add_option("--clear-revisionid", dest="clear_revisionid", 
                 action="store_true",
                 help="Clear CKAN revision ids")
    p.add_option("--init-db", dest="init_db",
                  action="store_true",
                  help="Initialise DB")
    p.add_option("--drop-db", dest="drop_all",
                  action="store_true",
                  help="Delete DB")
    p.add_option("--enroll-tests", dest="enroll_tests",
                 help="Enroll a CSV file of tests")
    p.add_option("--level", dest="level",
                 type="int",
                 default=1,
                 help="Test level (e.g., 1 == Activity)")
    p.add_option("--minimal-pkgs", dest="minimal_pkgs",
                 action="store_true",
                 default=False,
                 help="Operate on a minimal set of packages")
    p.add_option("--download", dest="download",
                 action="store_true",
                 default=False,
                 help="Download packages")
    p.add_option("--import_codelists", dest="import_codelists",
                 action="store_true",
                 default=False,
                 help="Import codelists")
    p.add_option("--enqueue-test", dest="enqueue_test",
                 action="store_true",
                 default=False,
                 help="Set a package to be tested (with --package)")
    p.add_option("--package", dest="package_name",
                 help="Set name of package to be tested")
    p.add_option("--filename", dest="filename",
                 help="Set filename of data to test")
    p.add_option("--local_folder", dest="local_folder",
                 help="Set local folder where data to test is stored")
    p.add_option("--import_indicators", dest="import_indicators",
                 action="store_true",
                 default=False,
                 help="Import indicators. Will try to assign indicators to existing tests.")
    p.add_option("--import_publishers", dest="import_publishers",
                 action="store_true",
                 default=False,
                 help="Import publishers. Will try to create and assign publishers to existing packages.")
    p.add_option("--setup", dest="setup",
                 action="store_true",
                 default=False,
                 help="""Quick setup. Will init db, add tests, add codelists, 
                      add indicators, refresh package data from Registry.""")

    options, args = p.parse_args()

    if options.drop_all:
        iatidq.db.drop_all()
        return

    if options.init_db:
        iatidq.db.create_all()
        iatidq.dqimporttests.hardcodedTests()
        return

    if options.enroll_tests:
        filename = options.enroll_tests.decode()
        result = iatidq.dqimporttests.importTests(
            filename=filename, 
            level=options.level)
        if not result:
            print "Error importing"
        return

    if options.clear_revisionid:
        iatidq.dqfunctions.clear_revisions()
        return

    if options.import_codelists:
        iatidq.dqcodelists.importCodelists()
        return

    if options.download:
        if options.minimal_pkgs:
            for package_name, _ in which_packages:
                iatidq.dqdownload.run(package_name=package_name)
        else:
            iatidq.dqdownload.run()
        return

    if options.import_indicators:
        if options.filename:
            iatidq.dqindicators.importIndicatorsFromFile("pwyf2013",
                                                         options.filename)
        else:
            iatidq.dqindicators.importIndicators()
        return

    if options.import_publishers:
        if options.filename:
            iatidq.dqpublishers.importPublisherPackagesFromFile(options.filename)
        else:
            print "Error: please provide a filename"
        return

    if options.setup:
        print "Creating DB"
        iatidq.db.create_all()
        print "Adding hardcoded tests"
        iatidq.dqimporttests.hardcodedTests()
        print "Importing tests"
        iatidq.dqimporttests.importTestsFromFile(
            filename="tests/iati2foxpath_tests.csv")
        print "Importing indicators"
        iatidq.dqindicators.importIndicatorsFromFile(
            "pwyf2013",
            "tests/iati2foxpath_tests.csv")
        print "Importing indicator descriptions"
        iatidq.dqindicators.importIndicatorDescriptionsFromFile("pwyf2013", 
                                                                "tests/indicators.csv")
        print "Importing codelists"
        iatidq.dqcodelists.importCodelists()
        print "Refreshing package data from Registry"
        dqregistry.refresh_packages()
        return

    if options.enqueue_test:
        assert options.package_name
        assert options.filename

        iatidq.dqruntests.enqueue_package_for_test(options.filename,
                                                   options.package_name)
        return

    run(refresh=options.refresh, minimal=options.minimal_pkgs)

if __name__ == '__main__':
    main()

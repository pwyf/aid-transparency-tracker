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
        3) setting packages to "active"
"""

import argparse
import sys

import iatidq

import iatidq.dqfunctions
import iatidq.dqimporttests
import iatidq.dqdownload
import iatidq.dqcodelists
import iatidq.dqruntests
import iatidq.dqindicators
import iatidq.dqorganisations
import iatidq.dqaggregationtypes
import iatidq.dqtests
import iatidq.dqprocessing
import iatidq.inforesult
import iatidq.setup
import iatidq.dqregistry as dqregistry
from iatidq.minimal import which_packages


def refresh(options):
    pkg_names = None
    if options.package_name:
        pkg_names = [options.package_name]
    elif options.minimal:
        pkg_names = [i[0] for i in which_packages]
    elif options.matching:
        pkg_names = [i for i in dqregistry.matching_packages(options.matching)]

    if pkg_names is not None:
        [ dqregistry.refresh_package_by_name(name) for name in pkg_names ]
    else:
        dqregistry.refresh_packages()

def activate_packages(options):
    if options.matching:
        which_packages = [(i, True) 
                          for i in dqregistry.matching_packages(
                options.matching)]
    dqregistry.activate_packages(which_packages, clear_revision_id=True)

def drop_db(options):
    iatidq.db.drop_all()

def init_db(options):
    iatidq.db.create_all()
    iatidq.dqimporttests.hardcodedTests()

def enroll_tests(options):
    assert options.filename
    filename = options.filename.decode()
    result = iatidq.dqimporttests.importTestsFromFile(
        filename=filename, 
        level=options.level)
    if not result:
        print "Error importing"

def clear_revisionid(options):
    iatidq.dqfunctions.clear_revisions()

def import_codelists(options):
    iatidq.dqcodelists.importCodelists()

def import_basic_countries(options):
    filename = 'tests/countries_basic.csv'
    codelist_name='countriesbasic'
    codelist_description='Basic list of countries for running tests against'
    iatidq.dqcodelists.add_manual_codelist(filename, codelist_name, codelist_description)

def download(options):
    if options.minimal:
        for package_name, _ in which_packages:
            iatidq.dqdownload.run(package_name=package_name)
    elif options.matching:
        for pkg_name in dqregistry.matching_packages(options.matching):
            iatidq.dqdownload.run(package_name=pkg_name)
    else:
        iatidq.dqdownload.run()

def import_indicators(options):
    if options.filename:
        iatidq.dqindicators.importIndicatorsFromFile("pwyf2013",
                                                     options.filename)
    else:
        iatidq.dqindicators.importIndicators()

def import_organisations(options):
    if options.filename:
        iatidq.dqorganisations.importOrganisationPackagesFromFile(options.filename)
    else:
        print "Error: please provide a filename"

def create_aggregation_types(options):
    iatidq.setup.create_aggregation_types()

def create_inforesult_types(options):
    iatidq.setup.create_inforesult_types()

def updatefrequency(options):
    iatidq.dqorganisations.downloadOrganisationFrequency()

def enqueue_test(options):
    assert options.package_name
    assert options.filename
    iatidq.dqruntests.enqueue_package_for_test(options.filename,
                                               options.package_name)

def aggregate_results(options):
    assert options.runtime_id
    assert options.package_id
    iatidq.dqprocessing.aggregate_results(options.runtime_id, 
                                          options.package_id)

def setup_organisations(options):
    iatidq.setup.setup_organisations()

def setup_users(options):
    assert options.filename
    iatidq.dqusers.importUserDataFromFile(options.filename)

def setup(options):
    iatidq.setup.setup(options)

commands = [
    ("drop-db", drop_db, "Delete DB"),
    ("init-db", init_db, "Initialise DB"),
    ("enroll-tests", enroll_tests, "Enroll a CSV file of tests"),
    ("clear-revisionid", clear_revisionid, "Clear CKAN revision ids"),
    ("import-codelists", import_codelists, "Import codelists"),
    ("import-basic-countries", import_basic_countries, "Import basic list of countries"),
    ("download", download, "Download packages"),
    ("updatefrequency", updatefrequency, "Update frequency"),
    ("import-indicators", import_indicators, "Import indicators. Will try to assign indicators to existing tests."),
    ("import-organisations", import_organisations, "Import organisations. Will try to create and assign organisations to existing packages."),
    ("setup", setup, "Quick setup. Will init db, add tests, add codelists, add indicators, refresh package data from Registry."),
    ("enqueue-test", enqueue_test, "Set a package to be tested (with --package"),
    ("refresh", refresh, "Refresh"),
    ("activate-packages", activate_packages, "Mark all packages as active"),
    ("create-aggregation-types", create_aggregation_types, "Create basic aggregation types."),
    ("aggregate-results", aggregate_results, "Trigger result aggregation"),
    ("create-inforesult-types", create_inforesult_types, "Create basic infroresult types."),
    ("setup-organisations", setup_organisations, "Setup organisations."),
    ("setup-users", setup_users, "Setup users and permissions."),
]

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    for arg, handler, help_text in commands:
        subparser = subparsers.add_parser(arg, help=help_text)
        subparser.set_defaults(handler=handler)
        _ = subparser.add_argument("--runtime-id", dest="runtime_id",
                     type=int,
                     help="Runtime id (integer)")
        _ = subparser.add_argument("--package-id", dest="package_id",
                     type=int,
                     help="Package id (integer)")
        _ = subparser.add_argument("--level", dest="level",
                     type=int,
                     default=1,
                     help="Test level (e.g., 1 == Activity)")
        _ = subparser.add_argument("--minimal", dest="minimal",
                     action="store_true",
                     default=False,
                     help="Operate on a minimal set of packages")
        _ = subparser.add_argument("--package", dest="package_name",
                     help="Set name of package to be tested")
        _ = subparser.add_argument("--filename", dest="filename",
                     help="Set filename of data to test")
        _ = subparser.add_argument("--local-folder", dest="local_folder",
                     help="Set local folder where data to test is stored")
        _ = subparser.add_argument("--matching", dest="matching",
                     help="Regular expression for matching packages")
    
    args = parser.parse_args()
    args.handler(args)

if __name__ == '__main__':
    main()

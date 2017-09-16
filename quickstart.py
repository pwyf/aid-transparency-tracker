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

from iatidataquality import db
from iatidq import dqcodelists, dqdownload, dqfunctions, dqimporttests, dqindicators, dqminimal, dqorganisations, dqprocessing, dqregistry, dqruntests, dqusers
from iatidq import setup as dqsetup


def refresh(options):
    pkg_names = None
    if options.package_name:
        pkg_names = [options.package_name]
    elif options.minimal:
        pkg_names = [i[0] for i in dqminimal.which_packages]
    elif options.matching:
        pkg_names = [i for i in dqregistry.matching_packages(options.matching)]

    if pkg_names is not None:
        [ dqregistry.refresh_package_by_name(name) for name in pkg_names ]
    else:
        dqregistry.refresh_packages()

def activate_packages(options):
    assert options.matching
    matching_packages = [(i, True)
                      for i in dqregistry.matching_packages(
            options.matching)]
    dqregistry.activate_packages(matching_packages, clear_revision_id=True)

def drop_db(options):
    print('\nWarning! This will drop all database tables!')
    confirmed = raw_input('Are you really really sure? (y/N) ')
    if confirmed.lower() == 'y':
        db.drop_all()
        print('DB dropped.')

def init_db(options):
    db.create_all()
    dqimporttests.hardcodedTests()

def enroll_tests(options):
    assert options.filename
    filename = options.filename.decode()
    result = dqimporttests.importTestsFromFile(
        filename=filename, 
        level=options.level)
    if not result:
        print "Error importing"

def clear_revisionid(options):
    dqfunctions.clear_revisions()

def import_codelists(options):
    dqcodelists.importCodelists()

def import_basic_countries(options):
    filename = 'tests/countries_basic.csv'
    codelist_name = 'countriesbasic'
    codelist_description = 'Basic list of countries for running tests against'
    dqcodelists.add_manual_codelist(filename, codelist_name, codelist_description)

def download(options):
    if options.minimal:
        for package_name, _ in dqminimal.which_packages:
            dqdownload.run(package_name=package_name)
    elif options.matching:
        for pkg_name in dqregistry.matching_packages(options.matching):
            dqdownload.run(package_name=pkg_name)
    else:
        dqdownload.run()

def import_indicators(options):
    if options.filename:
        dqindicators.importIndicatorsFromFile("pwyf2013",
                                                     options.filename)
    else:
        dqindicators.importIndicators()

def import_organisations(options):
    if options.filename:
        dqorganisations.importOrganisationPackagesFromFile(options.filename)
    else:
        print "Error: please provide a filename"

def create_aggregation_types(options):
    dqsetup.create_aggregation_types()

def create_inforesult_types(options):
    dqsetup.create_inforesult_types()

def updatefrequency(options):
    dqorganisations.downloadOrganisationFrequency()

def enqueue_test(options):
    assert options.package_name
    assert options.filename
    dqruntests.enqueue_package_for_test(options.filename,
                                               options.package_name)

def aggregate_results(options):
    assert options.runtime_id
    assert options.package_id
    dqprocessing.aggregate_results(options.runtime_id, 
                                          options.package_id)

def setup_organisations(options):
    dqsetup.setup_organisations()

def setup_users(options):
    assert options.filename
    dqusers.importUserDataFromFile(options.filename)

def create_admin(options):
    dqsetup.setup_admin_user(options.username, options.password)

def setup(options):
    dqsetup.setup(options)

def create_subparser(subparsers, handler, command, help_text):
    subparser = subparsers.add_parser(command, help=help_text)
    subparser.set_defaults(handler=handler)
    return subparser

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    create_subparser(subparsers, drop_db, 'drop-db', help_text='Delete DB')

    create_subparser(subparsers, init_db, 'init-db', help_text='Initialise DB')

    subparser = create_subparser(subparsers, enroll_tests, 'enroll-tests', help_text='Enroll a CSV file of tests')
    subparser.add_argument('--filename', help='Set filename of data to test', required=True)
    subparser.add_argument('--level', type=int, default=1, help='Test level (e.g. 1 == Activity)')

    create_subparser(subparsers, clear_revisionid, 'clear-revisionid', help_text='Clear CKAN revision ids')

    create_subparser(subparsers, import_codelists, 'import-codelists', help_text='Import codelists')

    create_subparser(subparsers, import_basic_countries, 'import-basic-countries', help_text='Import basic list of countries')

    subparser = create_subparser(subparsers, download, 'download', help_text='Download packages')
    subparser.add_argument('--minimal', dest='minimal', action='store_true', default=False, help='Operate on a minimal set of packages')
    subparser.add_argument('--matching', dest='matching', help='Regular expression for matching packages')

    create_subparser(subparsers, updatefrequency, 'updatefrequency', help_text='Update frequency')

    subparser = create_subparser(subparsers, import_indicators, 'import-indicators', help_text='Import indicators. Will try to assign indicators to existing tests.')
    subparser.add_argument('--filename', dest='filename', help='Set filename of data to test')

    subparser = create_subparser(subparsers, import_organisations, 'import-organisations', help_text='Import organisations. Will try to create and assign organisations to existing packages.')
    subparser.add_argument('--filename', dest='filename', help='Set filename of data to test')

    subparser = create_subparser(subparsers, setup, 'setup', help_text='Quick setup. Will init db, add tests, add codelists, add indicators, refresh package data from Registry.')
    subparser.add_argument('--minimal', dest='minimal', action='store_true', default=False, help='Operate on a minimal set of packages')

    subparser = create_subparser(subparsers, enqueue_test, 'enqueue-test', help_text='Set a package to be tested (with --package-name')
    subparser.add_argument('--package-name', dest='package_name', help='Set name of package to be tested', required=True)
    subparser.add_argument('--filename', dest='filename', help='Set filename of data to test', required=True)

    subparser = create_subparser(subparsers, refresh, 'refresh', help_text='Refresh')
    subparser.add_argument('--package-name', dest='package_name', help='Set name of package to be tested')
    subparser.add_argument('--minimal', dest='minimal', action='store_true', default=False, help='Operate on a minimal set of packages')
    subparser.add_argument('--matching', dest='matching', help='Regular expression for matching packages')

    subparser = create_subparser(subparsers, activate_packages, 'activate-packages', help_text='Mark all packages as active')
    subparser.add_argument('--matching', dest='matching', help='Regular expression for matching packages', required=True)

    create_subparser(subparsers, create_aggregation_types, 'create-aggregation-types', help_text='Create basic aggregation types.')

    subparser = create_subparser(subparsers, aggregate_results, 'aggregate-results', help_text='Trigger result aggregation')
    subparser.add_argument('--runtime-id', dest='runtime_id', type=int, help='Runtime id (integer)', required=True)
    subparser.add_argument('--package-id', dest='package_id', type=int, help='Package id (integer)', required=True)

    create_subparser(subparsers, create_inforesult_types, 'create-inforesult-types', help_text='Create basic infroresult types.')

    create_subparser(subparsers, setup_organisations, 'setup-organisations', help_text='Setup organisations.')

    subparser = create_subparser(subparsers, setup_users, 'setup-users', help_text='Setup users and permissions.')
    subparser.add_argument('--filename', dest='filename', help='Set filename of data to test', required=True)

    subparser = create_subparser(subparsers, create_admin, 'create-admin', help_text='Create an admin user.')
    subparser.add_argument('--username', dest='username', help='The username of the new admin user')
    subparser.add_argument('--password', dest='password', help='The password of the new admin user')
    
    args = parser.parse_args()
    args.handler(args)

if __name__ == '__main__':
    main()

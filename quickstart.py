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
import iatidq.dqorganisations
import iatidq.dqaggregationtypes
import iatidq.dqtests
import iatidq.dqprocessing
import iatidq.test_level as test_level
import iatidq.inforesult
import optparse
import sys

which_packages = [
    (u'worldbank-tz', True),
    (u'unops-tz', True),
    (u'dfid-tz', True),
    (u'unitedstates-tz', True)
    ]

default_tests_filename="tests/tests.csv"
default_indicator_group_name="pwyf2013"
default_minimal_organisations = [
            {
            'organisation_name': 'World Bank',
            'organisation_code': '44002',
            'packagegroup_name': 'worldbank',
            'condition': None,
            'package_name': 'worldbank-tz'
            },
            {
            'organisation_name': 'USAID',
            'organisation_code': 'US-1',
            'packagegroup_name': 'unitedstates',
            'condition': 'participating-org[@role="Extending"][@ref="US-1"]',
            'package_name': 'unitedstates-tz'
            },
            {
            'organisation_name': 'MCC',
            'organisation_code': 'US-18',
            'packagegroup_name': 'unitedstates',
            'condition': 'participating-org[@role="Extending"][@ref="US-18"]',
            'package_name': 'unitedstates-tz'
            },
            {
            'organisation_name': 'UK, DFID',
            'organisation_code': 'GB-1',
            'packagegroup_name': 'dfid',
            'condition': None,
            'package_name': 'dfid-tz'
            }            
        ]

def refresh(options):
    pkg_names = None
    if options.package_name:
        pkg_names = [options.package_name]
    elif options.minimal_pkgs:
        pkg_names = [i[0] for i in which_packages]

    if pkg_names is not None:
        [ dqregistry.refresh_package_by_name(name) for name in pkg_names ]
    else:
        dqregistry.refresh_packages()

def activate_packages(options):
    dqregistry.activate_packages(which_packages, clear_revision_id=True)

def drop_all(options):
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

def download(options):
    if options.minimal_pkgs:
        for package_name, _ in which_packages:
            iatidq.dqdownload.run(package_name=package_name)
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
    print "Adding an aggregation type for all data"
    iatidq.dqaggregationtypes.addAggregationType({'name':'All data',
                                                'description': '',
                                                'test_id': None,
                                                'test_result':'1'})
    print "Adding an aggregation type for current data"
    currentdata_test = iatidq.dqtests.test_by_test_name(
        "activity-date[@type='start-planned']/@iso-date or transaction-date/@iso-date (for each transaction) is less than 13 months ago?"
        )
    iatidq.dqaggregationtypes.addAggregationType({'name':'Current data',
                                                'description': '',
                                                'test_id':currentdata_test.id,
                                                'test_result':'1'})

def create_inforesult_types(options):
    print "Adding an aggregation type"
    iatidq.inforesult.add_type("coverage", "Coverage")

def setup_common():
    print "Creating DB"
    iatidq.db.create_all()
    print "Adding hardcoded tests"
    iatidq.dqimporttests.hardcodedTests()
    print "Importing tests"
    iatidq.dqimporttests.importTestsFromFile(
        default_tests_filename,
        test_level.ACTIVITY)
    print "Importing indicators"
    iatidq.dqindicators.importIndicatorsFromFile(
        default_indicator_group_name,
        default_tests_filename)
    print "Importing indicator descriptions"
    iatidq.dqindicators.importIndicatorDescriptionsFromFile("pwyf2013", 
                                                            "tests/indicators.csv")
    print "Importing codelists"
    iatidq.dqcodelists.importCodelists()

def setup_packages_minimal():
    print "Creating packages"
    pkg_names = [i[0] for i in which_packages]

    if pkg_names is not None:
        [ dqregistry.refresh_package_by_name(name) for name in pkg_names ]
    else:
        print "No packages are defined in quickstart"

def setup_minimal(options):
    setup_common()

    setup_packages_minimal()

    print "Creating aggregation types."
    create_aggregation_types(options)
    create_inforesult_types(options)

    print "Setup complete."
    setup_organisations_minimal()
    print "Complete"

def setup_organisations_minimal():    
    for organisation in default_minimal_organisations:
        inserted_organisation = iatidq.dqorganisations.addOrganisation(
            organisation)
        if inserted_organisation is False:
            inserted_organisation = iatidq.dqorganisations.organisations(
                organisation['organisation_code'])
        thepackage = models.Package.query.filter_by(
            package_name=organisation['package_name']
                ).first()
        
        organisationpackage_data = {
            "organisation_id": inserted_organisation.id, 
            "package_id": thepackage.id,
            "condition": organisation["condition"]
            }
        iatidq.dqorganisations.addOrganisationPackage(organisationpackage_data)

def setup_organisations():
    print "Adding organisations"
    iatidq.dqorganisations.importOrganisationPackagesFromFile("tests/organisations_with_identifiers.csv")

def setup(options):
    setup_common()
    print "Refreshing package data from Registry"
    dqregistry.refresh_packages()

    setup_organisations()
    create_aggregation_types(options)
    create_inforesult_types(options)

    print "Setup complete."

def enqueue_test(options):
    assert options.package_name
    assert options.filename

    iatidq.dqruntests.enqueue_package_for_test(options.filename,
                                               options.package_name)
def aggregate_results(options):
    assert options.runtime_id
    assert options.package_id
    iatidq.dqprocessing.aggregate_results(options.runtime_id, options.package_id)

commands = {
    "drop_db": (drop_all, "Delete DB"),
    "init_db": (init_db, "Initialise DB"),
    "enroll_tests": (enroll_tests, "Enroll a CSV file of tests"),
    "clear_revisionid": (clear_revisionid, "Clear CKAN revision ids"),
    "import_codelists": (import_codelists, "Import codelists"),
    "download": (download, "Download packages"),
    "import_indicators": (
        import_indicators, 
        "Import indicators. Will try to assign indicators to existing tests."),
    "import_organisations": (
        import_organisations, 
        "Import organisations. Will try to create and assign organisations "
        "to existing packages."),
    "setup": (setup, """Quick setup. Will init db, add tests, add codelists, 
                      add indicators, refresh package data from Registry."""),
    "enqueue_test": (enqueue_test, "Set a package to be tested (with --package)"),
    "refresh": (refresh, "Refresh"),
    "activate_packages": (activate_packages, "Mark all packages as active"),
    "create_aggregation_types": (create_aggregation_types, "Create basic aggregation types."),
    "aggregate_results": (aggregate_results, "Trigger result aggregation"),
    "setup_minimal": (setup_minimal, "Quick minimal setup"),
    "create_inforesult_types": (create_inforesult_types, "Create basic infroresult types.")
}

def main():
    p = optparse.OptionParser()

    for k, v in commands.iteritems():
        handler, help_text = v
        option_name = "--" + k.replace("_", "-")
        p.add_option(option_name, dest=k, action="store_true", default=False, help=help_text)
    
    p.add_option("--runtime-id", dest="runtime_id",
                 type=int,
                 help="Runtime id (integer)")
    p.add_option("--package-id", dest="package_id",
                 type=int,
                 help="Package id (integer)")
    p.add_option("--level", dest="level",
                 type="int",
                 default=1,
                 help="Test level (e.g., 1 == Activity)")
    p.add_option("--minimal-pkgs", dest="minimal_pkgs",
                 action="store_true",
                 default=False,
                 help="Operate on a minimal set of packages")
    p.add_option("--package", dest="package_name",
                 help="Set name of package to be tested")
    p.add_option("--filename", dest="filename",
                 help="Set filename of data to test")
    p.add_option("--local-folder", dest="local_folder",
                 help="Set local folder where data to test is stored")

    options, args = p.parse_args()

    for mode, handler_ in commands.iteritems():
        handler, _ = handler_
        if getattr(options, mode, None):
            handler(options)
            return
    
    usage()

def usage():
    print "You need to specify which mode to run under"
    sys.exit(1)

if __name__ == '__main__':
    main()

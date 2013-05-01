
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import models, dqregistry 
from iatidq import db

import dqimporttests
import dqorganisations
import dqindicators
import dqcodelists
import test_level
import dqaggregationtypes
import dqtests
import inforesult

# FIXME: duplicated
which_packages = [
    (u'worldbank-tz', True),
    (u'unops-tz', True),
    (u'dfid-tz', True),
    (u'unitedstates-tz', True),
    (u'dfid-org', True)
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
            },
            {
            'organisation_name': 'UK, DFID',
            'organisation_code': 'GB-1',
            'packagegroup_name': 'dfid',
            'condition': None,
            'package_name': 'dfid-org'
            }         
        ]

def create_inforesult_types(options):
    print "Adding an info result type"
    inforesult.add_type("coverage", "Coverage")

def create_aggregation_types(options):
    print "Adding an aggregation type for all data"
    dqaggregationtypes.addAggregationType({'name':'All data',
                                           'description': '',
                                           'test_id': None,
                                           'test_result':'1'})
    print "Adding an aggregation type for current data"
    currentdata_test = dqtests.test_by_test_name(
        "activity-date[@type='start-planned']/@iso-date or transaction-date/@iso-date (for each transaction) is less than 13 months ago?"
        )
    dqaggregationtypes.addAggregationType({'name':'Current data',
                                           'description': '',
                                           'test_id':currentdata_test.id,
                                           'test_result':'1'})

def setup_common():
    print "Creating DB"
    db.create_all()
    print "Adding hardcoded tests"
    dqimporttests.hardcodedTests()
    print "Importing tests"
    dqimporttests.importTestsFromFile(
        default_tests_filename,
        test_level.ACTIVITY)
    print "Importing indicators"
    dqindicators.importIndicatorsFromFile(
        default_indicator_group_name,
        default_tests_filename)
    print "Importing indicator descriptions"
    dqindicators.importIndicatorDescriptionsFromFile("pwyf2013", 
                                                            "tests/indicators.csv")
    print "Importing codelists"
    dqcodelists.importCodelists()

def setup_packages_minimal():
    print "Creating packages"
    pkg_names = [i[0] for i in which_packages]

    if pkg_names is not None:
        [ dqregistry.refresh_package_by_name(name) for name in pkg_names ]
    else:
        print "No packages are defined in quickstart"

def setup_organisations_minimal():    
    for organisation in default_minimal_organisations:
        inserted_organisation = dqorganisations.addOrganisation(
            organisation)
        if inserted_organisation is False:
            inserted_organisation = dqorganisations.organisations(
                organisation['organisation_code'])
        thepackage = models.Package.query.filter_by(
            package_name=organisation['package_name']
                ).first()
        
        organisationpackage_data = {
            "organisation_id": inserted_organisation.id, 
            "package_id": thepackage.id,
            "condition": organisation["condition"]
            }
        dqorganisations.addOrganisationPackage(organisationpackage_data)

def setup_organisations():
    print "Adding organisations"
    dqorganisations.importOrganisationPackagesFromFile("tests/organisations_with_identifiers.csv")

def setup_packages():
    print "Refreshing package data from Registry"
    dqregistry.refresh_packages()

def setup(options):
    setup_common()

    if options.minimal:
        setup_packages_minimal()
    else:
        setup_packages()

    create_aggregation_types(options)
    create_inforesult_types(options)

    if options.minimal:
        setup_organisations_minimal()
    else:
        setup_organisations()

    print "Setup complete."

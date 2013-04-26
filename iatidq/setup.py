
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

    if options.minimal():
        setup_organisations_minimal()
    else:
        setup_organisations()

    print "Setup complete."

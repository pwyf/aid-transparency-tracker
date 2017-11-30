
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from getpass import getpass

from iatidataquality import app, db
from . import dqaggregationtypes
from . import dqcodelists
from . import dqimporttests
from . import dqindicators
from . import dqminimal
from . import dqorganisations
from . import dqtests
from . import dqregistry
from . import dqusers
from . import inforesult
from . import models
from . import survey
from . import test_level


default_tests_filename = "tests/tests.yaml"
default_infotypes_filename = "tests/infotypes.csv"
default_indicator_group_name = app.config["INDICATOR_GROUP"]
default_userdata_filename = 'tests/users.csv'
default_indicator_filename = 'tests/indicators.csv'
default_basic_countries_filename = 'tests/countries_basic.csv'


def create_inforesult_types():
    print("Adding info result types")
    inforesult.importInfoTypesFromFile(
        default_infotypes_filename,
        test_level.ACTIVITY)


def create_aggregation_types():
    print("Adding an aggregation type for all data")
    dqaggregationtypes.addAggregationType({'name':'All data',
                                           'description': '',
                                           'test_id': None,
                                           'test_result':'1'})
    print("Adding an aggregation type for current data")
    currentdata_test = models.Test.where(description='Current activities').first()
    dqaggregationtypes.addAggregationType({'name':'Current data',
                                           'description': '',
                                           'test_id':currentdata_test.id,
                                           'test_result':'1'})

def setup_common():
    print("Creating tables")
    db.create_all()
    print "Adding hardcoded tests"
    dqimporttests.hardcodedTests()
    print "Importing indicators"
    dqindicators.importIndicatorsFromFile(
        default_indicator_group_name,
        default_indicator_filename)
    print "Importing indicator descriptions"
    dqindicators.importIndicatorDescriptionsFromFile(
        app.config["INDICATOR_GROUP"],
        "tests/indicators.csv")
    print "Importing tests"
    dqimporttests.importTestsFromFile(
        default_tests_filename,
        test_level.ACTIVITY)
    print "Importing codelists"
    dqcodelists.importCodelists()
    print "Importing basic countries"
    codelist_name='countriesbasic'
    codelist_description='Basic list of countries for running tests against'
    dqcodelists.add_manual_codelist(default_basic_countries_filename, codelist_name, codelist_description)

def setup_packages_minimal():
    print "Creating packages"
    pkg_names = [i[0] for i in dqminimal.which_packages]

    if pkg_names is not None:
        [ dqregistry.refresh_package_by_name(name) for name in pkg_names ]
    else:
        print "No packages are defined in quickstart"

def setup_organisations_minimal():
    for organisation in dqminimal.default_minimal_organisations:
        inserted_organisation = dqorganisations.addOrganisation(
            organisation)
        if inserted_organisation is False:
            inserted_organisation = models.Organisation.where(organisation_code=organisation['organisation_code']).first()
        thepackage = models.Package.query.filter_by(
            package_name=organisation['package_name']
                ).first()

        if thepackage is None:
            print "Organisation lookup failure", organisation
            raise ValueError

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

def setup_admin_user(username=None, password=None):
    print('Creating admin user ...')
    while not username:
        username = raw_input('Username: ')
    while not password:
        password = getpass('Password: ')
    user_dict = {
        'username': username,
        'password': password,
    }
    user = dqusers.addUser(user_dict)
    permission = dqusers.addUserPermission({
        'user_id': user.id,
        'permission_name': 'admin',
        'permission_method': 'role'
    })
    print('Admin user successfully created.')

def setup(minimal):
    setup_common()

    if minimal:
        setup_packages_minimal()
    else:
        setup_packages()

    create_aggregation_types()
    create_inforesult_types()

    # associate with inforesults
    dqindicators.importIndicatorsFromFile(
        default_indicator_group_name,
        default_infotypes_filename, True)

    if minimal:
        setup_organisations_minimal()
    else:
        setup_organisations()

    print "Getting organisation frequency"
    dqorganisations.downloadOrganisationFrequency()
    print "Setting up survey"
    survey.setup.setupSurvey()

    setup_admin_user()

    print("Importing all users and creating permissions")
    dqusers.importUserDataFromFile(default_userdata_filename)
    print("Finished importing users")

    print "Setup complete."

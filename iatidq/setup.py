
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from getpass import getpass
import os

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
    currentdata_test = models.Test.where(description='Current data').first()
    dqaggregationtypes.addAggregationType({'name':'Current data',
                                           'description': '',
                                           'test_id':currentdata_test.id,
                                           'test_result':'1'})

def setup_common():
    print("Creating tables")
    db.create_all()
    print("Adding hardcoded tests")
    dqimporttests.hardcodedTests()
    print("Importing indicators")
    dqindicators.importIndicatorsFromFile(
        default_indicator_group_name,
        default_indicator_filename)
    print("Importing indicator descriptions")
    dqindicators.importIndicatorDescriptionsFromFile(
        app.config["INDICATOR_GROUP"],
        "tests/indicators.csv")
    print("Importing tests")
    dqimporttests.importTestsFromFile(
        default_tests_filename,
        test_level.ACTIVITY)

def setup_organisations():
    print("Adding organisations")
    org_file = os.environ.get('ORG_FILE', "tests/organisations_with_identifiers.csv")
    dqorganisations.importOrganisationPackagesFromFile(org_file)

def setup_packages():
    print("Refreshing package data from Registry")
    dqregistry.refresh_packages()

def setup_admin_user(username=None, password=None):
    print('Creating admin user ...')
    while not username:
        username = input('Username: ')
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

def setup():
    setup_common()

    setup_admin_user()

    # setup_packages()

    create_aggregation_types()
    create_inforesult_types()

    # associate with inforesults
    dqindicators.importIndicatorsFromFile(
        default_indicator_group_name,
        default_infotypes_filename, True)

    setup_organisations()

    print("Getting organisation frequency")
    dqorganisations.downloadOrganisationFrequency()
    print("Setting up survey")
    survey.setup.setupSurvey()

    # print("Importing all users and creating permissions")
    # dqusers.importUserDataFromFile(default_userdata_filename)
    # print("Finished importing users")

    print("Setup complete.")

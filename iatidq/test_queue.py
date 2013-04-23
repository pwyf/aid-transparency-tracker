
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import sys, os, json, ckan, urllib2
import itertools
from datetime import date, datetime
import models, dqprocessing, dqparsetests, dqpackages
import dqfunctions, queue
import dqprocessing
from lxml import etree
import re

from iatidq import db

# FIXME: this should be in config
download_queue='iati_tests_queue'

def aggregate_results(runtime, package_id):
    return dqprocessing.aggregate_results(runtime, package_id)

def get_organisations_for_testing(package_id):
    organisations = []
    conditions = []
    conditions_specified = False
    packageorganisations = dqpackages.packageOrganisations(package_id)

    if packageorganisations:
        for packageorganisation in packageorganisations:
            # add organisations to be tested;
            organisation_id = packageorganisation.Organisation.id
            condition = packageorganisation.OrganisationPackage.condition.strip()

            organisations.append({
            'organisation_id': organisation_id,
            'activities_xpath': "//iati-activity[%s]" % condition
                            })
            if condition is not "":
                conditions_specified = True
                conditions.append(condition)

        conditions_str = " or ".join(conditions)
        remainder_xpath = "//iati-activity[not(%s)]" % conditions_str

    # If conditions have been specified, then
    # run the tests again without an organisation
    # But exclude those activities that have already
    # been included above.

    if (not packageorganisations): 
        organisations.append({
        'organisation_id': None,
        'activities_xpath': "//iati-activity"
        })
    elif (conditions_specified is True):
        organisations.append({
        'organisation_id': None,
        'activities_xpath': remainder_xpath
        })
    return organisations

def test_type(test_name):
    if re.compile("(\S*) is on list (\S*)").match(test_name):
        return "list"
    else:
        return ""

def test_activity(runtime_id, package_id, result_identifier, 
                  result_hierarchy, data, test_functions, codelists,
                  organisation_id):

    xmldata = etree.fromstring(data)

    tests = models.Test.query.filter(models.Test.active == True).all()

    def add_result(test_id, the_result):
        newresult = models.Result()
        newresult.runtime_id = runtime_id
        newresult.package_id = package_id
        newresult.test_id = test.id
        newresult.result_data = the_result
        newresult.result_identifier = result_identifier
        newresult.result_hierarchy = result_hierarchy
        newresult.organisation_id = organisation_id
        db.session.add(newresult)

    # | test_result == True  -> 1
    # | test_result == False -> 0
    # | exception            -> 2 (exceptions aren't counted against publishers)
    def execute_test(test_id, test_type):
        try:
            if (test_type == "list"):
                data = {
                    "activity": xmldata,
                    "lists": codelists
                }
                return int(test_functions[test_id](data))
            else:
                return int(test_functions[test_id](xmldata))
        except:
            return 2

    def execute_and_record(test):
        the_result = execute_test(test.id, test_type(test.name))
        add_result(test.id, the_result)

    test_exists = lambda t: t.id in test_functions
    tests = itertools.ifilter(test_exists, tests)
    
    [ execute_and_record(test) for test in tests ]

    return "Success"

def parse_xml(file_name):
    try:
        data = etree.parse(file_name)
        return True, data
    except etree.XMLSyntaxError:
        return False, None

def check_file(test_functions, codelists, file_name, 
                runtime_id, package_id, context=None):
    try:
        xml_parsed, data = parse_xml(file_name)

        dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, 
                                           xml_parsed)
        db.session.commit()

        organisations = get_organisations_for_testing(package_id)
        #TODO: Implement for each organisation.
        # This is a bit crude because it only works for
        # iati-activities, and not organisation files.
        # But it's sufficient for now.

        if not xml_parsed:
            print "XML parse failed"
            return False

        def get_result_hierarchy(activity):
            hierarchy = activity.get('hierarchy', default=None)
            if hierarchy is "":
                return None
            return hierarchy

        def run_test_activity(organisation_id, activity):
            result_hierarchy = get_result_hierarchy(activity)
            
            result_identifier = activity.find('iati-identifier').text.decode()
            activity_data = etree.tostring(activity)

            res = test_activity(runtime_id, package_id, 
                                result_identifier, result_hierarchy,
                                activity_data, test_functions, 
                                codelists, organisation_id)
            db.session.commit()

        assert len(organisations) > 0
        for organisation in organisations:
            org_activities = data.xpath(organisation['activities_xpath'])
            org_id = organisation['organisation_id']

            [ run_test_activity(org_id, activity) 
              for activity in org_activities ]

        print "Aggregating results..."
        dqprocessing.aggregate_results(runtime_id, package_id)
        print "Finished aggregating results"
        db.session.commit()    

        dqfunctions.add_test_status(package_id, 3, commit=True)
        return True
    except Exception, e:
        print "Exception in check_file ", e
        raise

def dequeue_download(body, test_functions, codelists):
    try:
        args = json.loads(body)
        check_file(test_functions, 
                   codelists,
                   args['filename'],
                   args['runtime_id'],
                   args['package_id'],
                   args['context'])
    except Exception, e:
        print "Exception in dequeue_download", e

def run_test_queue():
    from dqparsetests import test_functions as tf
    test_functions = tf()
    import dqcodelists
    codelists = dqcodelists.generateCodelists()

    for body in queue.handle_queue_generator(download_queue):
        dequeue_download(body, test_functions, codelists)

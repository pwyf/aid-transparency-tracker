#!/usr/bin/env python

# this line must precede ckan import
import config
import sys, os, json, ckan, urllib2
from datetime import date, datetime
from iatidataquality import models, db, dqprocessing, dqparsetests, \
    dqfunctions, queue
from iatidataquality.dqprocessing import add_hardcoded_result
from lxml import etree
from iatidataquality.util import ensure_download_dir


# FIXME: this should be in config
download_queue='iati_tests_queue'

def aggregate_results(runtime, package_id):
    return dqprocessing.aggregate_results(runtime, package_id)

def test_activity(runtime_id, package_id, result_identifier, data, 
                  test_functions, result_hierarchy):
    xmldata = etree.fromstring(data)

    tests = models.Test.query.filter(models.Test.active == True).all()
    conditions = models.TestCondition.query.filter(
        models.TestCondition.active == True).all()
    
    for test in tests:
        if not test.id in test_functions:
            continue
        try:
            if test_functions[test.id](xmldata):
                the_result = 1
            else:
                the_result = 0
        # If an exception is not caught in test functions,
        # it should not count against the publisher
        except Exception:
            the_result = 2

        newresult = models.Result()
        newresult.runtime_id = runtime_id
        newresult.package_id = package_id
        newresult.test_id = test.id
        newresult.result_data = the_result
        newresult.result_identifier = result_identifier
        newresult.result_hierarchy = result_hierarchy
        db.session.add(newresult)
    return "Success"

def check_file(file_name, runtime_id, package_id, context=None):
    try:
        try:
            data = etree.parse(file_name)
        except etree.XMLSyntaxError:
            dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, False)
            return
        dqprocessing.add_hardcoded_result(-3, runtime_id, package_id, True)
        from iatidataquality.dqparsetests import test_functions as tf
        test_functions = tf()

        def get_result_hierarchy(activity):
            hierarchy = activity.get('hierarchy', default=None)
            if hierarchy is "":
                return None
            return hierarchy

        for activity in data.findall('iati-activity'):
            result_hierarchy = get_result_hierarchy(activity)

            result_identifier = activity.find('iati-identifier').text
            activity_data = etree.tostring(activity)

            res = test_activity(runtime_id, package_id, 
                                result_identifier, activity_data, 
                                test_functions, result_hierarchy)

        db.session.commit()
        print "Aggregating results..."
        dqprocessing.aggregate_results(runtime_id, package_id)
        print "Finished aggregating results"
        db.session.commit()    
        dqfunctions.add_test_status(package_id, 3)
    except Exception, e:
        print "Exception in check_file ", e

def dequeue_download(body):
    args = json.loads(body)
    try:
        check_file(args['filename'],
                  args['runtime_id'],
                  args['package_id'],
                  args['context'])
    except Exception, e:
        print "Exception in dequeue_download", e

def callback_fn(ch, method, properties, body):
    dequeue_download(body)
    ch.basic_ack(delivery_tag = method.delivery_tag)

def run_test_queue():
    while True:
        queue.handle_queue(download_queue, callback_fn)

if __name__ == '__main__':
    print "Starting up..."
    directory = config.DATA_STORAGE_DIR
    ensure_download_dir(directory)
    run_test_queue()

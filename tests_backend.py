import sys, os, json, ckan, pika, urllib2
from datetime import date, datetime
from iatidataquality import models, db, DATA_STORAGE_DIR, dqprocessing, dqparsetests
from iatidataquality.dqprocessing import add_hardcoded_result
from lxml import etree


download_queue='iati_tests_queue'

def aggregate_results(runtime, package_id):
    return dqprocessing.aggregate_results(runtime, package_id)

def test_activity(runtime_id, package_id, result_identifier, data, test_functions, result_hierarchy):
    xmldata = etree.fromstring(data)

    tests = models.Test.query.filter(models.Test.active == True).all()
    conditions = models.TestCondition.query.filter(models.TestCondition.active == True).all()
    
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
            continue

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
        for activity in data.findall('iati-activity'):
            try:
                result_hierarchy = activity.get('hierarchy')
            except KeyError:
                result_hierarchy = None
            result_identifier = activity.find('iati-identifier').text
            activity_data = etree.tostring(activity)
            res = test_activity(runtime_id, package_id, result_identifier, activity_data, test_functions, result_hierarchy)
        db.session.commit()
        dqprocessing.aggregate_results(runtime_id, package_id)
        db.session.commit()
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

def get_connection(host):
    count = 0.4
    while count < 60:
        try:            
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host))
            return connection
        except:
            time.sleep(count)
            count *= 1.7
    sys.exit(1)

def handle_queue(queue_name, callback_fn):
    try:
        connection = get_connection('localhost')
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(callback_fn, queue=queue_name)
        channel.start_consuming()
    except:
        pass 
    finally:
        connection.close()

def callback_fn(ch, method, properties, body):
    dequeue_download(body)
    ch.basic_ack(delivery_tag = method.delivery_tag)

if __name__ == '__main__':
    print "Starting up..."
    directory = DATA_STORAGE_DIR()
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception, e:
            print "Failed:", e
            print "Couldn't create directory"
    while True:
        handle_queue(download_queue, callback_fn)

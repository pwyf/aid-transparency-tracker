from db import *
import models, dqprocessing, dqparsetests, pika, json

download_queue='iati_tests_queue'

def DATA_STORAGE_DIR():
    return app.config["DATA_STORAGE_DIR"]

#@celery.task(name="iatidataquality.load_package", track_started=True)
def load_packages(runtime):
    output = []
    
    path = DATA_STORAGE_DIR()
    for package in models.Package.query.filter_by(active=True).order_by(models.Package.id).all():
        # check file; add one task per package

        filename = path + '/' + package.package_name + '.xml'

        # run tests on file
        enqueue_download(filename, runtime, package.id, None)

        output.append(package.package_name)
    return {'testing_packages': output}

def enqueue(args):
    body = json.dumps(args)
    
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=download_queue, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=download_queue,
                          body=body,
                          properties=pika.BasicProperties(delivery_mode=2))
    connection.close()

def enqueue_download(filename, runtime_id, package_id, context=None):
    args = {
        'filename': filename,
        'runtime_id': runtime_id,
        'package_id': package_id,
        'context': context
        }
    enqueue(args)

# start testing all packages
def start_testing():
    newrun = models.Runtime()
    db.session.add(newrun)
    db.session.commit()
    return load_packages(newrun.id)

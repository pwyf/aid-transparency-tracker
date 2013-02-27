from db import *
import models, dqprocessing, dqparsetests, pika, json

download_queue='iati_tests_queue'

def DATA_STORAGE_DIR():
    return app.config["DATA_STORAGE_DIR"]

def load_packages(runtime, package_name=None):
    output = []
    
    path = DATA_STORAGE_DIR()

    if (package_name is not None):
        package = models.Package.query.filter_by(package_name=package_name).first()
        filename = path + '/' + package.package_name + '.xml'
        # Run tests on file -> send to queue
        enqueue_download(filename, runtime, package.id, None)
        output.append(package.package_name)
    else:
        for package in models.Package.query.filter_by(active=True).order_by(models.Package.id).all():
            filename = path + '/' + package.package_name + '.xml'
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

# start testing all packages, or just one if provided
def start_testing(package_name=None):
    newrun = models.Runtime()
    db.session.add(newrun)
    db.session.commit()
    return load_packages(newrun.id, package_name)

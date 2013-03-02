from db import *
import models, dqprocessing, dqparsetests, json, dqfunctions
import queue
import os

# FIXME: this should be in config
download_queue='iati_tests_queue'

def DATA_STORAGE_DIR():
    return app.config["DATA_STORAGE_DIR"]

def load_packages(runtime, package_name=None):
    output = []
    
    path = DATA_STORAGE_DIR()

    def load_package(package):
        dqfunctions.add_test_status(package.id, 2)
        filename = os.path.join(path, package.package_name + '.xml')
        # Run tests on file -> send to queue
        enqueue_download(filename, runtime, package.id, None)
        output.append(package.package_name)

    if (package_name is not None):
        package = models.Package.query.filter_by(package_name=package_name).first()
        load_package(package)
    else:
        for package in models.Package.query.filter_by(active=True).order_by(models.Package.id).all():
            load_package(package)
    return {'testing_packages': output}

def enqueue_download(filename, runtime_id, package_id, context=None):
    args = {
        'filename': filename,
        'runtime_id': runtime_id,
        'package_id': package_id,
        'context': context
        }
    queue.enqueue(args)

# start testing all packages, or just one if provided
def start_testing(package_name=None):
    newrun = models.Runtime()
    db.session.add(newrun)
    db.session.commit()
    return load_packages(newrun.id, package_name)

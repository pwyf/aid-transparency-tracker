
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db, app

import models, dqprocessing, json, dqfunctions
import queue
import os

import testrun
import package_status

# FIXME: this should be in config
tests_queue='iati_tests_queue'

def load_packages(runtime, package_name=None):
    output = []
    
    path = app.config["DATA_STORAGE_DIR"]

    def load_package(package):
        dqfunctions.add_test_status(package.id, package_status.TO_DOWNLOAD)
        filename = os.path.join(path, package.package_name + '.xml')
        # Run tests on file -> send to queue
        enqueue_download(filename, runtime, package.id, None)
        output.append(package.package_name)

    if (package_name is not None):
        package = models.Package.query.filter_by(
            package_name=package_name).first()
        packages = [ package ]
    else:
        packages = models.Package.query.filter_by(
            active=True).order_by(models.Package.id).all()
    [ load_package(pkg) for pkg in packages ]

    return {'testing_packages': output}

def enqueue_download(filename, runtime_id, package_id, context=None):
    args = {
        'filename': filename,
        'runtime_id': runtime_id,
        'package_id': package_id,
        'context': context
        }
    queue.enqueue(tests_queue, args)

def enqueue_package_for_test(filename, package_name):
    package = models.Package.query.filter_by(
        package_name=package_name).first()
    package_id = package.id
    runtime_id = testrun.start_new_testrun().id
    enqueue_download(filename, runtime_id, package_id)
    
# start testing all packages, or just one if provided
def start_testing(package_name=None):
    newrun = testrun.start_new_testrun()
    return load_packages(newrun.id, package_name)

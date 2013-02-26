#!/usr/bin/env python
import sys
import ckan    
from datetime import date, datetime
import os
from iatidataquality import models
from iatidataquality import db, DATA_STORAGE_DIR
import json

import sys
import pprint
pp = pprint.PrettyPrinter(indent=2)

db.create_all()
runtime = models.Runtime()
db.session.add(runtime)
db.session.commit()

download_queue = 'iati_download_queue'
import pika

def get_package(pkg, package):

    pkg_name = package.package_name
    new_package = False
    update_package = False
    # Check if package already exists; if it has not been updated more 
    # recently than the database, then download it again
    check_package = package

    if ((package.package_revision_id) != (pkg['revision_id'])):
        # if the package has been updated, 
        # then download it and update the package data
        update_package = True
        print "Updating package"

    if (update_package or new_package):
        # Download the file

        resources = pkg.get('resources', [])
        assert len(resources) <= 1
        if resources == []:
            return

        resource = resources[0]
        enqueue_download(pkg_name,
                         resource['url'], pkg, update_package)
    else:
        print update_package, new_package
        print "Already have package", pkg["name"]

def run():
    # Get list of packages from DB

    url = 'http://iatiregistry.org/api'
    import ckanclient
    registry = ckanclient.CkanClient(base_location=url)

    packages = models.Package.query.filter_by(active=True).all()

    for package in packages:
        pkg = registry.package_entity_get(package.package_name)
        get_package(pkg, package)

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

def enqueue_download(pkg_name, filename, pkg, update_package):
    args = {
        'pkg_name': pkg_name,
        'file': filename,
        'pkg': pkg,
        'update_package': update_package
        }
    enqueue(args)

if __name__ == '__main__':
    print "NB, you need to run iatidataquality/quickstart.py before running this script in order to populate the list of packages"
    run()

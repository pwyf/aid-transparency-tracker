#!/usr/bin/env python
import sys
import ckan    
from datetime import date, datetime
import os
from iatidataquality import models, db,  DATA_STORAGE_DIR
import json

import sys
import pprint
pp = pprint.PrettyPrinter(indent=2)

runtime = models.Runtime()
db.session.add(runtime)
db.session.commit()

download_queue = 'iati_download_queue'
import pika

def get_package(pkg, pkg_name):
    new_package = False
    update_package = False
    # Check if package already exists; if it has not been updated more 
    # recently than the database, then download it again
    check_package = models.Package.query.filter_by(package_ckan_id = 
                                                   pkg['id']).first()
    if (check_package):
        # found a package
        if ((check_package.package_revision_id) != (pkg['revision_id'])):
            # if the package has been updated, 
            # then download it and update the package data
            update_package = True
            print "Updating package"
    else:
        # package not already downloaded
        new_package = True
        update_package = False

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
    url = 'http://iatiregistry.org/api'
    import ckanclient
    registry = ckanclient.CkanClient(base_location=url)

    for pkg_name in registry.package_register_get():
            pkg = registry.package_entity_get(pkg_name) 

            get_package(pkg, pkg_name)

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
    run()

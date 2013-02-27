#!/usr/bin/env python
import sys, os, json, pika, ckan, ckanclient
from datetime import date, datetime
import models, dqfunctions
from db import *

db.create_all()
runtime = models.Runtime()
db.session.add(runtime)
db.session.commit()

download_queue = 'iati_download_queue'

def get_package(pkg, package, runtime_id):

    new_package = False
    update_package = False
    # Check if package already exists; if it has not been updated more 
    # recently than the database, then download it again
    check_package = package

    if ((package.package_revision_id) != (pkg['revision_id'])):
        # if the package has been updated, 
        # then download it and update the package data
        update_package = True
        print "Updating package", pkg['name']

    if (update_package or new_package):
        resources = pkg.get('resources', [])
        assert len(resources) <= 1
        if resources == []:
            return

        resource = resources[0]
        enqueue_download(package, pkg, 
                         resource['url'], update_package, runtime_id)
    else:
        print "Package", pkg["name"], "is already the latest version"
        dqfunctions.add_test_status(package.id, 4)

def run(package_name=None):
    # Get list of packages from DB

    url = 'http://iatiregistry.org/api'
    registry = ckanclient.CkanClient(base_location=url)

    # `pkg` is the Dataset entity
    # `package` is the name of the package
    # `runtime.id` is the runtime that this is under

    # This might be too slow for web UI, because it makes one query 
    # per package to the Registry to check whether it's been updated
    if (package_name is None):
        packages = models.Package.query.filter_by(active=True).all()
        for package in packages:
            dqfunctions.add_test_status(package.id, 1)
            pkg = registry.package_entity_get(package.package_name)
            get_package(pkg, package, runtime.id)
    else:    
        package = models.Package.query.filter_by(package_name=package_name).first()
        dqfunctions.add_test_status(package.id, 1)
        pkg = registry.package_entity_get(package.package_name)
        get_package(pkg, package, runtime.id)
        

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

def enqueue_download(package, pkg, url, update_package, runtime_id):
    args = {
        'package_id': package.id,
        'package_name': package.package_name,
        'pkg': pkg,
        'url': url,
        'update_package': update_package,
        'runtime_id': runtime_id
        }
    enqueue(args)

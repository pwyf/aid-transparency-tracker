#!/usr/bin/env python
import sys, os, json, pika, ckan, ckanclient
from datetime import date, datetime
import models
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

def run():
    # Get list of packages from DB

    url = 'http://iatiregistry.org/api'
    registry = ckanclient.CkanClient(base_location=url)

    packages = models.Package.query.filter_by(active=True).all()

    # `pkg` is the Dataset entity
    # `package` is the name of the package
    # `runtime.id` is the runtime that this is under

    # This might be too slow for web UI, because it makes one query 
    # per package to the Registry to check whether it's been updated
    for package in packages:
        pstatus = models.PackageStatus()
        pstatus.package_id = package.id
        pstatus.status = 1
        db.session.add(pstatus)
        db.session.commit()
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

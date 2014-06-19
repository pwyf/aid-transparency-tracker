
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import sys, os, json, ckan, ckanclient, urllib2
import queue
from datetime import date, datetime

from iatidq import db

import models
from dqfunctions import add_test_status, packages_from_registry
import package_status
import testrun
import package_status

download_queue = 'iati_download_queue'

IATIUPDATES_URL = "http://tracker.publishwhatyoufund.org/iatiupdates/api/package/hash/"
REGISTRY_URL = "http://iatiregistry.org/api/2/search/dataset?fl=id,name,groups,title,revision_id&offset=%s&limit=1000"
CKANurl = 'http://iatiregistry.org/api'

def get_package(pkg, package, runtime_id):
    new_package = False
    update_package = False
    # Check if package already exists; if it has not been updated more 
    # recently than the database, then download it again
    check_package = package

    if ((package.package_metadata_modified) != (pkg['metadata_modified'])):
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
        enqueue_download(package, runtime_id)
    else:
        print "Package", pkg["name"], "is already the latest version"
        add_test_status(package.id, package_status.UP_TO_DATE)

def download_packages(runtime):
    # Check registry for packages list
    registry_packages = [ (pkg["name"], pkg["metadata-modified"]) 
                          for pkg in packages_from_registry(IATIUPDATES_URL) ]

    print "Found", len(registry_packages),"packages on the IATI Registry"
    print "Checking for updates, calculating and queuing packages;"
    print "this may take a moment..."

    registry_packages=dict(registry_packages)
    testing_packages=[]
    packages = models.Package.query.filter_by(active=True).all()

    print registry_packages
    for package in packages:
        name = package.package_name
        print name
        print package.package_metadata_modified
        
        # Handle automatically retrieved packages (from Registry)
        if package.man_auto == 'auto':
            try:
                if package.package_metadata_modified != registry_packages[name]:
                    print "Need to update package", name
                    # need to add status here, because otherwise the status could 
                    # be written to DB after the package has finished testing
                    add_test_status(package.id, package_status.NEW)
                    testing_packages.append(package.id)
                    enqueue_download(package, runtime.id)
                else:
                    print "Packages have the same ID"
                    print "Metadata modified is", package.package_metadata_modified
                    print "Registry package name is", registry_packages[name]
            except KeyError, e:
                if name not in registry_packages:
                    print "name wasn't there"
                    # TODO: handle deleted packages; for now just pass
                    pass
                else:
                    raise Exception, e

        # Handle manually added packages
        else:
            if ((package.package_metadata_modified == "") or (package.package_metadata_modified == None)):
                print "Need to update manual package", name
                # need to add status here, because otherwise the status could 
                # be written to DB after the package has finished testing
                add_test_status(package.id, package_status.NEW)
                testing_packages.append(package.id)
                enqueue_download(package, runtime.id)
            else:
                print "Not testing manual package, because it has not been set to refresh"

    print "Testing", len(testing_packages), "packages"

def download_package(runtime, package_name):
    package = models.Package.query.filter_by(
        package_name=package_name).first()
    add_test_status(package.id, package_status.NEW)

    registry = ckanclient.CkanClient(base_location=CKANurl)  

    pkg = registry.package_entity_get(package.package_name)
    try:
        if pkg['metadata_modified'] == package.package_metadata_modified:
            add_test_status(package.id, package_status.UP_TO_DATE)
        else:
            get_package(pkg, package, runtime.id)
    except IndexError:
        print "Package has no resources"
        pass
    except KeyError:
        print "Package resource has no package_metadata_modified"
        pass

def run(package_name=None):
    runtime = testrun.start_new_testrun()
    # Get list of packages from DB
    if (package_name is None):
        download_packages(runtime)
    else:
        download_package(runtime, package_name)

def enqueue_download(package, runtime_id):
    args = {
        'package_id': package.id,
        'package_name': package.package_name,
        'runtime_id': runtime_id,
        'man_auto': package.man_auto
        }
    queue.enqueue(download_queue, args)

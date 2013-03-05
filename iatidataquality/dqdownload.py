
import sys, os, json, ckan, ckanclient, urllib2
import queue
from datetime import date, datetime

from iatidataquality import db

import models, dqfunctions

download_queue = 'iati_download_queue'
REGISTRY_URL = "http://iatiregistry.org/api/2/search/dataset?fl=id,name,groups,title,revision_id&offset=%s&limit=1000"

def run(package_name=None):
    runtime = models.Runtime()
    db.session.add(runtime)
    db.session.commit()
    # Get list of packages from DB
    if (package_name is None):
        # Check registry for packages list
        registry_packages = []
        offset = 0
        while True:  
            data = urllib2.urlopen(REGISTRY_URL % (offset), timeout=60).read()
            print (REGISTRY_URL % (offset))
            data = json.loads(data)

            if len(data["results"]) < 1:
                break          

            [ registry_packages.append(
                    (pkg['name'], pkg['revision_id'])
                    ) for pkg in data["results"] ]

            offset += 1000

        print "Found", len(registry_packages),"packages on the IATI Registry"
        print "Checking for updates, calculating and queuing packages;"
        print "this may take a moment..."
        registry_packages=dict(registry_packages)
        
        testing_packages=[]
        packages = models.Package.query.filter_by(active=True).all()
        for package in packages:
            name = package.package_name
            if package.package_revision_id != registry_packages[name]:
                testing_packages.append(package.id)
                enqueue_download(package, runtime.id)
        print "Testing",len(testing_packages),"packages"
        print "Writing status of packages..."
        for tp in testing_packages:
            dqfunctions.add_test_status(tp, 1, commit=False)
        db.session.commit()
    else:    
        package = models.Package.query.filter_by(
            package_name=package_name).first()
        dqfunctions.add_test_status(package.id, 1)
        CKANurl = 'http://iatiregistry.org/api'
        registry = ckanclient.CkanClient(base_location=CKANurl)  
        pkg = registry.package_entity_get(package.package_name)
        if pkg['revision_id'] == package.package_revision_id:
            dqfunctions.add_test_status(package.id, 4)
        else:
            get_package(package, runtime.id)

def enqueue_download(package, runtime_id):
    args = {
        'package_id': package.id,
        'package_name': package.package_name,
        'runtime_id': runtime_id
        }
    queue.enqueue(download_queue, args)

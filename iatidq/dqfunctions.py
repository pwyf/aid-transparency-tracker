
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import json
import urllib2

from iatidq import db
import models

def add_test_status(package_id, status_id):
    with db.session.begin():
        pstatus = models.PackageStatus()
        pstatus.package_id = package_id
        pstatus.status = status_id
        db.session.add(pstatus)

def clear_revisions():
    with db.session.begin():
        for pkg in models.Package.query.filter(
            models.Package.package_revision_id!=None, 
            models.Package.active == True
            ).all():

            pkg.package_revision_id = None
        
            db.session.add(pkg)

def packages_from_registry(registry_url):
    #offset = 0
    #while True:
    #data = urllib2.urlopen(registry_url % (offset), timeout=60).read()
    #print (registry_url % (offset))
    data = urllib2.urlopen(registry_url, timeout=60).read()
    print registry_url
    data = json.loads(data)

    #if len(data["results"]) < 1:
    #    break          

    for pkg in data["data"]:
        yield pkg

    #offset += 1000

def get_package_organisations(iatiupdates_url):
    data = urllib2.urlopen(iatiupdates_url, timeout=60).read()
    print iatiupdates_url
    data = json.loads(data)
    package_data = data["data"]
    out = {}
    for pd in package_data:
        out[pd['name']] = pd['organization']
    return out

def packages_from_iati_registry(registry_url):
    offset = 0
    while True:
        data = urllib2.urlopen(registry_url % (offset), timeout=60).read()
        print (registry_url % (offset))
        data = json.loads(data)

        if len(data["results"]) < 1:
            break          

        for pkg in data["results"]:
            yield pkg

        offset += 1000

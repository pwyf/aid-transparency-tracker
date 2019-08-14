
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import json
import urllib.request, urllib.error, urllib.parse

from iatidataquality import db
from . import models


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

def get_package_organisations(iatiupdates_url):
    data = urllib.request.urlopen(iatiupdates_url, timeout=60).read()
    print(iatiupdates_url)
    data = json.loads(data)
    package_data = data["data"]
    out = {}
    for pd in package_data:
        out[pd['name']] = pd['organization']
    return out

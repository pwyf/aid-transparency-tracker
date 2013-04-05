
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db
import models

def package_status(package_id):
    return models.PackageStatus.query.filter_by(package_id=package_id).order_by("runtime_datetime desc").first()

def packages():
    return models.Package.query.order_by(models.Package.package_name).all()

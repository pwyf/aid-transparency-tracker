
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

def packageGroups():
    return models.PackageGroup.query.order_by(models.PackageGroup.name).all()

def packageOrganisations(package_id):
    if package_id is not None:
        packageorganisations = db.session.query(models.Organisation,
                                             models.OrganisationPackage
                        ).filter(models.Package.id==package_id
                        ).join(models.OrganisationPackage
                        ).join(models.Package
                        ).all()
        return packageorganisations
    else:
        return False

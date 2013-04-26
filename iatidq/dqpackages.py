
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

def packages(package_id=None):
    if id is not None:
        return models.Package.query.filter_by(id=package_id).order_by(models.Package.package_name).first()
    else:
        return models.Package.query.order_by(models.Package.package_name).all()

def packages_by_name(package_name):
    return models.Package.query.filter_by(package_name=package_name).order_by(models.Package.package_name).first()

def packages_by_packagegroup(packagegroup_id=None):
    return models.Package.query.filter(models.PackageGroup.id==packagegroup_id
                ).join(models.PackageGroup
                ).order_by(models.Package.package_name
                ).all()    

def packages_by_packagegroup_name(packagegroup_name=None):
    return models.Package.query.filter(models.PackageGroup.name==packagegroup_name
                ).join(models.PackageGroup
                ).order_by(models.Package.package_name
                ).all()    

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

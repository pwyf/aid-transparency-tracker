
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db
import dqorganisations
import models
import unicodecsv

def importManualPackages(organisation_code, filename, prefix_url):
    with file(filename) as fh:
        packages = unicodecsv.DictReader(fh)
        organisation = dqorganisations.organisations(organisation_code)
        for package in packages:
            data = {
                'package_name': "manual_" + package['package_name'],
                'package_title': package['package_title'],
                'source_url': prefix_url + package['filename'],
                'man_auto': 'man',
                'active': True
            }
            print "Adding package", package["package_name"]
            newp = addPackage(data)
            if newp:
                dqorganisations.addOrganisationPackage({
                    'organisation_id': organisation.id,
                    'package_id': newp.id,
                    'condition': None
                })
    print "Success"
            

def addPackage(data):
    checkP = models.Package.query.filter_by(
            package_name=data['package_name']).first()
    if not checkP:
        with db.session.begin():
            p = models.Package()
            p.package_name = data['package_name']
            p.package_title = data['package_title']
            p.source_url = data['source_url']
            p.man_auto = data['man_auto']
            p.active=data['active']
            p.hash=data.get('hash')
            db.session.add(p)
        return p
    else:
        return False

def updatePackage(data):
    checkP = models.Package.query.filter_by(
            id=data['package_id']).first()
    checkOK = models.Package.query.filter_by(package_name=data['package_name']).first()
    if checkP:
        if (checkOK and checkOK.id!=checkP.id):
            return False
        with db.session.begin():
            checkP.package_name = data['package_name']
            checkP.package_title = data['package_title']
            checkP.source_url = data['source_url']
            checkP.man_auto = data['man_auto']
            checkP.active=data['active']
            checkP.hash=data['hash']
            db.session.add(checkP)
        return checkP
    return False

def package_status(package_id):
    return models.PackageStatus.query.filter_by(
        package_id=package_id).order_by("runtime_datetime desc").first()

def packages(package_id=None):
    if package_id is not None:
        return models.Package.query.filter_by(
            id=package_id).order_by(models.Package.package_name).first()
    else:
        return models.Package.query.order_by(models.Package.package_name).all()

def packages_by_name(package_name):
    return models.Package.query.filter_by(
        package_name=package_name).order_by(models.Package.package_name).first()

def packages_by_packagegroup(packagegroup_id=None):
    return models.Package.query.filter(
        models.PackageGroup.id==packagegroup_id
                ).join(models.PackageGroup
                ).order_by(models.Package.package_name
                ).all()    

def packages_by_packagegroup_name(packagegroup_name=None):
    return models.Package.query.filter(
        models.PackageGroup.name==packagegroup_name
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

def packageGroupOrganisations(packagegroup_name):
    if packagegroup_name is not None:
        packagegrouporganisations = db.session.query(models.Organisation
                        ).filter(models.PackageGroup.name==packagegroup_name
                        ).join(models.OrganisationPackageGroup
                        ).join(models.PackageGroup
                        ).all()
        return packagegrouporganisations
    else:
        return False

def get_organisations_for_testing(package_id):
    organisations = []
    conditions = []
    conditions_unbracketed = []
    packageorganisations = packageOrganisations(package_id)

    dummy = [{
            'organisation_id': None,
            'activities_xpath': "//iati-activity"
            }]

    if not packageorganisations:
        return dummy

    for packageorganisation in packageorganisations:
        # add organisations to be tested;
        organisation_id = packageorganisation.Organisation.id
        condition = packageorganisation.OrganisationPackage.condition
        if condition == '':
            condition = None
        if condition is not None:
            # unicode-escape is necessary to deal with an umlaut in a condition.
            condition_unbracketed = condition.decode('unicode-escape').strip()
            condition = u"[" + condition_unbracketed + u"]"
            conditions.append(condition)
            conditions_unbracketed.append(condition_unbracketed)
        else:
            condition_unbracketed = u""
            condition = u""

        organisations.append({
                'organisation_id': organisation_id,
                'activities_xpath': u"//iati-activity%s" % condition
                })

    conditions_str = " or ".join(conditions_unbracketed)
    remainder_xpath = u"//iati-activity[not(%s)]" % conditions_str

    if conditions:
        organisations.append({
                'organisation_id': None,
                'activities_xpath': remainder_xpath
                })

    if organisations:
        return organisations
    return dummy


#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

from sqlalchemy import func

import summary

from models import *
import csv
import util
import unicodecsv

def checkCondition(row):
    pg_cond = row.get('packagegroup_condition', '')
    if pg_cond != '':
        return pg_cond
    return None

def importOrganisationPackagesFromFile(filename, 
                                       organisation_c=None, 
                                       organisation_n=None):
    with file(filename) as fh:
        return _importOrganisationPackages(organisation_c, organisation_n, 
                                           fh, True)

def _importOrganisationPackages(organisation_c, organisation_n, fh, local):
    def get_checkp_code_name():
        if organisation_c is None:
            return (
                organisations(row['organisation_code']),
                row['organisation_code'],
                row['organisation_name']
                )
        return (
            organisations(organisation_c),
            organisation_c,
            organisation_n
            )

    def get_organisation(checkP):
        if checkP:
            return checkP
        return addOrganisation(
            {"organisation_name": organisation_name,
             "organisation_code": organisation_code
             })
    
    def get_packages(organisation_code):
        return Package.query.filter(
            PackageGroup.publisher_iati_id==organisation_code
            ).join(PackageGroup).all()

    def get_packagegroup(organisation_code):
        return PackageGroup.query.filter(
            PackageGroup.publisher_iati_id==organisation_code
            ).all()

    def get_packagegroup_by_name(pg_name):
        return PackageGroup.query.filter(
            PackageGroup.name == pg_name
            ).first()

    checkP, organisation_code, organisation_name = get_checkp_code_name()

    data = unicodecsv.DictReader(fh)

    for row in data:
        condition = checkCondition(row)
        organisation = get_organisation(checkP)

        def add_org_package(package):
            addOrganisationPackage({
                    "organisation_id" : organisation.id,
                    "package_id" : package.id,
                    "condition": condition
                    })
            
        def add_org_packagegroup(packagegroup):
            addOrganisationPackageGroup({
                    "organisation_id" : organisation.id,
                    "packagegroup_id" : packagegroup.id,
                    "condition": condition
                    })

        def add_org_package_from_pg(packagegroup):
            data = {
                'packagegroup_id': packagegroup.id,
                'organisation_id': organisation.id,
                'condition': condition
                }
            addOrganisationPackageFromPackageGroup(data)

        print organisation_code

        for package in get_packages(organisation_code):
            add_org_package(package)

        for packagegroup in get_packagegroup(organisation_code):
            add_org_packagegroup(packagegroup)

        pg_name = row.get('packagegroup_name', "")
        if pg_name != '':
            packagegroup = get_packagegroup_by_name(pg_name)
            add_org_package_from_pg(packagegroup)
                
    print "Imported successfully"
    return True

def organisations(organisation_code=None):
    if organisation_code is None:
        return Organisation.query.all()
    else:
        return Organisation.query.filter_by(
            organisation_code=organisation_code).first()

def organisationPackages(organisation_code=None):
    if organisation_code is None:
        return False

    return db.session.query(Package,
                            OrganisationPackage
                        ).filter(
                        Organisation.organisation_code==organisation_code
                        ).join(OrganisationPackage
                        ).join(Organisation
                        ).all()

def organisationPackageGroups(organisation_code=None):
    if organisation_code is None:
        return False

    return db.session.query(PackageGroup,
                            OrganisationPackageGroup
            ).filter(Organisation.organisation_code==organisation_code
            ).join(OrganisationPackageGroup
            ).join(Organisation
            ).all()

def addOrganisation(data):
    organisation_code = data["organisation_code"]
    checkP = Organisation.query.filter_by(
        organisation_code=organisation_code).first()

    if checkP:
        return False

    newP = Organisation()
    newP.setup(
        organisation_name = data["organisation_name"],
        organisation_code = data["organisation_code"]
        )
    db.session.add(newP)
    db.session.commit()
    return newP

def updateOrganisation(organisation_code, data):
    checkP = Organisation.query.filter_by(
        organisation_code=organisation_code).first()

    if checkP is None:
        return False

    checkP.organisation_code = data["organisation_code"]
    checkP.organisation_name = data["organisation_code"]
    db.session.add(checkP)
    db.session.commit()
    return checkP

def addOrganisationPackage(data):
    checkPP=OrganisationPackage.query.filter_by(
        organisation_id=data['organisation_id'], package_id=data['package_id']
                ).first()

    if checkPP is not None:
        return False

    newPP = OrganisationPackage()
    newPP.setup(
        organisation_id = data["organisation_id"],
        package_id = data["package_id"],
        condition = data["condition"]
        )
    db.session.add(newPP)
    db.session.commit()
    return newPP

def addOrganisationPackageGroup(data):
    checkPG = OrganisationPackageGroup.query.filter_by(
        organisation_id=data['organisation_id'], 
        packagegroup_id=data['packagegroup_id']
                ).first()

    if checkPG is not None:
        # Confirm that it's already been added
        return checkPG

    newPG = OrganisationPackageGroup()
    newPG.setup(
        organisation_id = data["organisation_id"],
        packagegroup_id = data["packagegroup_id"],
        condition = data["condition"]
        )
    db.session.add(newPG)
    db.session.commit()
    return newPG

def addOrganisationPackageFromPackageGroup(data):
    packages = Package.query.filter_by(
        package_group=data['packagegroup_id']
        ).all()
    count_packages = 0

    for package in packages:
        packagedata = {
            'organisation_id': data['organisation_id'],
            'package_id': package.id,
            'condition': data["condition"]
        }
        if addOrganisationPackage(packagedata):
            count_packages+=1

    if count_packages >0:
        return count_packages
    else:
        return False

def deleteOrganisationPackage(organisation_code, package_name, 
                              organisationpackage_id):

    checkPP = OrganisationPackage.query.filter_by(
        id=organisationpackage_id).first()

    if not checkPP:
        return False

    db.session.delete(checkPP)
    db.session.commit()
    return checkPP

def addFeedback(data):
    checkF=OrganisationConditionFeedback.query.filter_by(
        uses=data["uses"], element=data["element"], where=data["where"]
        ).first()

    if checkF:
        return False

    feedback = OrganisationConditionFeedback()
    feedback.organisation_id=data["organisation_id"]
    feedback.uses=data["uses"]
    feedback.element=data["element"]
    feedback.where=data["where"]
    db.session.add(feedback)
    db.session.commit()
    return feedback

def _organisation_detail_ungrouped(organisation):
    return db.session.query(Indicator,
                                     Test,
                                     AggregateResult.results_data,
                                     AggregateResult.results_num,
                                     AggregateResult.result_hierarchy,
                                     AggregateResult.package_id,
                                     func.max(AggregateResult.runtime_id)
        ).filter(Organisation.id==organisation.id)

def _organisation_detail(organisation):
    aggregate_results = _organisation_detail_ungrouped(organisation)\
        .group_by(Indicator,
                   AggregateResult.result_hierarchy, 
                   Test, 
                   AggregateResult.package_id,
                   AggregateResult.results_data,
                   AggregateResult.results_num
        ).join(IndicatorTest
        ).join(Test
        ).join(AggregateResult
        ).join(Package
        ).join(OrganisationPackage
        ).join(Organisation
        ).all()

    pconditions = OrganisationCondition.query.filter_by(organisation_id=organisation.id
            ).all()

    db.session.commit()
    return summary.agr_results(aggregate_results, 
                                   conditions=pconditions, 
                                   mode="publisher")

def _organisation_indicators(organisation, aggregation_type=2):
    aggregate_results = db.session.query(Indicator,
                                     Test,
                                     AggregateResult.results_data,
                                     AggregateResult.results_num,
                                     AggregateResult.result_hierarchy,
                                     AggregateResult.package_id,
                                     func.max(AggregateResult.runtime_id)
        ).filter(Organisation.organisation_code==organisation.organisation_code
        ).filter(AggregateResult.aggregateresulttype_id == aggregation_type
        ).filter(AggregateResult.organisation_id == organisation.id
        ).group_by(AggregateResult.result_hierarchy, 
                   Test, 
                   AggregateResult.package_id,
                   Indicator,
                   AggregateResult.results_data,
                   AggregateResult.results_num,
                   AggregateResult.package_id
        ).join(IndicatorTest
        ).join(Test
        ).join(AggregateResult
        ).join(Package
        ).join(OrganisationPackage
        ).join(Organisation
        ).all()

    pconditions = OrganisationCondition.query.filter_by(organisation_id=organisation.id
            ).all()

    return summary.agr_results(aggregate_results, 
                                                conditions=pconditions, 
                                                mode="publisher_indicators")

def _organisation_indicators_split(organisation, aggregation_type=2):
    results = _organisation_indicators(organisation, aggregation_type)

    zero = lambda kv: not kv[1]["results_pct"]
    non_zero = lambda kv: kv[1]["results_pct"]

    zero_results = dict(filter(zero, results.iteritems()))
    non_zero_results = dict(filter(non_zero, results.iteritems()))

    return { "zero": zero_results,
             "non_zero": non_zero_results }

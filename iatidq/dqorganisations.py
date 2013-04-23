
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

import models
import csv
import util
import unicodecsv

def checkCondition(row):
    if (('packagegroup_condition' in row) and (row['packagegroup_condition']!='')):
        return row['packagegroup_condition']
    else:
        return None

def importOrganisationPackagesFromFile(filename, organisation_c=None, organisation_n=None):
    with file(filename) as fh:
        return _importOrganisationPackages(organisation_c, organisation_n, fh, True)

def _importOrganisationPackages(organisation_c, organisation_n, fh, local):

        data = unicodecsv.DictReader(fh)

        for row in data:
            condition = checkCondition(row)

            if organisation_c is None:
                checkP = organisations(row['organisation_code'])
                organisation_code = row['organisation_code']
                organisation_name = row['organisation_name']
            else:
                checkP = organisations(organisation_c)
                organisation_code = organisation_c
                organisation_name = organisation_n
            if checkP:
                organisation = checkP
            else:
                organisation = addOrganisation({"organisation_name": organisation_name,
                                          "organisation_code": organisation_code
                                        })
            print organisation_code
            packages = models.Package.query.filter(models.PackageGroup.publisher_iati_id==organisation_code
                        ).join(models.PackageGroup
                        ).all()

            if not packages:
                continue
            else:
                for package in packages:
                    organisationpackage = addOrganisationPackage({
                                "organisation_id" : organisation.id,
                                "package_id" : package.id,
                                "condition": condition
                            })
                
        print "Imported successfully"
        return True

def organisations(organisation_code=None):
    if organisation_code is None:
        organisations = models.Organisation.query.all()
    else:
        organisations = models.Organisation.query.filter_by(organisation_code=organisation_code).first()
    return organisations

def organisationPackages(organisation_code=None):
    if organisation_code is not None:
        organisationpackages = db.session.query(models.Package,
                                             models.OrganisationPackage
                        ).filter(models.Organisation.organisation_code==organisation_code
                        ).join(models.OrganisationPackage
                        ).join(models.Organisation
                        ).all()
        return organisationpackages
    else:
        return False

def addOrganisation(data):
    checkP = models.Organisation.query.filter_by(organisation_code=data["organisation_code"]).first()
    if not checkP:
        newP = models.Organisation()
        newP.setup(
            organisation_name = data["organisation_name"],
            organisation_code = data["organisation_code"]
        )
        db.session.add(newP)
        db.session.commit()
        return newP
    else:
        return False

def updateOrganisation(organisation_code, data):
    checkP = models.Organisation.query.filter_by(organisation_code=organisation_code).first()
    if (checkP is not None):
        checkP.organisation_code = data["organisation_code"]
        checkP.organisation_name = data["organisation_code"]
        db.session.add(checkP)
        db.session.commit()
        return checkP
    else:
        return False

def addOrganisationPackage(data):
    checkPP=models.OrganisationPackage.query.filter_by(organisation_id=data['organisation_id'], package_id=data['package_id']
                ).first()
    if (checkPP is None):
        newPP = models.OrganisationPackage()
        newPP.setup(
            organisation_id = data["organisation_id"],
            package_id = data["package_id"],
            condition = data["condition"]
        )
        db.session.add(newPP)
        db.session.commit()
        return newPP
    else:
        return False

def addOrganisationPackageGroup(data):
    checkPG=models.OrganisationPackageGroup.query.filter_by(organisation_id=data['organisation_id'], packagegroup_id=data['packagegroup_id']
                ).first()
    if (checkPG is None):
        newPG = models.OrganisationPackageGroup()
        newPG.setup(
            organisation_id = data["organisation_id"],
            packagegroup_id = data["packagegroup_id"],
            condition = data["condition"]
        )
        db.session.add(newPG)
        db.session.commit()
        return newPG
    else:
        # Confirm that it's already been added
        return checkPG

def addOrganisationPackageFromPackageGroup(data):
    packages = models.Package.query.filter_by(package_group=data['packagegroup_id']
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

def deleteOrganisationPackage(organisation_code, package_name, organisationpackage_id):
    checkPP = models.OrganisationPackage.query.filter_by(id=organisationpackage_id).first()
    if checkPP:
        db.session.delete(checkPP)
        db.session.commit()
        return checkPP
    else:
        return False

def addFeedback(data):
    checkF=models.OrganisationConditionFeedback.query.filter_by(uses=data["uses"], element=data["element"], where=data["where"]
            ).first()
    if not checkF:
        feedback = models.OrganisationConditionFeedback()
        feedback.organisation_id=data["organisation_id"]
        feedback.uses=data["uses"]
        feedback.element=data["element"]
        feedback.where=data["where"]
        db.session.add(feedback)
        db.session.commit()
        return feedback
    else:
        return False

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
    return aggregation.agr_results(aggregate_results, 
                                   conditions=pconditions, 
                                   mode="publisher")

def _organisation_indicators(organisation, aggregation_type=None):
    aggregate_results = db.session.query(Indicator,
                                     Test,
                                     AggregateResult.results_data,
                                     AggregateResult.results_num,
                                     AggregateResult.result_hierarchy,
                                     AggregateResult.package_id,
                                     func.max(AggregateResult.runtime_id)
        ).filter(Organisation.organisation_code==organisation.organisation_code
        ).filter(AggregateResult.aggregateresulttype_id == aggregation_type
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

    return aggregation.agr_results(aggregate_results, 
                                                conditions=pconditions, 
                                                mode="publisher_indicators")


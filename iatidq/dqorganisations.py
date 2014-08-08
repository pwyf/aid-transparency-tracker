
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db, app

from sqlalchemy import func

import summary

from models import *
import csv
import util
import unicodecsv
import dqindicators
import dqpackages
import urllib2
import datetime
import json

def update_model(src, dst, keys):
    for key in keys:
        setattr(dst, key, getattr(dst, key))

def checkCondition(row):
    pg_cond = row.get('packagegroup_condition', '')
    if pg_cond != '':
        return pg_cond
    return None

def checkNum(value):
    try:
        return float(value)
    except Exception:
        return None

def importOrganisationPackagesFromFile(filename):
    with file(filename) as fh:
        return _importOrganisationPackages(fh, True)

def _importOrganisationPackages(fh, local):
    def get_check_org(row):
        checkOrg = organisations(row['organisation_code'])
        if checkOrg:
            return checkOrg
        else:
            return None

    def get_organisation(checkOrg, row):
        if checkOrg:
            return checkOrg
        return addOrganisation(
            {"organisation_name": row["organisation_name"],
             "organisation_code": row["organisation_code"],
             "organisation_total_spend": row["organisation_total_spend"],
             "organisation_total_spend_source": row["organisation_total_spend_source"],
             "organisation_currency": row["organisation_currency"],
             "organisation_currency_conversion": row["organisation_currency_conversion"],
             "organisation_currency_conversion_source": row["organisation_currency_conversion_source"],
             "organisation_largest_recipient": row["organisation_largest_recipient"],
             "organisation_largest_recipient_source": row["organisation_largest_recipient_source"]
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

    data = unicodecsv.DictReader(fh)

    for row in data:

        checkOrg = get_check_org(row)

        condition = checkCondition(row)
        organisation = get_organisation(checkOrg, row)
        organisation_code = organisation.organisation_code

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
            if packagegroup is not None:
                add_org_package_from_pg(packagegroup)
                add_org_packagegroup(packagegroup)
                
    print "Imported successfully"
    return True

def downloadOrganisationFrequency():
    fh = urllib2.urlopen(app.config["ORG_FREQUENCY_API_URL"])
    return _updateOrganisationFrequency(fh)

"""def downloadOrganisationFrequencyFromFile():
    filename = 'tests/iati_registry_updater_frequency_check.csv'
    with file(filename) as fh:
        return _updateOrganisationFrequency(fh)"""

def _updateOrganisationFrequency(fh):

    def get_frequency():
        d = fh.read()
        packagegroups = json.loads(d)["data"]
        
        for packagegroup in packagegroups:
            freq = packagegroup["frequency_code"]

            if freq==1:
                frequency = "monthly"
                comment = packagegroup["frequency_comment"]
            elif freq ==2:
                frequency = "quarterly"
                comment = packagegroup["frequency_comment"]
            else:
                frequency = "less than quarterly"
                comment = packagegroup["frequency_comment"]
            yield packagegroup["publisher"], frequency, comment

    for packagegroup, frequency, comment in get_frequency():
        organisations = dqpackages.packageGroupOrganisations(packagegroup)
        if not organisations:
            continue
        for organisation in organisations:
            with db.session.begin():
                organisation.frequency=frequency
                organisation.frequency_comment=comment
                db.session.add(organisation)

def organisations(organisation_code=None):
    if organisation_code is None:
        return Organisation.query.order_by(Organisation.organisation_name
            ).all()
    else:
        return Organisation.query.filter_by(
            organisation_code=organisation_code).first()

def organisation_by_id(organisation_id):
    return Organisation.query.filter_by(
        id=organisation_id).first()

def organisationid_by_code(organisation_code):
    assert organisation_code

    org = Organisation.query.filter_by(organisation_code=organisation_code).first()
    assert org
    return org.id

def organisation_by_code(organisation_code):
    assert organisation_code

    org = Organisation.query.filter_by(organisation_code=organisation_code).first()
    assert org
    return org

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

    with db.session.begin():
        newP = Organisation()
        newP.setup(
            organisation_name = data["organisation_name"],
            organisation_code = data["organisation_code"],
            organisation_total_spend = checkNum(data["organisation_total_spend"]),
            organisation_total_spend_source = data["organisation_total_spend_source"],
            organisation_currency = data["organisation_currency"],
            organisation_currency_conversion = checkNum(data["organisation_currency_conversion"]),
            organisation_currency_conversion_source = data["organisation_currency_conversion_source"],
            organisation_largest_recipient = data["organisation_largest_recipient"],
            organisation_largest_recipient_source = data["organisation_largest_recipient_source"]
            )
    #    update_model(data, newP, ["organisation_name", "organisation_code"])
        db.session.add(newP)
    return newP

def updateOrganisation(organisation_code, data):
    checkP = Organisation.query.filter_by(
        organisation_code=organisation_code).first()

    if checkP is None:
        return False
    with db.session.begin():
        checkP.organisation_code = data["organisation_code"]
        checkP.organisation_name = data["organisation_name"]
        checkP.no_independent_reviewer = data["no_independent_reviewer"]
        checkP.organisation_responded = data["organisation_responded"]
        db.session.add(checkP)
    return checkP

def addOrganisationPackage(data):
    checkPP=OrganisationPackage.query.filter_by(
        organisation_id=data['organisation_id'], package_id=data['package_id']
                ).first()

    if checkPP is not None:
        return False
    
    with db.session.begin():
        newPP = OrganisationPackage()
        newPP.setup(
            organisation_id = data["organisation_id"],
            package_id = data["package_id"],
            condition = data["condition"]
            )
        db.session.add(newPP)
    return newPP

def addOrganisationPackageGroup(data):
    checkPG = OrganisationPackageGroup.query.filter_by(
        organisation_id=data['organisation_id'], 
        packagegroup_id=data['packagegroup_id']
                ).first()

    if checkPG is not None:
        # Confirm that it's already been added
        return checkPG

    with db.session.begin():
        newPG = OrganisationPackageGroup()
        newPG.setup(
            organisation_id = data["organisation_id"],
            packagegroup_id = data["packagegroup_id"],
            condition = data["condition"]
            )
        db.session.add(newPG)
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

    with db.session.begin():
        db.session.delete(checkPP)

    return checkPP

def addFeedback(data):
    checkF=OrganisationConditionFeedback.query.filter_by(
        uses=data["uses"], element=data["element"], where=data["where"]
        ).first()

    if checkF:
        return False

    with db.session.begin():
        feedback = OrganisationConditionFeedback()
        feedback.organisation_id=data["organisation_id"]
        feedback.uses=data["uses"]
        feedback.element=data["element"]
        feedback.where=data["where"]
        db.session.add(feedback)

    return feedback


def make_publisher_summary(organisation, aggregation_type):
    s = summary.PublisherSummaryCreator(organisation, aggregation_type)
    return s.summary.summary() ## FIXME

def info_result_tuple(ir):
    ind = {
        'description': ir.Indicator.description,
        'name': ir.Indicator.name,
        'id': ir.Indicator.id,
        'indicatorgroup_id': ir.Indicator.indicatorgroup_id,
        'indicator_type': ir.Indicator.indicator_type,
        'indicator_category_name': ir.Indicator.indicator_category_name,
        'indicator_subcategory_name': ir.Indicator.indicator_subcategory_name,
        'longdescription': ir.Indicator.longdescription,
        'indicator_noformat': ir.Indicator.indicator_noformat,
        'indicator_ordinal': ir.Indicator.indicator_ordinal,
        'indicator_order': ir.Indicator.indicator_order,
        'indicator_weight': ir.Indicator.indicator_weight
        }

    return (ir.Indicator.id, 
            {
            'results_num': 1,
            'results_pct': ir.InfoResult.result_data,
            'indicator': ind,
            'tests': [
                {'test': {
                        'id': 'infotype-' + str(ir.InfoType.id),
                        'name': ir.InfoType.name, 
                        'description': ir.InfoType.description
                        }, 
                 'results_pct': ir.InfoResult.result_data, 
                 'results_num': 1}
                ]
            })

def _organisation_indicators(organisation, aggregation_type=2):
    s = summary.PublisherIndicatorsSummaryCreator(organisation,
                                                  aggregation_type)
    data = s.summary.summary()  ## FIXME
    
    # Sorry, this is really crude
    inforesults = _organisation_indicators_inforesults(organisation)
    data.update([ info_result_tuple(ir) for ir in inforesults ])

    # make sure indicators are complete
    indicators = dqindicators.indicators_subset(app.config["INDICATOR_GROUP"], u"publication")
    for indc in indicators:
        if indc.id in data:
            continue
        data[indc.id] = {
            'results_num': 0,
            'results_pct': 0,
            'indicator': {
                'description': indc.description,
                'name': indc.name,
                'id': indc.id,
                'indicatorgroup_id': indc.indicatorgroup_id,
                'indicator_type': indc.indicator_type,
                'indicator_category_name': indc.indicator_category_name,
                'indicator_subcategory_name': indc.indicator_subcategory_name,
                'longdescription': indc.longdescription,
                'indicator_noformat': indc.indicator_noformat,
                'indicator_ordinal': indc.indicator_ordinal,
                'indicator_order': indc.indicator_order,
                'indicator_weight': indc.indicator_weight
                },
            'tests': {}
            }
    return data

def _organisation_indicators_inforesults(organisation):
    # Get InfoResults that can be joined to an Indicator
    #  -- if they can't be joined to an indicator then
    #     the results just contain coverage data.

    inforesult_data = db.session.query(InfoResult,
                                     Indicator,
                                     InfoType
        ).filter(InfoResult.organisation_id==organisation.id
        ).filter(OrganisationPackage.organisation_id==organisation.id
        ).join(InfoType
        ).join(IndicatorInfoType
        ).join(Indicator
        ).join(Package
        ).join(OrganisationPackage
        ).group_by(InfoResult,  
                   Indicator,
                   InfoType                   
        ).all()
    return inforesult_data

def _organisation_indicators_complete_split(organisation, aggregation_type=2):
    results = _organisation_indicators(organisation, aggregation_type)
    
    commitment_data = dqindicators.indicators_subset(app.config["INDICATOR_GROUP"], 
                                                     u"commitment")
    commitment_results = dict(map(lambda x: (x.id, {'indicator': x }), commitment_data))

    publication_organisation = lambda kv: (kv[1]["indicator"]["indicator_category_name"]=="organisation")
    publication_activity = lambda kv: (kv[1]["indicator"]["indicator_category_name"]=="activity")
    publication_organisation_results = dict(filter(publication_organisation, results.iteritems()))
    publication_activity_results = dict(filter(publication_activity, results.iteritems()))

    return { "publication_activity": publication_activity_results,
             "publication_organisation": publication_organisation_results,
             "commitment": commitment_results}

def _organisation_indicators_split(organisation, aggregation_type=2):
    results = _organisation_indicators(organisation, aggregation_type)
    
    commitment_data = dqindicators.indicators_subset(app.config["INDICATOR_GROUP"], 
                                                     u"commitment")
    commitment = dict(map(lambda x: (x.id, {'indicator': x }), commitment_data))
    if not results:
        indicators = dqindicators.indicators(app.config["INDICATOR_GROUP"])
        indicators_restructured = dict(map(lambda x: (x.id, {'indicator': {'name': x.name } }), indicators))
        return {"zero": indicators_restructured,
                "non_zero": {},
                "commitment": commitment}

    zero = lambda kv: not kv[1]["results_pct"]
    non_zero = lambda kv: kv[1]["results_pct"]

    zero_results = dict(filter(zero, results.iteritems()))
    non_zero_results = dict(filter(non_zero, results.iteritems()))

    return { "zero": zero_results,
             "non_zero": non_zero_results,
             "commitment": commitment}

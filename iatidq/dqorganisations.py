
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
import dqindicators
import dqpackages
import urllib2
import datetime

ORG_FREQUENCY_API_URL = "https://api.scraperwiki.com/api/1.0/datastore/sqlite?format=csv&name=iati_registry_updater_frequency_check&query=select+*+from+%60packagegroups_dates_data%60&apikey="

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
                
    print "Imported successfully"
    return True

def downloadOrganisationFrequency():
    fh = urllib2.urlopen(ORG_FREQUENCY_API_URL)
    return _updateOrganisationFrequency(fh)

def downloadOrganisationFrequencyFromFile():
    filename = 'tests/iati_registry_updater_frequency_check.csv'
    with file(filename) as fh:
        return _updateOrganisationFrequency(fh)

def _updateOrganisationFrequency(fh):
    def check_data_last_four_months(packagegroup_name, packagegroups):
        fourmonths_ago = (datetime.datetime.utcnow()-datetime.timedelta(days=4*30)).date()
        lastfourmonth_dates = filter(lambda d: d>fourmonths_ago, packagegroups[packagegroup_name])
        return len(lastfourmonth_dates)

    def check_data_avg_months_to_publication(packagegroup_name, packagegroups):
        earliest_date = min(packagegroups[packagegroup_name])
        earliest_date_days_ago=(datetime.datetime.utcnow().date()-earliest_date).days
        number_months_changes = len(packagegroups[packagegroup_name])
        avg_days_per_change = earliest_date_days_ago/number_months_changes
        return avg_days_per_change

    def generate_data():
        data = unicodecsv.DictReader(fh)
        packagegroups = {}
        for row in data:
            try:
                packagegroups[row['packagegroup_name']].append((datetime.date(year=int(row['year']), month=int(row['month']), day=1)))
            except KeyError:
                packagegroups[row['packagegroup_name']] = []
                packagegroups[row['packagegroup_name']].append((datetime.date(year=int(row['year']), month=int(row['month']), day=1)))
        return packagegroups

    def get_frequency():
        packagegroups = generate_data()
        for packagegroup in sorted(packagegroups.keys()):
            lastfour = check_data_last_four_months(packagegroup, packagegroups)
            avgmonths = check_data_avg_months_to_publication(packagegroup, packagegroups)
            if lastfour >=3:
                frequency = "monthly"
                comment = "Updated " + str(lastfour) + " times in the last 4 months"
            elif avgmonths<31:
                frequency = "monthly"
                comment = "Updated on average every " + str(avgmonths) + " days"
            elif avgmonths<93:
                frequency = "quarterly"
                comment = "Updated on average every " + str(avgmonths) + " days"
            else:
                frequency = "less than quarterly"
                comment = "Updated on average every " + str(avgmonths) + " days"
            yield packagegroup, frequency, comment

    for packagegroup, frequency, comment in get_frequency():
        organisations = dqpackages.packageGroupOrganisations(packagegroup)
        if not organisations:
            continue
        for organisation in organisations:
            organisation.frequency=frequency
            organisation.frequency_comment=comment
            db.session.add(organisation)
            db.session.commit()

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


def _organisation_detail_ungrouped(organisation, aggregation_type):
    return db.session.query(Indicator,
                                     Test,
                                     AggregateResult.results_data,
                                     AggregateResult.results_num,
                                     AggregateResult.result_hierarchy,
                                     AggregateResult.package_id,
                                     func.max(AggregateResult.runtime_id)
        ).filter(Organisation.id==organisation.id
        ).filter(AggregateResult.aggregateresulttype_id == aggregation_type)

def _organisation_detail(organisation, aggregation_type):
    aggregate_results = _organisation_detail_ungrouped(organisation, aggregation_type)\
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
        ).order_by(Indicator.indicator_type, 
                   Indicator.indicator_category_name, 
                   Indicator.indicator_subcategory_name
        ).all()

    pconditions = OrganisationCondition.query.filter_by(organisation_id=organisation.id
            ).all()

    data = summary.agr_results(aggregate_results, 
                                                conditions=pconditions, 
                                                mode="publisher_indicators")
    
    # Sorry, this is really crude
    inforesults = _organisation_indicators_inforesults(organisation)
    for inforesult in inforesults:
        try:
            data[inforesult.Indicator.id]
        except KeyError:
            data[inforesult.Indicator.id]={}
        data[inforesult.Indicator.id]={
            'results_num': 1,
            'results_pct': inforesult.result_data,
            'indicator': {
                'description': inforesult.Indicator.description,
                'name': inforesult.Indicator.name,
                'id': inforesult.Indicator.id,
                'indicatorgroup_id': inforesult.Indicator.indicatorgroup_id,
                'indicator_type': inforesult.Indicator.indicator_type,
                'indicator_category_name': inforesult.Indicator.indicator_category_name,
                'indicator_subcategory_name': inforesult.Indicator.indicator_subcategory_name,
                'longdescription': inforesult.Indicator.longdescription,
                'indicator_noformat': inforesult.Indicator.indicator_noformat,
                'indicator_ordinal': inforesult.Indicator.indicator_ordinal
            },
            'tests': {}
        }
    # make sure indicators are complete
    indicators = dqindicators.indicators_subset("pwyf2013", "publication")
    for indicator in indicators:
        if indicator.id not in data:
            data[indicator.id] = {
            'results_num': 0,
            'results_pct': 0,
            'indicator': {
                'description': indicator.description,
                'name': indicator.name,
                'id': indicator.id,
                'indicatorgroup_id': indicator.indicatorgroup_id,
                'indicator_type': indicator.indicator_type,
                'indicator_category_name': indicator.indicator_category_name,
                'indicator_subcategory_name': indicator.indicator_subcategory_name,
                'longdescription': indicator.longdescription,
                'indicator_noformat': indicator.indicator_noformat,
                'indicator_ordinal': indicator.indicator_ordinal
            },
            'tests': {}
        }
    
    return data

def _organisation_indicators_inforesults(organisation):
    inforesult_data = db.session.query(Indicator,
                                     InfoType,
                                     InfoResult.package_id,
                                     InfoResult.result_data,
                                     func.max(InfoResult.runtime_id)
        ).filter(InfoResult.organisation_id==organisation.id
        ).join(IndicatorInfoType
        ).join(InfoType
        ).join(InfoResult
        ).group_by(Indicator,
                   InfoType,
                   InfoResult.result_data,
                   InfoResult.package_id,
                   InfoType.id
        ).all()
    return inforesult_data

def _organisation_indicators_split(organisation, aggregation_type=2):
    results = _organisation_indicators(organisation, aggregation_type)
    
    commitment_data = dqindicators.indicators_subset("pwyf2013", "commitment")
    commitment = dict(map(lambda x: (x.id, {'indicator': x }), commitment_data))
    if not results:
        indicators = dqindicators.indicators("pwyf2013")
        indicators_restructured = dict(map(lambda x: (x.id, {'indicator': x }), indicators))
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

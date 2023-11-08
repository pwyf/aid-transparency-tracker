
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import urllib.request, urllib.error, urllib.parse

import csv
import codecs

from iatidataquality import app, db
from . import dqindicators, models, summary


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
    with open(filename) as fh:
        return _importOrganisationPackages(fh, True)


def _importOrganisationPackages(fh, local):
    def get_or_create_organisation(row):
        organisation = models.Organisation.where(
            organisation_code=row['organisation_code']).first()
        if not organisation:
            organisation = addOrganisation(row)
        return organisation

    def get_packages(organisation_code):
        return models.Package.query.filter(
            models.PackageGroup.publisher_iati_id==organisation_code
            ).join(models.PackageGroup).all()

    def get_packagegroup(organisation_code):
        return models.PackageGroup.query.filter(
            models.PackageGroup.publisher_iati_id==organisation_code
            ).all()

    def get_packagegroup_by_name(pg_name):
        return models.PackageGroup.query.filter(
            models.PackageGroup.name == pg_name
            ).first()

    data = csv.DictReader(fh)

    for row in data:
        condition = checkCondition(row)
        organisation = get_or_create_organisation(row)
        organisation_code = organisation.organisation_code

        def add_org_package(package):
            addOrganisationPackage({
                    "organisation_id": organisation.id,
                    "package_id": package.id,
                    "condition": condition
                    })

        def add_org_packagegroup(packagegroup):
            addOrganisationPackageGroup({
                    "organisation_id": organisation.id,
                    "packagegroup_id": packagegroup.id,
                    "condition": condition
                    })

        def add_org_package_from_pg(packagegroup):
            data = {
                'packagegroup_id': packagegroup.id,
                'organisation_id': organisation.id,
                'condition': condition
                }
            addOrganisationPackageFromPackageGroup(data)

        print(organisation_code)

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

    print("Imported successfully")
    return True


def downloadOrganisationFrequency():
    fh = urllib.request.urlopen(app.config["ORG_FREQUENCY_API_URL"])

    timelag_fh = urllib.request.urlopen(app.config["ORG_FREQUENCY_API_URL"].replace("_frequency", "_timelag"))
    timelag_dict = {}

    rows = csv.DictReader(codecs.iterdecode(timelag_fh, 'utf-8'))

    for row in rows:
        timelag_in_csv = row["Time lag"]

        if timelag_in_csv == "One month":
            timelag = "one month"
        elif timelag_in_csv == "A quarter":
            timelag = "a quarter"
        else:
            timelag = "more than a quarter"
        timelag_dict[row["Publisher Registry Id"]] = timelag

    def get_frequency():
        rows = csv.DictReader(codecs.iterdecode(fh, 'utf-8'))

        for row in rows:
            freq = row["Frequency"]

            if freq == "Monthly":
                frequency = "monthly"
            elif freq == "Quarterly":
                frequency = "quarterly"
            else:
                frequency = "less than quarterly"
            yield row["Publisher Registry Id"], frequency

    for packagegroup, frequency in get_frequency():
        organisations = (
            models.Organisation.where(registry_slug=packagegroup).all())
        if not organisations:
            continue
        for organisation in organisations:
            with db.session.begin():
                if organisation.frequency != frequency:
                    timelag = timelag_dict.get(packagegroup)
                    print(('{}: Updated {}, with time lag {} (previously: Updated {}, with time lag {})'.format(
                        organisation.organisation_name,
                        frequency,
                        timelag,
                        organisation.frequency,
                        organisation.timelag
                    )))
                    organisation.frequency = frequency
                    organisation.timelag = timelag
                    db.session.add(organisation)


def organisationPackages(organisation_code=None):
    if organisation_code is None:
        return False

    return db.session.query(models.Package,
                            models.OrganisationPackage
                            ).filter(
                                models.Organisation.organisation_code==organisation_code
                            ).join(
                                models.OrganisationPackage
                            ).join(
                                models.Organisation
                            ).all()


def organisationPackageGroups(organisation_code=None):
    if organisation_code is None:
        return False

    return db.session.query(
        models.PackageGroup, models.OrganisationPackageGroup
    ).filter(
        models.Organisation.organisation_code==organisation_code
    ).join(
        models.OrganisationPackageGroup
    ).join(
        models.Organisation
    ).all()


def addOrganisation(data):
    organisation_code = data["organisation_code"]
    checkP = models.Organisation.query.filter_by(
        organisation_code=organisation_code).first()

    if checkP:
        return False

    with db.session.begin():
        newP = models.Organisation()
        newP.setup(
            organisation_name=data["organisation_name"],
            registry_slug=data["packagegroup_name"],
            organisation_code=data["organisation_code"],
            organisation_total_spend=0,
            organisation_currency_conversion=1,
            condition=data.get('packagegroup_condition'),
            self_ref=data.get('self_ref'),
        )
        db.session.add(newP)
    return newP


def updateOrganisation(organisation_code, data):
    checkP = models.Organisation.query.filter_by(
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
    checkPP = models.OrganisationPackage.query.filter_by(
        organisation_id=data['organisation_id'], package_id=data['package_id']
                ).first()

    if checkPP is not None:
        return False

    with db.session.begin():
        newPP = models.OrganisationPackage()
        newPP.setup(
            organisation_id=data["organisation_id"],
            package_id=data["package_id"],
            condition=data["condition"]
            )
        db.session.add(newPP)
    return newPP


def addOrganisationPackageGroup(data):
    checkPG = models.OrganisationPackageGroup.query.filter_by(
        organisation_id=data['organisation_id'],
        packagegroup_id=data['packagegroup_id']
                ).first()

    if checkPG is not None:
        # Confirm that it's already been added
        return checkPG

    with db.session.begin():
        print("trying to add packagegroup!")
        print(data)
        newPG = models.OrganisationPackageGroup()
        newPG.setup(
            organisation_id=data["organisation_id"],
            packagegroup_id=data["packagegroup_id"],
            condition=data["condition"]
        )
        db.session.add(newPG)
    return newPG


def addOrganisationPackageFromPackageGroup(data):
    packages = models.Package.query.filter_by(
        package_group_id=data['packagegroup_id']
        ).all()
    count_packages = 0

    for package in packages:
        packagedata = {
            'organisation_id': data['organisation_id'],
            'package_id': package.id,
            'condition': data["condition"]
        }
        if addOrganisationPackage(packagedata):
            count_packages += 1

    if count_packages > 0:
        return count_packages
    else:
        return False


def deleteOrganisationPackage(organisation_code, package_name,
                              organisationpackage_id):

    checkPP = models.OrganisationPackage.query.filter_by(
        id=organisationpackage_id).first()

    if not checkPP:
        return False

    with db.session.begin():
        db.session.delete(checkPP)

    return checkPP


def addFeedback(data):
    checkF = models.OrganisationConditionFeedback.query.filter_by(
        uses=data["uses"], element=data["element"], where=data["where"]
        ).first()

    if checkF:
        return False

    with db.session.begin():
        feedback = models.OrganisationConditionFeedback()
        feedback.organisation_id = data["organisation_id"]
        feedback.uses = data["uses"]
        feedback.element = data["element"]
        feedback.where = data["where"]
        db.session.add(feedback)

    return feedback


def make_publisher_summary(organisation, aggregation_type):
    s = summary.PublisherSummaryCreator(organisation, aggregation_type)
    return s.summary.summary()  # FIXME


def info_result_tuple(ir):
    ind = {
        'description': ir.Indicator.description,
        'name': ir.Indicator.name,
        'id': ir.Indicator.id,
        'indicatorgroup_id': ir.Indicator.indicatorgroup_id,
        'indicator_type': ir.Indicator.indicator_type,
        'indicator_category_name': ir.Indicator.indicator_category_name,
        'indicator_subcategory_name': ir.Indicator.indicator_subcategory_name_text,
        'indicator_category_name_text': ir.Indicator.indicator_category_name_text,
        'indicator_subcategory_name_text': ir.Indicator.indicator_subcategory_name_text,
        'longdescription': ir.Indicator.longdescription,
        'indicator_noformat': ir.Indicator.indicator_noformat,
        'indicator_ordinal': ir.Indicator.indicator_ordinal,
        'indicator_order': ir.Indicator.indicator_order,
        'indicator_weight': ir.Indicator.indicator_weight
    }

    return (ir.Indicator.id, {
                'results_num': ir.InfoResult.result_num,
                'results_pct': ir.InfoResult.result_data,
                'indicator': ind,
                'tests': [
                    {'test': {
                            'id': 'infotype-' + str(ir.InfoType.id),
                            'name': ir.InfoType.name,
                            'description': ir.InfoType.description
                            },
                     'results_pct': ir.InfoResult.result_data,
                     'results_num': ir.InfoResult.result_num}
                ]
            })


def _organisation_indicators(organisation, aggregation_type=2):
    s = summary.PublisherIndicatorsSummaryCreator(organisation,
                                                  aggregation_type)
    data = s.summary.summary()  # FIXME

    # Sorry, this is really crude
    inforesults = _organisation_indicators_inforesults(organisation)
    data.update([info_result_tuple(ir) for ir in inforesults])

    # make sure indicators are complete
    indicators = dqindicators.indicators_subset(app.config["INDICATOR_GROUP"], "publication")
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
                'indicator_category_name_text': indc.indicator_category_name_text,
                'indicator_subcategory_name_text': indc.indicator_subcategory_name_text,
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

    inforesult_data = db.session.query(
        models.InfoResult, models.Indicator, models.InfoType
    ).filter(
        models.InfoResult.organisation_id==organisation.id
    ).filter(
        models.OrganisationPackage.organisation_id==organisation.id
    ).join(
        models.InfoType
    ).join(
        models.IndicatorInfoType
    ).join(
        models.Indicator
    ).join(
        models.Package
    ).join(
        models.OrganisationPackage
    ).group_by(
        models.InfoResult, models.Indicator, models.InfoType
    ).all()
    return inforesult_data


def _organisation_indicators_complete_split(organisation, aggregation_type=2):
    results = _organisation_indicators(organisation, aggregation_type)

    commitment_data = dqindicators.indicators_subset(app.config["INDICATOR_GROUP"],
                                                     "commitment")
    commitment_results = dict([(x.id, {'indicator': x.as_dict() }) for x in commitment_data])

    publication_organisation = lambda kv: (kv[1]["indicator"]["indicator_category_name"]=="organisation")
    publication_activity = lambda kv: (kv[1]["indicator"]["indicator_category_name"]=="activity")
    publication_organisation_results = dict(list(filter(publication_organisation, iter(results.items()))))
    publication_activity_results = dict(list(filter(publication_activity, iter(results.items()))))

    return {"publication_activity": publication_activity_results,
            "publication_organisation": publication_organisation_results,
            "commitment": commitment_results}


def _organisation_indicators_split(organisation, aggregation_type=2):
    results = _organisation_indicators(organisation, aggregation_type)
    commitment_data = dqindicators.indicators_subset(
                    app.config["INDICATOR_GROUP"],
                    "commitment")
    commitment = dict([(x.id, {'indicator': x.as_dict() }) for x in commitment_data])
    if not results:
        indicators = dqindicators.indicators(app.config["INDICATOR_GROUP"])
        indicators_restructured = dict([(x.id, {
            'indicator': {
                'name': x.name,
                'indicator_subcategory_name': x.indicator_subcategory_name,
            }
        }) for x in indicators])
        return {"zero": indicators_restructured,
                "non_zero": {},
                "commitment": commitment}

    zero_results = dict([kv for kv in iter(results.items()) if not kv[1]["results_pct"]])
    non_zero_results = dict([kv for kv in iter(results.items()) if kv[1]["results_pct"]])

    return {"zero": zero_results,
            "non_zero": non_zero_results,
            "commitment": commitment}


def get_ordinal_values_years():
    return {
        3: {
            'text': '3 years ahead',
            'class': 'success',
        },
        2: {
            'text': '2 years ahead',
            'class': 'warning',
        },
        1: {
            'text': '1 year ahead',
            'class': 'danger',
        },
        0: {
            'text': 'No forward data',
            'class': 'inverse',
        },
        -1: {
            'text': 'Unknown',
            'class': '',
        },
    }

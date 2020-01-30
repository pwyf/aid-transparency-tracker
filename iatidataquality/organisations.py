
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import json
import operator

from flask import abort, render_template, flash, request, redirect, url_for, send_file
from flask_login import current_user

from . import app, db, surveys, usermanagement
from iatidq import donorresponse, dqorganisations, dqpackages, dqaggregationtypes, dqindicators, util
from iatidq.dqcsv import make_csv
import iatidq.survey.data as dqsurveys
import iatidq.inforesult
from iatidq.models import InfoResult, Organisation
from functools import reduce


def get_info_results(org_packages, organisation):
    for _, p in org_packages:
        package_id = p.package_id
        runtime = db.session.query(
            db.func.max(InfoResult.runtime_id)).filter(
            InfoResult.package_id == package_id
            ).first()
        runtime, = runtime
        results = iatidq.inforesult.info_results(
            package_id, runtime, organisation.id)
        if "coverage" not in results:
            continue
        try:
            yield int(results["coverage_current"])
        except TypeError:
            yield 0


# FIXME: use organisation_total_spend when data is imported to db
def get_coverage(organisation, info_results):
    coverage_found = reduce(operator.add, info_results, 0)
    coverage_total = organisation.organisation_total_spend * 1000000

    if coverage_total and coverage_found:
        c = float(coverage_found) / float(coverage_total)
        coverage_pct = int(c * 100)
    else:
        coverage_pct = None
        coverage_found = None
        coverage_total = None

    return {
        'total': coverage_total,
        'found': coverage_found,
        'pct': coverage_pct
        }


def get_summary_data(organisation, aggregation_type):
    # try:
    return _organisation_indicators_summary(organisation, aggregation_type)
    # except Exception, e:
    #     return None


def organisations_coverage():
    organisations = Organisation.sort('organisation_name').all()
    coverage_data = {}

    for organisation in organisations:
        org_packages = dqorganisations.organisationPackages(organisation.organisation_code)
        irs = [ir for ir in get_info_results(org_packages, organisation)]
        coverage_data[organisation.id] = (get_coverage(organisation, irs))
    return render_template("organisations_coverage.html",
                           organisations=organisations,
                           coverage_data=coverage_data,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user)


def organisations_index(organisation_code=None):
    organisation = Organisation.where(organisation_code=organisation_code).first()
    if not organisation:
        return abort(404)

    aggregation_type = integerise(request.args.get('aggregation_type', 2))

    template_args = {}
    org_packages = dqorganisations.organisationPackages(organisation_code)

    packagegroups = dqorganisations.organisationPackageGroups(organisation_code)

    irs = [ir for ir in get_info_results(org_packages, organisation)]
    coverage = get_coverage(organisation, irs)

    organisation_survey = dqsurveys.getSurvey(organisation_code)

    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)

    surveydata, _ = dqsurveys.get_survey_data_and_workflow(
        organisation_survey, surveydata)

    summary_data = get_summary_data(organisation, aggregation_type)

    allowed_to_view_survey = usermanagement.check_perms(
        "survey",
        "view")

    allowed_to_edit_survey_researcher = usermanagement.check_perms(
        "survey_researcher",
        "edit",
        {"organisation_code": organisation_code})

    allowed_to_edit_survey_cso = usermanagement.check_perms(
        "survey_cso",
        "edit",
        {"organisation_code": organisation_code})

    show_researcher_button = (
        (allowed_to_edit_survey_researcher or allowed_to_edit_survey_cso)
        and
         (
           (organisation_survey and
           organisation_survey.Workflow.name == 'researcher') 
           or
           (organisation_survey and
           organisation_survey.Workflow.name == 'cso')
           or
          (not organisation_survey)
         )
        )
    
    survey_workflow = 'researcher' if organisation_survey is None else organisation_survey.Workflow.name

    template_args = dict(organisation=organisation,
                         summary_data=summary_data,
                         packagegroups=packagegroups,
                         coverage=coverage,
                         surveydata=surveydata,
                         admin=usermanagement.check_perms('admin'),
                         loggedinuser=current_user,
                         allowed_to_view_survey=allowed_to_view_survey,
                         show_researcher_button=show_researcher_button,
                         survey_workflow=survey_workflow)

    return render_template("organisation_index.html", **template_args)


def get_organisations(organisation_code=None):
    check_perms = usermanagement.check_perms(
        'organisation', 'view', {'organisation_code': organisation_code})

    if organisation_code is not None:
        template = {
            True: 'organisations_index',
            False: 'organisation_publication'
            }[check_perms]

        return redirect(url_for(template, organisation_code=organisation_code))

    organisations = Organisation.sort('organisation_name').all()

    template_args = {
        'organisations': organisations,
        'admin': usermanagement.check_perms('admin'),
        'loggedinuser': current_user,
        'ati_year': app.config['ATI_YEAR'],
    }
    return render_template("organisations.html", **template_args)


def organisation_new():
    organisation = None
    if request.method == 'POST':
        data = {
            'organisation_code': request.form['organisation_code'],
            'organisation_name': request.form['organisation_name']
        }
        organisation = dqorganisations.addOrganisation(data)
        if organisation:
            flash('Successfully added organisation', 'success')
            return redirect(url_for(
                    'organisation_edit',
                    organisation_code=organisation.organisation_code))

        flash("Couldn't add organisation", "danger")
        organisation = data

    return render_template("organisation_edit.html", organisation=organisation,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user,
                           donorresponses=donorresponse.RESPONSE_TYPES)


def integerise(data):
    try:
        return int(data)
    except ValueError:
        return None
    except TypeError:
        return None

# this lambda and the things which use it exists in surveys.py as well
# ... merge?
id_tuple = lambda x: (x.id, x.as_dict())
name_tuple = lambda x: (x.name, x.as_dict())


def organisation_publication(organisation_code, aggregation_type):
    aggregation_type = integerise(request.args.get('aggregation_type', 2))
    all_aggregation_types = dqaggregationtypes.allAggregationTypes()

    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    aggregate_results = dqorganisations._organisation_indicators_split(
        organisation, aggregation_type)

    aggregate_results['zero'] = util.resort_dict_indicator(
                                aggregate_results['zero'])
    aggregate_results['non_zero'] = util.resort_dict_indicator(
                                    aggregate_results['non_zero'])

    organisation_survey = dqsurveys.getSurvey(organisation_code)
    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation_code)

    surveydata, surveydata_workflow = dqsurveys.get_survey_data_and_workflow(
        organisation_survey, surveydata)

    published_status_by_id = dict(list(map(id_tuple, dqsurveys.publishedStatus())))
    publishedformats = dict(list(map(id_tuple, dqsurveys.publishedFormatsAll())))

    published_status_by_id[None] = {
        'title': 'Unknown',
        'title': 'unknown',
        'publishedstatus_class': 'label-inverse'
        }

    publishedformats[None] = {
        'title': 'Unknown',
        'name': 'unknown',
        'format_class': 'label-inverse'
        }

    latest_runtime = 1

    years = dqorganisations.get_ordinal_values_years()

    test_level_description = {
        3: ("on", "organisation files", ""),
        2: ("on", "each package of data", ""),
        1: ("for", "each activity", "in your data"),
        0: ("for", "each transaction", "in your data")
        }

    links = {
        "organisation_page": url_for(
            'get_organisations',
            organisation_code=organisation.organisation_code),
        "organisation_detail": url_for(
            'organisation_publication_detail',
            organisation_code=organisation.organisation_code),
        "organisation_feedback": url_for(
            'organisation_feedback',
            organisation_code=organisation.organisation_code)
        }
    if surveydata:
        links.update({
                "organisation_survey_edit": url_for(
                    'organisation_survey_edit',
                    organisation_code=organisation.organisation_code,
                    workflow_name=surveydata_workflow)
                })

    def agg_detail(agt):
        tmp = agt.as_dict()
        tmp["selected"] = agt.id == aggregation_type
        return tmp

    agg_type = [agg_detail(agt) for agt in all_aggregation_types]

    frequencies = {
        "less than quarterly": (0.5,
                                """It looks like you publish less often than
          quarterly, so the maximum you can score for IATI data is
          75 points. The total points for the relevant indicators have been
          adjusted accordingly"""),
        "quarterly": (0.9,
                      """It looks like you publish quarterly and not monthly,
          so the maximum you can score for IATI data is 95 points. The total
          points for the relevant indicators have been adjusted
          accordingly.""")
        }

    freq_score = frequencies.get(organisation.frequency, (1.0, ))
    if organisation.frequency in frequencies:
        freq_alert = {"text": frequencies.get(organisation.frequency)[1]}
    else:
        freq_alert = None

    def annotate(res, zero):
        def annotate_test(t):
            tmp2 = dict(t)
            tmp2["results_pct_rounded"] = round(tmp2["results_pct"], 2)
            tmp2["results_num_rounded"] = round(tmp2["results_num"], 2)

            if "test_level" not in tmp2["test"]: # hopeless
                return tmp2

            test_level = tmp2["test"]["test_level"]
            level = test_level_description[test_level]
            preposition, description, coda = level
            tmp2["level_preposition"] = preposition
            tmp2["level_description"] = description
            tmp2["level_coda"] = coda

            return tmp2

        tmp = dict(res)

        tmp["is_activity"] = (
            tmp["indicator"]["indicator_category_name"] == "activity")

        multiplier = {True: freq_score[0], False: 1}[tmp["is_activity"]]

        def points():
            if not zero:
                return round((tmp["results_pct"] * multiplier / 2.0 + 50), 2)

            ind_id = res["indicator"]["id"]

            if surveydata:
                if (res["indicator"]["indicator_ordinal"] and surveydata[ind_id].PublishedFormat) and surveydata[ind_id].OrganisationSurveyData.ordinal_value:
                    return round(
                        (surveydata[ind_id].OrganisationSurveyData.ordinal_value / 3.0) *
                        surveydata[ind_id].PublishedFormat.format_value * 50, 2)
                elif (surveydata[ind_id].PublishedStatus and surveydata[ind_id].PublishedFormat):
                    return (
                        surveydata[ind_id].PublishedStatus.publishedstatus_value *
                        surveydata[ind_id].PublishedFormat.format_value * 50)
                else:
                    return 0
            else:
                return ""

        tmp["points"] = points()
        if not zero:
            tmp["points_minus_50"] = round((tmp["points"] - 50), 2)
            # it all fails if the other branch tries to use this value

        tmp["tests"] = list(map(annotate_test, res["tests"]))

        if zero:
            if surveydata:
                osd = surveydata[tmp["indicator"]["id"]].OrganisationSurveyData.as_dict()

                def status_class_and_text():
                    if tmp["indicator"]["indicator_ordinal"]:
                        return (years[osd["ordinal_value"]]["class"],
                                years[osd["ordinal_value"]]["text"])
                    else:
                        return (published_status_by_id[osd["published_status_id"]]["publishedstatus_class"],
                                published_status_by_id[osd["published_status_id"]]["title"])

                def format_class_and_text():
                    if published_status_by_id[osd["published_status_id"]]["publishedstatus_class"] != 'danger':
                        return (publishedformats[osd["published_format_id"]]["format_class"],
                                publishedformats[osd["published_format_id"]]["title"])
                    else:
                        return ("", "")
                tmp["status_class"], tmp["status_text"] = status_class_and_text()
                tmp["format_class"], tmp["format_text"] = format_class_and_text()

        tmp["results_pct_rounded"] = round(tmp["results_pct"], 2)
        tmp["results_pct_halved_rounded"] = round(tmp["results_pct"]/2.0, 2)

        return tmp

    annotate_zero = lambda res : annotate(res, True)
    annotate_nonzero = lambda res : annotate(res, False)

    # testdata.results_pct|round(2)
    # testdata["results_num"]|round(2)
    # as far as line 296

    def get_sd(data):
        return {
            "OrganisationSurveyData": data[0].as_dict(),
            "Workflow": data[3].as_dict(),
        }

    def jsonsurvey(surveydata):
        if not surveydata:
            return None

        return dict([(x[0], get_sd(x[1])) for x in list(surveydata.items())])

    payload = {
        "links": links,
        "agg_type": agg_type,
        "freq": freq_score,
        "freq_alert": freq_alert,
        "result": {
            "non_zero": list(map(annotate_nonzero, list(aggregate_results["non_zero"].values()))),
            "zero": list(map(annotate_zero, list(aggregate_results["zero"].values())))
            },
        "surveydata": jsonsurvey(surveydata)
    }

    return render_template("organisation_indicators.html",
                           ati_year=app.config['ATI_YEAR'],
                           organisation=organisation,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user,
                           **payload)


def _organisation_publication_detail(organisation_code, aggregation_type,
                                     is_admin):

    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    packages = dqorganisations.organisationPackages(
        organisation.organisation_code)

    all_aggregation_types = dqaggregationtypes.aggregationTypes()

    aggregate_results = dqorganisations.make_publisher_summary(
        organisation, aggregation_type)

    return render_template("organisation_detail.html",
                           organisation=organisation, packages=packages,
                           results=aggregate_results,
                           all_aggregation_types=all_aggregation_types,
                           aggregation_type=aggregation_type,
                           admin=is_admin,
                           loggedinuser=current_user)


def organisation_publication_detail(organisation_code=None):
    aggregation_type=integerise(request.args.get('aggregation_type', 2))
    is_admin = usermanagement.check_perms('admin')
    return _organisation_publication_detail(
        organisation_code, aggregation_type, is_admin)


def _org_pub_csv(organisations, filename, index_data=False, history=False):
    string_io = make_csv(organisations, index_data, history)
    return send_file(string_io, attachment_filename=filename,
                     as_attachment=True)


def all_organisations_publication_index_csv_history():
    organisations = Organisation.query.all()
    return _org_pub_csv(organisations, "tracker_index_history.csv", True, True)


def all_organisations_publication_index_csv():
    organisations = Organisation.query.all()
    return _org_pub_csv(organisations, "dataqualityresults_index.csv", True)


def all_organisations_publication_csv():
    organisations = Organisation.query.all()
    return _org_pub_csv(organisations, "dataqualityresults_all.csv")


def organisation_publication_csv(organisation_code=None):
    organisation = Organisation.query.filter_by(
        organisation_code=organisation_code).first_or_404()

    organisations = [organisation]
    filename = "dataqualityresults_%s.csv" % organisation_code

    return _org_pub_csv(organisations, filename)


def add_packages(organisation):
    def add_org_pkg(package):
        condition = request.form['condition']
        data = {
            'organisation_id': organisation.id,
            'package_id': package,
            'condition': condition
            }
        if dqorganisations.addOrganisationPackage(data):
            flash('Successfully added package to your organisation.',
                  'success')
        else:
            flash("Couldn't add package to your organisation.",
                  'danger')

    packages = request.form.getlist('package')
    [add_org_pkg(package) for package in packages]


def add_packagegroup(organisation):
    condition = request.form['condition']
    data = {
        'organisation_id': organisation.id,
        'packagegroup_id': request.form['packagegroup'],
        'condition': condition
        }
    total = dqorganisations.addOrganisationPackageFromPackageGroup(data)
    if 'applyfuture' in request.form:
        if dqorganisations.addOrganisationPackageGroup(data):
            flash(
                'All future packages in this package group will be '
                'added to this organisation', 'success')
        else:
            flash(
                'Could not ensure that all packages in this package '
                'group will be added to this organisation', 'danger')
    if total:
        flash(
            'Successfully added %d packages to your organisation.' % total,
            'success')
    else:
        flash(
            "No packages were added to your organisation. This "
            "could be because you've already added all existing ones.",
            'danger')


def update_organisation(organisation_code):
    if 'no_independent_reviewer' in request.form:
        irev = True
    else:
        irev = False
    if 'organisation_responded' in request.form:
        orgresp = donorresponse.RESPONSE_TYPES[request.form['organisation_responded']]["id"]
    else:
        orgresp = None
    data = {
        'organisation_code': request.form['organisation_code'],
        'organisation_name': request.form['organisation_name'],
        'no_independent_reviewer': irev,
        'organisation_responded': orgresp
        }
    organisation = dqorganisations.updateOrganisation(
        organisation_code, data)


def organisation_edit(organisation_code=None):
    packages = dqpackages.packages()
    packagegroups = dqpackages.packageGroups()
    organisation = Organisation.where(organisation_code=organisation_code).first()

    if request.method == 'POST':
        if 'addpackages' in request.form:
            add_packages(organisation)
        elif 'addpackagegroup' in request.form:
            add_packagegroup(organisation)
        elif 'updateorganisation' in request.form:
            update_organisation(organisation_code)

    organisationpackages = dqorganisations.organisationPackages(
        organisation.organisation_code)

    return render_template(
        "organisation_edit.html",
        organisation=organisation,
        packages=packages,
        packagegroups=packagegroups,
        donorresponses=donorresponse.RESPONSE_TYPES,
        organisationpackages=organisationpackages,
        admin=usermanagement.check_perms('admin'),
        loggedinuser=current_user)


def organisationpackage_delete(organisation_code=None, package_name=None,
                               organisationpackage_id=None):

    def get_message(result):
        if result:
            return ('Successfully removed package %s from organisation %s.',
                    'success')
        else:
            return ('Could not remove package %s from organisation %s.',
                    'danger')

    result = dqorganisations.deleteOrganisationPackage(
        organisation_code, package_name, organisationpackage_id)

    msg_template, msg_type = get_message(result)
    flash(msg_template % (package_name, organisation_code), msg_type)

    return redirect(url_for('organisation_edit',
                            organisation_code=organisation_code))


def _organisation_indicators_summary(organisation, aggregation_type=2):
    summarydata = dqorganisations._organisation_indicators(organisation,
                                                           aggregation_type)

    # Create crude total score
    totalpct = 0.00
    totalindicators = 0

    if not summarydata:
        return None

    testing = [(i["indicator"]["name"], i["results_pct"]) for i in list(summarydata.values())]
    print(testing)
    percentages = [i["results_pct"] for i in list(summarydata.values())]
    totalpct = reduce(operator.add, percentages, 0.0)
    totalindicators = len(percentages)
    totalscore = totalpct / totalindicators

    return totalscore, totalindicators

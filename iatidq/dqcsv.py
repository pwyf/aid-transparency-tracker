
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2014  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import StringIO
import unicodecsv
import dqorganisations
import survey.data as dqsurveys

id_tuple = lambda x: (x.id, x)

def extract_survey_data_with_guards(surveydata, indicator_id,
                                    field, val1_name, val2_name):
    if indicator_id in surveydata:
        resp = surveydata[indicator_id]
        if hasattr(resp, field):
            data = getattr(resp, field)
            if hasattr(data, val1_name) and hasattr(data, val2_name):
                return getattr(data, val1_name), getattr(data, val2_name)
    return "", 0

def get_publication_status(surveydata, indicator_id):
    return extract_survey_data_with_guards(surveydata, indicator_id, 'PublishedStatus', 
                                           'name', 'publishedstatus_value')

def get_publication_format(surveydata, indicator_id):
    return extract_survey_data_with_guards(surveydata, indicator_id, 'PublishedFormat', 
                                           'name', 'format_value')
    
def get_frequency_multiplier(frequency):
    if (frequency == "less than quarterly"):
        return 0.5
    elif (frequency == "quarterly"):
        return 0.9
    else:
        return 1.0

def write_agg_csv_result(out, organisation, freq, result):
    if result['results_pct'] == 0:
        points = 0
    else:
        points = float(result['results_pct']) * freq / 2.0 + 50

    i = result["indicator"]
    out.writerow({
            "organisation_name": organisation.organisation_name, 
            "organisation_code": organisation.organisation_code, 
            "indicator_category_name": i['indicator_category_name'],
            "indicator_subcategory_name": i['indicator_subcategory_name'],
            "indicator_name": i['description'], 
            "indicator_description": i['longdescription'], 
            "percentage_passed": result['results_pct'], 
            "num_results": result['results_num'],
            "points": str(points)
            })      

def write_organisation_publications_csv(out, organisation):
    aggregate_results = dqorganisations._organisation_indicators(organisation)

    freq = get_frequency_multiplier(organisation.frequency)

    for resultid, result in aggregate_results.items():
        write_agg_csv_result(out, organisation, freq, result)


class CSVIndicatorInfo(object):
    def __init__(self, description, name, _id, category_name, 
                 subcategory_name, order, weight):
        self.description = description
        self.name = name
        self.id = _id
        self.category_name = category_name
        self.subcategory_name = subcategory_name
        self.order = order
        self.weight = weight

    def as_dict(self):
        return {
            "indicator_name": self.description,
            "indicator_id": self.name,
            "indicator_category_name": self.category_name,
            "indicator_subcategory_name": self.subcategory_name,
            "indicator_order": self.order,
            "indicator_weight": self.weight
            }

class CSVRow(object):
    def __init__(self, *args):
        self.field_data = args

    def write_to(self, stream, workflow):
        self._write(stream, workflow, *self.field_data)

    def _write(self, out, workflow_name, organisation, indicator_info, indicator_total_weighted_points, indicator_category_subcategory, iati_manual, publication_format, publication_format_points, total_points, iati_data_quality_passed, iati_data_quality_points, freq, frequency_multiplier, iati_data_quality_total_points, survey_publication_status, survey_publication_status_value, survey_ordinal_value, survey_publication_format, survey_publication_format_value, survey_total_points):
        data = {
            "id": organisation.organisation_code + "-" + indicator_info.name,
            "organisation_name": organisation.organisation_name, 
            "organisation_code": organisation.organisation_code, 
            "indicator_total_weighted_points": indicator_total_weighted_points,
            "indicator_category_subcategory": indicator_category_subcategory,
            "iati_manual": iati_manual,
            "publication_format": publication_format,
            "publication_format_points": str(publication_format_points),
            "total_points": str(total_points),
            "iati_data_quality_passed": str(iati_data_quality_passed),
            "iati_data_quality_points": str(iati_data_quality_points),
            "iati_data_quality_frequency": organisation.frequency,
            "iati_data_quality_frequency_value": str(freq),
            "iati_data_quality_frequency_multiplier": str(frequency_multiplier),
            "iati_data_quality_total_points": str(iati_data_quality_total_points),
            "survey_publication_status": str(survey_publication_status),
            "survey_publication_status_value": str(survey_publication_status_value),
            "survey_ordinal_value": str(survey_ordinal_value),
            "survey_publication_format": str(survey_publication_format),
            "survey_publication_format_value": str(survey_publication_format_value),
            "survey_total_points": str(survey_total_points)
            }
        data.update(indicator_info.as_dict())
        if workflow_name:
            data['survey_workflow_name'] = workflow_name
            data['survey_source'] = survey_source
            data['survey_comment'] = survey_comment
            data['survey_agree'] = survey_agree
        out.writerow(data)
    
def write_agg_csv_result_index(out, organisation, freq, result, iati_manual, surveydata, surveydata_workflow, published_status, published_format, history=False, workflows=None):

    def calculate_ordinal_points(thevalue, theformat, thetype):
        if thetype == 'commitment':
            return thevalue
        else:
            if thevalue == None:
                return 0
            points = (float(thevalue)/3.0)*float(theformat)
            return points

        
    i = result["indicator"]

    if iati_manual == 'iati':
        indicator_info = CSVIndicatorInfo(i["description"], i["name"], i["id"],
                                          i["indicator_category_name"],
                                          i["indicator_subcategory_name"],
                                          i["indicator_order"],
                                          i["indicator_weight"])
    
        if (indicator_info.category_name == 'activity'):
            frequency_multiplier = freq
        else:
            frequency_multiplier = 1

        iati_data_quality_total_points = (float(result['results_pct']) * frequency_multiplier) / 2.0
        iati_data_quality_points = (float(result['results_pct']) / 2.0)
        iati_data_quality_passed = float(result["results_pct"])

        survey_publication_status = ""
        survey_publication_status_value = ""
        survey_ordinal_value = ""
        survey_publication_format = ""
        survey_publication_format_value = ""
        survey_total_points = 0

        publication_format = "iati"
        publication_format_points = 50
        total_points = iati_data_quality_total_points + 50.0
    else:
        frequency_multiplier=1
        if iati_manual == "commitment":
            indicator_ordinal = 1
            indicator_info = CSVIndicatorInfo(i.description, i.name, i.id,
                                              "commitment", 
                                              i.indicator_subcategory_name,
                                              i.indicator_order,
                                              i.indicator_weight)
            iati_manual = "manual"
            survey_category = "commitment"
        else:
            indicator_info = CSVIndicatorInfo(i["description"], i["name"],
                                              i["id"],
                                              i["indicator_category_name"],
                                              i["indicator_subcategory_name"],
                                              i["indicator_order"],
                                              i["indicator_weight"])

            indicator_ordinal = i["indicator_ordinal"]
            survey_category = "publication"
        if surveydata:
            if not history:
                iati_data_quality_total_points = 0
                iati_data_quality_points = 0
                iati_data_quality_passed = 0

                survey_publication_status, survey_publication_status_value = get_publication_status(surveydata, indicator_info.id)

                survey_publication_format, survey_publication_format_value = get_publication_format(surveydata, indicator_info.id)
                survey_publication_format_value *= 50

                if indicator_ordinal:
                    survey_ordinal_value = surveydata[indicator_info.id].OrganisationSurveyData.ordinal_value
                    survey_total_points = calculate_ordinal_points(surveydata[indicator_info.id].OrganisationSurveyData.ordinal_value, 
                                    survey_publication_format_value, 
                                    survey_category)
                else:
                    survey_ordinal_value = ""
                    survey_total_points = survey_publication_format_value * survey_publication_status_value

                publication_format = survey_publication_format
                publication_format_points = survey_total_points
                total_points = survey_total_points
            else:
                sd=surveydata
                for workflow in workflows:
                    print workflow.Workflow.name
                    if not sd:
                        continue
                    surveydata = sd.get(workflow.Workflow.name)
                    if not surveydata:
                        continue
                    print "continuing"
                    iati_data_quality_total_points = 0
                    iati_data_quality_points = 0
                    iati_data_quality_passed = 0

                    survey_publication_status, survey_publication_status_value = get_publication_status(surveydata, indicator_info.id)

                    survey_publication_format, survey_publication_format_value = get_publication_format(surveydata, indicator_info.id)
                    survey_publication_format_value *= 50

                    if indicator_ordinal:
                        survey_ordinal_value = surveydata[indicator_info.id].OrganisationSurveyData.ordinal_value
                        survey_total_points = calculate_ordinal_points(surveydata[indicator_info.id].OrganisationSurveyData.ordinal_value, 
                                        survey_publication_format_value, 
                                        survey_category)
                    else:
                        survey_ordinal_value = ""
                        survey_total_points = survey_publication_format_value * survey_publication_status_value

                    publication_format = survey_publication_format
                    publication_format_points = survey_total_points
                    total_points = survey_total_points

                    try:
                        indicator_total_weighted_points = total_points * indicator_info.weight
                    except Exception:
                        indicator_total_weighted_points = 0

                    try:
                        indicator_category_subcategory = indicator_info.category_name + "-" + indicator_info.subcategory_name
                    except Exception:
                        indicator_category_subcategory = ""

                    if indicator_info.category_name == "commitment":
                        publication_format = "not-applicable"
                    survey_source = surveydata[indicator_info.id].OrganisationSurveyData.published_source
                    survey_comment = surveydata[indicator_info.id].OrganisationSurveyData.published_comment
                    survey_agree = surveydata[indicator_info.id].OrganisationSurveyData.published_accepted
                    print "writing csv row for", workflow.Workflow.name

                    csv_row = CSVRow(organisation, indicator_info, indicator_total_weighted_points, indicator_category_subcategory, iati_manual, publication_format, publication_format_points, total_points, iati_data_quality_passed, iati_data_quality_points, freq, frequency_multiplier, iati_data_quality_total_points, survey_publication_status, survey_publication_status_value, survey_ordinal_value, survey_publication_format, survey_publication_format_value, survey_total_points)
                    csv_row.write_to(out, workflow.Workflow.name)
        else:
            iati_data_quality_total_points = 0
            iati_data_quality_points = 0
            iati_data_quality_passed = 0
            survey_publication_status = ""
            survey_publication_status_value = ""
            survey_ordinal_value = ""
            survey_publication_format = ""
            survey_publication_format_value = ""
            survey_total_points = 0

            publication_format = "NO IATI DATA OR SURVEY DATA"
            publication_format_points = 0
            total_points = 0
    try:
        indicator_total_weighted_points = total_points * indicator_info.weight
    except Exception:
        indicator_total_weighted_points = 0

    try:
        indicator_category_subcategory = indicator_info.category_name + "-" + indicator_info.subcategory_name
    except Exception:
        indicator_category_subcategory = ""

    if indicator_info.category_name == "commitment":
        publication_format = "not-applicable"

    if not history:
        csv_row = CSVRow(organisation, indicator_info, indicator_total_weighted_points, indicator_category_subcategory, iati_manual, publication_format, publication_format_points, total_points, iati_data_quality_passed, iati_data_quality_points, freq, frequency_multiplier, iati_data_quality_total_points, survey_publication_status, survey_publication_status_value, survey_ordinal_value, survey_publication_format, survey_publication_format_value, survey_total_points)
        csv_row.write_to(out, None)

def write_organisation_publications_csv_index(out, organisation, history=False):
    aggregate_results = dqorganisations._organisation_indicators_split(organisation)

    freq = get_frequency_multiplier(organisation.frequency)
       
    organisation_survey = dqsurveys.getSurvey(organisation.organisation_code)
    surveydata = dqsurveys.getSurveyDataAllWorkflows(organisation.organisation_code)

    if not history:
        surveydata, surveydata_workflow = dqsurveys.get_survey_data_and_workflow(
            organisation_survey, surveydata)
        workflows = None
    else:
        workflows=dqsurveys.workflowsAll()
        surveydata_workflow=None

    published_status_by_id = dict(map(id_tuple, dqsurveys.publishedStatus()))
    publishedformats = dict(map(id_tuple, dqsurveys.publishedFormatsAll()))

    for resultid, result in aggregate_results["non_zero"].items():
        write_agg_csv_result_index(out, organisation, freq, result, "iati", None, None, None, None)

    for resultid, result in aggregate_results["zero"].items():
        write_agg_csv_result_index(out, organisation, freq, result, "manual", surveydata, surveydata_workflow, published_status_by_id, publishedformats, history, workflows)

    for resultid, result in aggregate_results["commitment"].items():
        write_agg_csv_result_index(out, organisation, freq, result, "commitment", surveydata, surveydata_workflow, published_status_by_id, publishedformats, history, workflows)

csv_fieldnames = [
    "organisation_name",
    "organisation_code",
    "indicator_category_name",
    "indicator_subcategory_name",
    "indicator_name",
    "indicator_description",
    "percentage_passed",
    "num_results",
    "points"
    ]

csv_fieldnames_index = [
    "id",
    "organisation_name",
    "organisation_code",
    "indicator_total_weighted_points",
    "indicator_id",
    "indicator_name",
    "indicator_category_name",
    "indicator_subcategory_name",
    "indicator_category_subcategory",
    "indicator_order",
    "indicator_weight",
    "iati_manual",
    "publication_format",
    "publication_format_points",
    "total_points",
    "iati_data_quality_passed",
    "iati_data_quality_points",
    "iati_data_quality_frequency",
    "iati_data_quality_frequency_value",
    "iati_data_quality_frequency_multiplier",
    "iati_data_quality_total_points",
    "survey_publication_status",
    "survey_publication_status_value",
    "survey_ordinal_value",
    "survey_publication_format",
    "survey_publication_format_value",
    "survey_total_points"
    ]

def make_csv(organisations, index_data=False, history=False):
    strIO = StringIO.StringIO()

    if index_data:
        csv_headers = csv_fieldnames_index
    else:
        csv_headers = csv_fieldnames
    if history:
        csv_headers.extend(["survey_workflow_name", "survey_source", "survey_comment", "survey_agree"])
    out = unicodecsv.DictWriter(strIO, fieldnames=csv_headers)
    headers = {}

    for fieldname in csv_headers:
        headers[fieldname] = fieldname
    out.writerow(headers)

    for organisation in organisations:
        if index_data:
            write_organisation_publications_csv_index(out, organisation, history)
        else:
            write_organisation_publications_csv(out, organisation)

    strIO.seek(0)
    return strIO

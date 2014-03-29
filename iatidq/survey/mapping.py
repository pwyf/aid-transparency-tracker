
import os
import unicodecsv

from iatidq import app

ORGANISATION_MAP_FILE = 'organisations_with_identifiers.csv'
# Trying to avoid proliferation of files...
OLD_YEAR = '2013'
NEW_YEAR = '2014'
OLD_ORG_FIELD_ID = OLD_YEAR + '_organisation_code'
NEW_ORG_FIELD_ID = 'organisation_code'
OLD_INDICATORS_FILE = OLD_YEAR + '_' + NEW_YEAR + '_indicators.csv'
OLD_RESULTS_FILE = OLD_YEAR + '_results.csv'
NEW_INDICATOR_NAME = NEW_YEAR + '_indicator_name'
OLD_INDICATOR_NAME = OLD_YEAR + '_indicator_name'

thisfile_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(thisfile_dir, "../../", "tests/")

def get_old_organisation_id(organisation_code='GB-1'):
    old_organisation_file = os.path.abspath(os.path.join(path, ORGANISATION_MAP_FILE))

    old_organisation_data = unicodecsv.DictReader(file(old_organisation_file))
    for row in old_organisation_data:
        if row[NEW_ORG_FIELD_ID] == organisation_code:
            return row[OLD_ORG_FIELD_ID]

# read in(!) a CSV file of last year's indicators or survey questions;
# significant fields:

#  question_number  - the numerical ID of the indicator in the previous year
#  YYYY_indicator_name - the name of the indicator in the current year,
#                        e.g. 2014_indicator_name

def get_old_indicators():
    old_indicators_file = os.path.join(path, OLD_INDICATORS_FILE)
    old_indicators_data = unicodecsv.DictReader(file(old_indicators_file))

    indicator_data = {}
    for row in old_indicators_data:
        if ((row[OLD_INDICATOR_NAME]) and (row[NEW_INDICATOR_NAME])):
            indicator_data[row[OLD_INDICATOR_NAME]] = row[NEW_INDICATOR_NAME]
    return indicator_data


# read in(!) a CSV file of last year's results; it must have fields

# id              - not used
# question_id     - the indicator id of the question in the old data
# target_id       - the organisation ID in the old data
# result          - used in templates
# result_evidence - used in templates
# result_comments - used in templates
# result_review   - not used
def get_organisation_results(organisation_code, newindicators):
    old_organisation_id = get_old_organisation_id(organisation_code)
    indicators = get_old_indicators()

    old_results_file = os.path.join(path, OLD_RESULTS_FILE)
    old_results_data = unicodecsv.DictReader(file(old_results_file))

    data = {}

    # old_indicators is a map from int -> string, e.g., 1 -> "foia"

    for d in old_results_data:
        if d["organisation_code"] == old_organisation_id:
            try:
                question_id = d["indicator_id"]
                d["newindicator_id"] = indicators[question_id]
                data[indicators[question_id]] = d
            except KeyError:
                pass

    for indicator_name in newindicators:
        if indicator_name not in data:
            data[indicator_name] = { 'result': '' }

    return data

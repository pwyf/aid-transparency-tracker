
import os
import unicodecsv

from iatidq import app

YEAR_MAP_FILE = '2012_2013_organisation_mapping.csv'
OLD_YEAR = '2012'
NEW_YEAR = '2013'
OLD_FIELD_ID = OLD_YEAR + '_id'
NEW_FIELD_ID = NEW_YEAR + '_id'
OLD_INDICATORS_FILE = OLD_YEAR + '_indicators.csv'
OLD_RESULTS_FILE = OLD_YEAR + '_results.csv'
NEW_INDICATOR_NAME = NEW_YEAR + '_indicator_name'

def get_old_organisation_id(organisation_code='GB-1'):
    path = app.config["DATA_STORAGE_DIR"]
    old_organisation_file = os.path.join(path, YEAR_MAP_FILE)

    old_organisation_data = unicodecsv.DictReader(file(old_organisation_file))
    for row in old_organisation_data:
        if row[NEW_FIELD_ID] == organisation_code:
            return row[OLD_FIELD_ID]

# read in(!) a CSV file of last year's indicators or survey questions;
# significant fields:

#  question_number  - the numerical ID of the indicator in the previous year
#  YYYY_indicator_name - the name of the indicator in the current year,
#                        e.g. 2014_indicator_name

def get_old_indicators():
    path = app.config["DATA_STORAGE_DIR"]
    old_indicators_file = os.path.join(path, OLD_INDICATORS_FILE)
    old_indicators_data = unicodecsv.DictReader(file(old_indicators_file))

    indicator_data = {}
    for row in old_indicators_data:
        question_number = int(row["question_number"])
        new_indicator_name = row[NEW_INDICATOR_NAME]

        assert question_number != 0
        if (question_number and new_indicator_name):
            indicator_data[question_number] = new_indicator_name

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
    old_indicators = get_old_indicators()

    path = app.config["DATA_STORAGE_DIR"]

    old_results_file = os.path.join(path, OLD_RESULTS_FILE)
    old_results_data = unicodecsv.DictReader(file(old_results_file))

    data = {}

    # old_indicators is a map from int -> string, e.g., 1 -> "foia"

    for d in old_results_data:
        if d["target_id"] == old_organisation_id:
            assert "question_id" in d
            question_id = int(d["question_id"])
            if question_id in old_indicators:
                data[old_indicators[question_id]] = d

    for indicator_name in newindicators:
        if indicator_name not in data:
            data[indicator_name] = { 'result': '' }

    return data

import csv
from os.path import dirname, join

from flask import current_app
import iatikit
from bdd_tester import BDDTester

from . import utils


def get_current_countries(publisher, current_data):
    country_codes = []

    for dataset in publisher.datasets:
        for idx, activity in enumerate(dataset.activities):
            if dataset.name not in current_data or idx not in current_data[dataset.name] or current_data[dataset.name][idx] is False:
                continue
            country_codes += activity.etree.xpath('recipient-country/@code')
            country_codes = list(set(country_codes))
    return country_codes


def country_strategy_or_mou(org, snapshot_date, test_name,
                            current_data_results):
    iati_result_path = current_app.config.get('IATI_RESULT_PATH')
    output_filepath = join(iati_result_path,
                           snapshot_date, org.organisation_code,
                           utils.slugify(test_name) + '.csv')

    iati_data_path = current_app.config.get('IATI_DATA_PATH')
    snapshot_xml_path = join(iati_data_path, snapshot_date)
    publisher = iatikit.data(snapshot_xml_path).publishers.get(
        org.registry_slug)

    current_country_codes = get_current_countries(
        publisher, current_data_results)

    if current_country_codes == []:
        return

    country_strategies = {}
    for dataset in publisher.datasets:
        for idx, activity in enumerate(dataset.activities):
            if dataset.name not in current_data_results or idx not in current_data_results[dataset.name] or current_data_results[dataset.name][idx] is False:
                continue
            mous = activity.etree.xpath('document-link[category/@code="A09"]')
            if mous == []:
                continue
            for c in activity.etree.xpath('recipient-country/@code'):
                country_strategies[c] = {
                    'dataset': dataset.name,
                    'identifier': activity.id,
                    'index': idx,
                    'result': 'pass',
                    'hierarchy': activity.etree.get('hierarchy', '1'),
                    'explanation': 'A09 found for {}',
                }

        for idx, organisation in enumerate(dataset.organisations):
            org_level_docs = organisation.etree.xpath(
                'document-link[category/@code="B03"]/recipient-country/@code')
            org_level_docs += organisation.etree.xpath(
                'document-link[category/@code="B13"]/recipient-country/@code')
            org_level_docs = list(set(org_level_docs))
            for c in org_level_docs:
                country_strategies[c] = {
                    'dataset': dataset.name,
                    'identifier': organisation.id,
                    'index': idx,
                    'result': 'pass',
                    'hierarchy': 1,
                    'explanation': 'B03 or B13 found for {}',
                }

    default_row = {
        'dataset': '',
        'identifier': '',
        'index': 0,
        'result': 'fail',
        'hierarchy': 1,
        'explanation': 'No country strategy or MoU found for {}',
    }
    fieldnames = ['dataset', 'identifier', 'index', 'result',
                  'hierarchy', 'explanation']
    with open(output_filepath, 'w') as handler:
        writer = csv.DictWriter(handler, fieldnames=fieldnames)
        writer.writeheader()
        for country_code in current_country_codes:
            row = country_strategies.get(country_code, dict(default_row))
            row['explanation'] = row['explanation'].format(country_code)
            writer.writerow(row)


def disaggregated_budget(org, snapshot_date, test_name,
                         current_data_results):
    iati_result_path = current_app.config.get('IATI_RESULT_PATH')
    output_filepath = join(iati_result_path,
                           snapshot_date, org.organisation_code,
                           utils.slugify(test_name) + '.csv')

    iati_data_path = current_app.config.get('IATI_DATA_PATH')
    snapshot_xml_path = join(iati_data_path, snapshot_date)
    publisher = iatikit.data(snapshot_xml_path).publishers.get(
        org.registry_slug)

    codelists = iatikit.codelists()
    current_country_codes = get_current_countries(
        publisher, current_data_results)

    disaggregated_budget_tmpl = '''@iati-organisation
Feature: Total disaggregated budget

  Scenario: Country budget available one year forward
    Given file is an organisation file
     Then `recipient-country-budget[recipient-country/@code="{country_code}"]` should be available 1 year forward

  Scenario: Country budget available two years forward
    Given file is an organisation file
     Then `recipient-country-budget[recipient-country/@code="{country_code}"]` should be available 2 years forward

  Scenario: Country budget available three years forward
    Given file is an organisation file
     Then `recipient-country-budget[recipient-country/@code="{country_code}"]` should be available 3 years forward
    '''
    base_path = join(dirname(current_app.root_path),
                     'index_indicator_definitions', 'test_definitions')
    step_definitions = join(base_path, 'step_definitions.py')
    tester = BDDTester(step_definitions)

    explanation_tmpl = 'Budget for {country_code} {found} ' + \
                       '{year} year{plural} forward'
    fieldnames = ['dataset', 'identifier', 'index', 'result',
                  'hierarchy', 'explanation']
    with open(output_filepath, 'w') as handler:
        writer = csv.DictWriter(handler, fieldnames=fieldnames)
        writer.writeheader()
        for country_code in current_country_codes:
            feature = tester._gherkinify_feature(
                disaggregated_budget_tmpl.format(country_code=country_code))
            for dataset in publisher.datasets:
                for idx, organisation in enumerate(dataset.organisations):
                    for year, test in enumerate(feature.tests):
                        result = test(
                            organisation.etree,
                            today=snapshot_date,
                            codelists=codelists)
                        explanation = explanation_tmpl.format(
                            country_code=country_code,
                            found='found' if result else 'not found',
                            year=year + 1,
                            plural='s' if year > 0 else '',
                        )
                        writer.writerow({
                            'dataset': dataset.name,
                            'identifier': organisation.id,
                            'index': idx,
                            'result': 'pass' if result else 'fail',
                            'hierarchy': 1,
                            'explanation': explanation,
                        })

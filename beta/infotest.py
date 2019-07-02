import csv
from os.path import join

from flask import current_app
import iatikit

from . import utils


def get_current_countries(publisher, current_data):
    country_codes = []

    for activity in publisher.activities:
        idx = activity.etree.getparent().index(activity.etree)
        if current_data[activity.dataset.name][idx] is False:
            continue
        country_codes += activity.etree.xpath('recipient-country/@code')
        country_codes = list(set(country_codes))
    return country_codes


def country_strategy_or_mou(org, snapshot_date, test_name,
                            current_data_results):
    iati_result_path = current_app.config.get('IATI_RESULT_PATH')
    output_filepath = join(iati_result_path,
                           snapshot_date, org.registry_slug,
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
    for activity in publisher.activities:
        idx = activity.etree.getparent().index(activity.etree)
        if current_data_results[activity.dataset.name][idx] is False:
            continue
        mous = activity.etree.xpath('document-link[category/@code="A09"]')
        if mous == []:
            continue
        for c in activity.etree.xpath('recipient-country/@code'):
            country_strategies[c] = {
                'dataset': activity.dataset.name,
                'identifier': activity.id,
                'index': activity.etree.getparent().index(activity.etree),
                'result': 'pass',
                'hierarchy': activity.etree.get('hierarchy', '1'),
                'explanation': 'A09 found for {}',
            }

    for organisation in publisher.organisations:
        org_level_docs = organisation.etree.xpath(
            'document-link[category/@code="B03"]/recipient-country/@code')
        org_level_docs += organisation.etree.xpath(
            'document-link[category/@code="B13"]/recipient-country/@code')
        org_level_docs = list(set(org_level_docs))
        for c in org_level_docs:
            idx = organisation.etree.getparent().index(organisation.etree)
            country_strategies[c] = {
                'dataset': organisation.dataset.name,
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

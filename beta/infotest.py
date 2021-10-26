import csv
from os.path import dirname, join
import json

from flask import current_app
import iatikit
from bdd_tester import BDDTester

from . import utils
from .excluded_xm_dac import excluded_xm_dac


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
                    'result': '1',
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
                    'result': '1',
                    'hierarchy': 1,
                    'explanation': 'B03 or B13 found for {}',
                }

    default_row = {
        'dataset': '',
        'identifier': '',
        'index': 0,
        'result': '0',
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
                         current_data_results, condition):
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

                    if condition:
                        activity_condition, org_condition = condition.split('|')

                        if org_condition.strip() and not organisation.etree.xpath(org_condition):
                            continue

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
                            'result': '1' if result else '0',
                            'hierarchy': 1,
                            'explanation': explanation,
                        })



def process_publishers():
    test_data_path = join(dirname(current_app.root_path), 'tests')
    publishers_by_prefix = {}
    publishers_by_ident = {}   

    with open(join(test_data_path,'publishers.json')) as f:
        publishers_json = json.load(f)
    for publisher in publishers_json:
        publisher['ident'] = publisher['IATI Organisation Identifier']
        publisher['prefix'] = publisher['Datasets Link'].split('/')[-1]
        publishers_by_ident[publisher['ident']] = publisher
        publishers_by_prefix[publisher['prefix']] = publisher
    
    return publishers_by_prefix, publishers_by_ident

def process_sector():
    test_data_path = join(dirname(current_app.root_path), 'tests')

    sector_by_code = {}

    with open(join(test_data_path,'Sector.json')) as f:
        sector_json = json.load(f)  
    for sector in sector_json['data']:
        code = sector['code']
        if code in excluded_xm_dac:
            continue
        fullcode = f'XM-DAC-{code}'
        sector['fullcode'] = fullcode
        sector_by_code[fullcode] = sector
    return sector_by_code

def process_orgid():
    test_data_path = join(dirname(current_app.root_path), 'tests')

    orgid_by_code = {}

    with open(join(test_data_path,'orgid.json')) as f:
        orgid_json = json.load(f)  
    for orgid in orgid_json['lists']:
        code = orgid['code']
        if code == 'XM-DAC':
            continue
        orgid_by_code[orgid['code']] = orgid

    return orgid_by_code


def test_participating_org_refs(publisher_prefix, org_tree, activity_tree, self_refs):

    aid_types = activity_tree.xpath('default-aid-type/@code')
    if 'F01' in aid_types or 'G01' in aid_types:
        return 'Aid type is F01 (Debt relief) or G01 (Administrative costs not included elsewhere)', None

    publishers_by_prefix, publishers_by_ident = process_publishers() 
    sector_by_code = process_sector()
    orgid_by_code = process_orgid()

    publisher_registry_id = publishers_by_prefix[publisher_prefix]['ident']
    organisation_ident = None
    organisation_reporting_org_ref = None
    activity_reporting_org_ref = None

    result = org_tree.xpath('organisation-identifier/text()')

    if not self_refs:
        self_refs = set([publisher_registry_id])
        if len(result):
            organisation_ident = result[0]
            self_refs.add(organisation_ident)

        result = org_tree.xpath('reporting-org/@ref')
        if len(result):
            organisation_reporting_org_ref = result[0]
            self_refs.add(organisation_reporting_org_ref)

        result = activity_tree.xpath('reporting-org/@ref')
        if len(result):
            activity_reporting_org_ref = result[0]
            self_refs.add(activity_reporting_org_ref)
    
    # print('self refs:', self_refs)
    
    participating_orgs = set(activity_tree.xpath('participating-org'))

    narratives_no_refs = 0
    for participating_org in participating_orgs:
        narratives = [po for po in participating_org.xpath('narrative/text()') if po.strip()]
        refs = participating_org.xpath('@ref')
        if len(narratives) and not len(refs):
            narratives_no_refs += 1
    
    # print(f"narratives with no refs count: {narratives_no_refs}")
        
    participating_orgs_refs = set(activity_tree.xpath('participating-org/@ref'))
    # print('participating org refs:', participating_orgs_refs)


    participating_orgs_no_self_ref = participating_orgs_refs - self_refs
    # print('participating orgs no self ref:', participating_orgs_no_self_ref)

    denominator =  len(participating_orgs_no_self_ref) + narratives_no_refs
    # print('count of orgs to test:',len(participating_orgs_no_self_ref))
    
    # print(f'denominator: {denominator}')
    if denominator == 0:
        return 'All self refs', None

    # publisher matching
    publisher_idents = set(publishers_by_ident)

    publisher_matches = participating_orgs_no_self_ref & publisher_idents

    # print('matching publisher:', publisher_matches)

    remaining = participating_orgs_no_self_ref - publisher_matches
    
    # sectors matching
    # print('sectors to test:', remaining)

    sectors = set(sector_by_code)

    sectors_matches = remaining & sectors

    # print('matching sectors:', sectors_matches)

    remaining = remaining - sectors_matches    
    
    # org ids
    # print('org_id_to_test:', remaining)
    
    org_ids = set(orgid_by_code)

    matching_org_ids = set()

    for org_ref in remaining:
        if any(org_ref.startswith(org_id) for org_id in org_ids):
            matching_org_ids.add(org_ref)
    # print('matching_org_ids:', matching_org_ids)

    failed_to_match = remaining - matching_org_ids

    # print(f'failed to match:', failed_to_match)
    # print(f'failed to match count:', len(failed_to_match))
    

    score = (len(participating_orgs_no_self_ref) * 1.0 - len(failed_to_match))/denominator
    explanation = f'score: ({len(participating_orgs_no_self_ref)} - {len(failed_to_match)})/{denominator}'

    return explanation, score


def networked_data_ref(org, snapshot_date, test_name,
                       current_data_results, condition):

    iati_result_path = current_app.config.get('IATI_RESULT_PATH')
    output_filepath = join(iati_result_path,
                           snapshot_date, org.organisation_code,
                           utils.slugify(test_name) + '.csv')

    iati_data_path = current_app.config.get('IATI_DATA_PATH')
    snapshot_xml_path = join(iati_data_path, snapshot_date)
    publisher = iatikit.data(snapshot_xml_path).publishers.get(org.registry_slug)

    fieldnames = ['dataset', 'identifier', 'index', 'result',
                  'hierarchy', 'explanation']

    publishers_by_prefix, publishers_by_ident = process_publishers() 
    sector_by_code = process_sector()
    orgid_by_code = process_orgid()

    organisation = None

    for dataset in publisher.datasets:
        for idx, org_dataset in enumerate(dataset.organisations):
            if condition:
                activity_condition, org_condition = condition.split('|')
                if org_condition.strip() and not org_dataset.etree.xpath(org_condition):
                    continue
                organisation = org_dataset
                break
            else:
                organisation = org_dataset

    if not organisation:
        raise Exception(f'Can not find organization for {org.organisation_code} - {org.registry_slug}')

    self_refs = set()
    if condition:
        activity_condition, org_condition = condition.split('|')

        if activity_condition:
            self_refs = set([org.organisation_code])

    with open(output_filepath, 'w') as handler:
        writer = csv.DictWriter(handler, fieldnames=fieldnames)
        writer.writeheader()

        for dataset in publisher.datasets:
            for idx, activity in enumerate(dataset.activities):
                if dataset.name not in current_data_results or idx not in current_data_results[dataset.name]:
                    continue

                explanation, score = test_participating_org_refs(org.registry_slug, organisation.etree, activity.etree, self_refs)

                if score is None:
                    score = 'not relevant'

                writer.writerow({
                    'dataset': dataset.name,
                    'identifier': activity.id,
                    'index': idx,
                    'result': str(score),
                    'hierarchy': 1,
                    'explanation': explanation,
                })

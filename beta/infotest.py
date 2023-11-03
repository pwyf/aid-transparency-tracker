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

    with open(join(test_data_path,'CRSChannelCode.json')) as f:
        sector_json = json.load(f) 
    with open(join(test_data_path,'AgencyCodes.json')) as f:
        agency_json = json.load(f)
    all_codes = sector_json['data'] + agency_json['data']
    for sector in all_codes:
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


def test_participating_org_refs(publisher_prefix, activity_tree, self_refs):

    aid_types = activity_tree.xpath('default-aid-type/@code')
    if 'A01' in aid_types or 'A02' in aid_types:
        return 'Aid type is A01 or A02', None

    if not self_refs:
        return 'Organisation excluded from networked data test', None

    publishers_by_prefix, publishers_by_ident = process_publishers() 
    sector_by_code = process_sector()
    orgid_by_code = process_orgid()

    publisher_registry_id = publishers_by_prefix[publisher_prefix]['ident']
    organisation_ident = None
    organisation_reporting_org_ref = None
    activity_reporting_org_ref = None

    # print('self refs:', self_refs)
    
    participating_orgs = set(activity_tree.xpath('participating-org'))

    narratives_no_refs = 0
    for participating_org in participating_orgs:
        narratives = [po for po in participating_org.xpath('narrative/text()') if po.strip()]
        refs = participating_org.xpath('@ref')
        if len(narratives) and not len([ref for ref in refs if ref.strip()]):
            narratives_no_refs += 1
    
    # print(f"narratives with no refs count: {narratives_no_refs}")
        
    participating_orgs_refs = set(ref for ref in activity_tree.xpath('participating-org/@ref') if ref.strip())
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

    # temporary fix for Korean organisations
    if publisher_prefix == "odakorea":
        korean_orgs = set([x for x in participating_orgs_no_self_ref if x.startswith('KR-GOV')])
        publisher_idents = publisher_idents | korean_orgs

    publisher_matches = participating_orgs_no_self_ref & publisher_idents

    # print(publisher_matches)

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

    # print(score)
    # print(explanation)

    return explanation, score


def networked_data_part_2(org, snapshot_date, test_name, current_data_results, condition):
    """Calculates score for Networked Data test, part 2: participating orgs with valid IDs
    
    Part 2 of the Networked Data scores each activity according to how many of the
    participating organisations are referred to with valid references. The score for the
    organisation is the average of the scores for each of their activities. This
    function calculates the score for each activity and writes it to the file
    <test_name.csv> (test_name for this test is currently 'participating_orgs').
    
    :param org: The organisation to be processed.
    :type org: iatidq.models.Organisation
    :param snapshot_date: The date of the data snapshot/download to use.
    :type snapshot_date: str (in YYYY-MM-DD format)
    :param test_name: The test name
    :type test_name: str
    :param current_data_results: All of the organisation's activities, grouped by
        dataset slug, indicating whether the activity is current or not.
    :type current_data_results: dictionary<dataset-slug, dictionary<activity-index, boolean>>
    :param condition: A condition which must be satisfied for the test to be applied
    :type condition: str (XPath expression)
    """

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

    self_refs = set()

    if org.self_ref:
        self_refs.update(org.self_ref.split(","))

    with open(output_filepath, 'w') as handler:
        writer = csv.DictWriter(handler, fieldnames=fieldnames)
        writer.writeheader()

        for dataset in publisher.datasets:
            for idx, activity in enumerate(dataset.activities):
                if dataset.name not in current_data_results or \
                    idx not in current_data_results[dataset.name] or \
                    current_data_results[dataset.name][idx] is False:
                    continue

                explanation, score = test_participating_org_refs(org.registry_slug, activity.etree, self_refs)

                if score is None:
                    score = 'not relevant'

                writer.writerow({
                    'dataset': dataset.name,
                    'identifier': activity.id,
                    'index': idx,
                    'result': str(score),
                    'hierarchy': activity.etree.get('hierarchy', '1'),
                    'explanation': explanation,
                })


def networked_data_part_3(org, snapshot_date, test_name, current_data_results):
    """Calculate scores for Networked Data part 3: proportion transactions w/receivers
    
    Part 3 of the Networked Data scores each activity according to how many of its
    transactions have valid receiving organisations listed. The score per activity is
    the proportion of valid transactions among assessable transactions.
    
    :param org: The organisation to be processed.
    :type org: iatidq.models.Organisation
    :param snapshot_date: The date of the data snapshot/download to use.
    :type snapshot_date: str (in YYYY-MM-DD format)
    :param test_name: The test name
    :type test_name: str
    :param current_data_results: All of the organisation's activities, grouped by
        dataset slug, indicating whether the activity is current or not.
    :type current_data_results: dictionary<dataset-slug, dictionary<activity-index, boolean>>
    """

    output_filepath = join(current_app.config.get('IATI_RESULT_PATH'),
                           snapshot_date, 
                           org.organisation_code,
                           utils.slugify(test_name) + '.csv')

    snapshot_xml_path = join(current_app.config.get('IATI_DATA_PATH'), snapshot_date)

    # get an IATIKIT Publisher object for the organisation being processed
    publisher = iatikit.data(snapshot_xml_path).publishers.get(org.registry_slug)

    fieldnames = ['dataset', 'identifier', 'index', 
                  'result', 'hierarchy', 'explanation']
    
    
    # we create three lists of publishers, or publisher prefixes, which are used to 
    # check the validity of the receiver-org refs; do that here so it's just done once
    org_id_prefixes = set(process_orgid())  # list of prefixes, except XM-DAC
    _, publishers_by_ident = process_publishers() 
    publisher_ids = set(publishers_by_ident)  # list of publishers on Registry
    xm_dac_codes = set(process_sector())  # list of acceptable XM-DAC codes


    with open(output_filepath, 'w') as handler:
        writer = csv.DictWriter(handler, fieldnames=fieldnames)
        writer.writeheader()

        for dataset in publisher.datasets:
            for idx, activity in enumerate(dataset.activities):
                # this test only applies to activities which are "current". "current" is
                # defined as: an activity that was in implementation, had transactions
                # or ended in the last 12 months
                if not (dataset.name in current_data_results and \
                        idx in current_data_results[dataset.name] and \
                        current_data_results[dataset.name][idx] == 1):
                    continue

                # if activity status code is not in [2, 3, 4] then skip
                activity_status_codes = activity.etree.xpath('activity-status/@code')
                if len(activity_status_codes) > 0 and \
                    activity_status_codes[0] not in ['2', '3', '4']:
                    continue

                transactions = activity.etree.xpath('transaction')

                # if an activity has no transactions, it shouldn't be counted
                # when determining proportion of passing activities 
                if len(transactions) == 0:
                    explanation = f'No transactions for this activity'
                    score = None
                else:
                    explanation, score = calc_networked_data_3_activity_score(org, 
                                                                              transactions,
                                                                              org_id_prefixes,
                                                                              publisher_ids,
                                                                              xm_dac_codes)

                writer.writerow({
                    'dataset': dataset.name,
                    'identifier': activity.id,
                    'index': idx,
                    'result': str(score),
                    'hierarchy': activity.etree.get('hierarchy', '1'),
                    'explanation': explanation,
                })


def calc_networked_data_3_activity_score(org, transactions, org_id_prefixes, 
                                         publisher_ids, xm_dac_codes):
    """Calculates score for part 3 of Networked data indicator for single activity"""

    # make a set of the organisation's self-references, which are to be excluded
    self_refs = set(org.self_ref.split(",")) if org.self_ref else set()

    total_transactions_assessed = 0
    receivers_w_narratives = 0
    receivers_w_valid_prefix = 0
    receivers_w_known_id = 0
    receivers_w_xm_dac = 0

    for transaction in transactions:

        # extract the data values the tests query
        receiver_orgs_refs = transaction.xpath("receiver-org/@ref")
        narrative_content = ''.join([k.strip() for k in 
                                    transaction.xpath('receiver-org/narrative/text()')])        

        # pre-assessment exclusions:

        # skip transactions which state receiver is current organisation
        if len(receiver_orgs_refs) > 0 and receiver_orgs_refs[0] in self_refs:
            continue
        
        # skip transactions which are not of type 2 or 3
        transaction_types = transaction.xpath("transaction-type/@code")
        if len(transaction_types) > 0 and transaction_types[0] not in ['2', '3']:
            continue


        # all pre-assessment exclusions now applied; so this transaction is assessable
        total_transactions_assessed += 1

        # to pass, either: it has some text in a <narrative> element. since the
        # <narrative> element can be repeated, this checks at least one has some content
        if len(narrative_content) > 0:
            receivers_w_narratives += 1            
            continue  # since we've passed the test, move to next transaction

        # if there is no receiver org ID, move on; this transaction fails, because
        # it has no org ID nor any name/narrative (transactions with narratives already)
        # handled
        if len(receiver_orgs_refs) == 0:
            continue  

        # get the receiver org id
        receiver_org_id = receiver_orgs_refs[0]

        # or: the receiver org ID must be a valid organisation ID; there are three
        # ways the ID is counted valid              

        # 1. the receiver organisation ID starts with a valid agency code
        if any([receiver_org_id.startswith(org_id) for org_id in org_id_prefixes]):
            receivers_w_valid_prefix += 1
            continue

        # 2. the receiver org ID is an existing IATI publisher on Registry
        if receiver_org_id in publisher_ids:
            receivers_w_known_id += 1
            continue

        # 3. the receiver org ID is one of the acceptable XM-DAC codes
        if receiver_org_id in xm_dac_codes:
            receivers_w_xm_dac += 1
    
    if total_transactions_assessed == 0:
        return 'No relevant transactions to assess', None
    
    passing_transactions = receivers_w_narratives + receivers_w_valid_prefix + \
                           receivers_w_known_id + receivers_w_xm_dac
    score = passing_transactions / total_transactions_assessed
    explanation = 'score: {a} (passing transactions) / {b} (total transactions assessed)'.format(
            a=(passing_transactions),
            b=total_transactions_assessed)
    
    # this alternative explanation for score breaks down the valid receivers according
    # to which test they passed; it's useful for debugging, but it is potentially 
    # misleading, inasmuch as when a transaction has both a narrative and a valid 
    # receiver reference, it will only be listed as having a valid narrative, which
    # may be confusing for the end user. 
            #f'score: ({receivers_w_narratives} (receivers w/narrative) + ' \
            #f'{receivers_w_valid_prefix} (receivers w/prefix) + ' \
            #f'{receivers_w_known_id} (receivers w/known ID) + ' \
            #f'{receivers_w_xm_dac} (receivers w/XM-DAC)) / {total_transactions_assessed}'

    
    return explanation, score
        







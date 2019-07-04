import csv
from glob import glob
from os.path import dirname, exists, join

from flask import current_app
from bdd_tester import BDDTester

from iatidataquality import db
from iatidq.models import AggregateResult, Test


def load_tests():
    """Load the index tests."""
    base_path = join(dirname(current_app.root_path),
                     'index_indicator_definitions', 'test_definitions')
    step_definitions = join(base_path, 'step_definitions.py')
    feature_filepaths = glob(join(base_path, '*', '*.feature'))
    tester = BDDTester(step_definitions)
    all_tests = [t for feature_filepath in feature_filepaths
                 for t in tester.load_feature(feature_filepath).tests]

    # Remove the current data condition from tests.
    for test in all_tests:
        test.steps = [x for x in test.steps
                      if not (x.step_type == 'given' and
                              x.text == 'the activity is current')]

    return all_tests


def load_current_data_test():
    """Load the current data test."""
    base_path = join(dirname(current_app.root_path),
                     'index_indicator_definitions', 'test_definitions')
    step_definitions = join(base_path, 'step_definitions.py')
    tester = BDDTester(step_definitions)
    return tester.load_feature(
        join(base_path, 'current_data.feature')).tests[0]


def load_current_data_results(org, snapshot_result_path):
    test = load_current_data_test()

    current_data_results = {}
    current_data_filepath = join(snapshot_result_path, org.registry_slug,
                                 slugify(test.name) + '.csv')
    with open(current_data_filepath) as handler:
        data = csv.DictReader(handler)
        for row in data:
            idx = int(row['index'])
            dataset = row['dataset']
            if dataset not in current_data_results:
                current_data_results[dataset] = {}
            current_data_results[dataset][idx] = row['result'] == 'pass'
    return current_data_results


def slugify(some_text):
    """Return a slugified version of an input string."""
    def safe_char(char):
        return char.lower() if char.isalnum() else '_'
    return ''.join(safe_char(char) for char in some_text).strip('_')


def run_test(test, publisher, output_path, test_condition, **kwargs):
    """Run test for a given publisher, and output results to a CSV."""
    result_lookup = {True: 'pass', False: 'fail', None: 'not relevant'}
    fieldnames = ['dataset', 'identifier', 'index', 'result',
                  'hierarchy', 'explanation']
    tags = test.tags + test.feature.tags
    if 'iati-activity' not in tags and 'iati-organisation' not in tags:
        # Skipping test (it's not tagged as activity or organisation level)
        return None

    with open(output_path, 'w') as handler:
        writer = csv.DictWriter(handler, fieldnames=fieldnames)
        writer.writeheader()
        if 'iati-activity' in tags:
            if test_condition:
                items = publisher.activities.where(xpath=test_condition)
            else:
                items = publisher.activities
        elif 'iati-organisation' in tags:
            items = publisher.organisations
        for item in items:
            result, explanation = test(item.etree, bdd_verbose=True, **kwargs)
            hierarchy = item.etree.get('hierarchy')
            if not hierarchy:
                hierarchy = '1'
            writer.writerow({
                'dataset': item.dataset.name,
                'identifier': item.id,
                'index': item.etree.getparent().index(item.etree),
                'result': result_lookup.get(result),
                'hierarchy': hierarchy,
                'explanation': str(explanation) if not result else '',
            })


def summarize_results(org, snapshot_result_path, all_tests,
                      current_data_results=None):
    aggregateresulttype = 2 if current_data_results else 1
    for test in all_tests:
        t = Test.where(description=test.name).first()
        test_id = t.id
        result_filepath = join(snapshot_result_path, org.registry_slug,
                               slugify(test.name) + '.csv')
        if not exists(result_filepath):
            continue
        with open(result_filepath) as handler:
            dataset = None
            for row in csv.DictReader(handler):
                if dataset is None:
                    dataset_test_results = {}
                    dataset = row['dataset']
                elif dataset != row['dataset']:
                    save_summary(dataset, dataset_test_results, test_id,
                                 org, aggregateresulttype)
                    dataset_test_results = {}
                    dataset = row['dataset']
                hierarchy = row['hierarchy']
                if hierarchy not in dataset_test_results:
                    dataset_test_results[hierarchy] = {
                        'pass': 0,
                        'fail': 0,
                    }
                result = row['result']
                if result == 'not relevant':
                    continue
                idx = int(row['index'])
                if (current_data_results and
                    current_data_results.get(dataset, {}).get(
                        idx, 'not relevant') == 'fail'):
                    continue
                dataset_test_results[hierarchy][result] += 1
            if dataset is not None:
                save_summary(dataset, dataset_test_results, test_id,
                             org, aggregateresulttype)


def save_summary(dataset, dataset_test_results, test_id, org,
                 aggregateresulttype):
    for hierarchy, scores in dataset_test_results.items():
        total = sum(scores.values())
        if total == 0:
            continue
        results_data = 100. * scores['pass'] / total

        ar = AggregateResult()
        ar.package_name = dataset.decode()
        ar.organisation_id = org.id
        ar.aggregateresulttype_id = aggregateresulttype
        ar.test_id = test_id
        ar.result_hierarchy = hierarchy
        ar.results_data = results_data
        ar.results_num = total

        with db.session.begin():
            db.session.add(ar)

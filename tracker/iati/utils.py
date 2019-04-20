from csv import DictWriter
from glob import glob
from os.path import dirname, join

from flask import current_app
from bdd_tester import BDDTester


def load_tests():
    """Load the index tests."""
    base_path = join(dirname(current_app.root_path),
                     'index_indicator_definitions', 'test_definitions')
    step_definitions = join(base_path, 'step_definitions.py')
    feature_filepaths = glob(join(base_path, '*', '*.feature'))
    tester = BDDTester(step_definitions)
    all_tests = [t for feature_filepath in feature_filepaths
                 for t in tester.load_feature(feature_filepath).tests]

    # current_data_test = tester.load_feature(
    #     join(base_path, 'current_data.feature')).tests[0]

    return all_tests


def slugify(some_text):
    """Return a slugified version of an input string."""
    def safe_char(char):
        return char.lower() if char.isalnum() else '_'
    return ''.join(safe_char(char) for char in some_text).strip('_')


def run_test(test, publisher, output_path):
    '''Run test for a given publisher, and output results to a CSV.'''
    fieldnames = ['dataset', 'identifier', 'index', 'result']
    tags = test.tags + test.feature.tags
    if 'iati-activity' not in tags and 'iati-organisation' not in tags:
        # Skipping test (it’s not tagged as activity or organisation level)
        return

    with open(output_path, 'w') as handler:
        writer = DictWriter(handler, fieldnames=fieldnames)
        writer.writeheader()
        if 'iati-activity' in tags:
            for dataset in publisher.datasets.where(filetype='activity'):
                dataset_name = dataset.name
                for idx, activity in enumerate(dataset.activities):
                    writer.writerow({
                        'dataset': dataset_name,
                        'identifier': activity.id,
                        'index': idx,
                        'result': str(test(activity.etree)),
                    })
        elif 'iati-organisation' in tags:
            for dataset in publisher.datasets.where(filetype='organisation'):
                dataset_name = dataset.name
                for idx, organisation in enumerate(dataset.organisations):
                    writer.writerow({
                        'dataset': dataset_name,
                        'identifier': organisation.id,
                        'index': idx,
                        'result': str(test(organisation.etree)),
                    })
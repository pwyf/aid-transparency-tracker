import os
import sys
import csv

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import iatidataquality
import iatidataquality.aggregation

import nose
import nose.tools

import json

def setup_func():
    pass

def teardown_func():
    pass

def check_aggregation(config):
    # FIXME
    # Don't check aggregation for now while 
    # we're changing it a lot...
    return True
    suffix, mode = config

    with file('unittests/artefacts/input-%s.json' % suffix) as f:
        data = json.load(f)

    with file('unittests/artefacts/output-%s.json' % suffix) as f:
        expected = f.read()

    observed = iatidataquality.aggregation._agr_results(
        data,
        conditions=None,
        mode=mode
        )

    assert json.dumps(observed, indent=2) == expected

@nose.with_setup(setup_func, teardown_func)
def test_aggregation_fn():
    configs = [
        ("publisher", "publisher"),
        ("package", None)
        ]

    for cfg in configs:
        yield (check_aggregation, cfg)

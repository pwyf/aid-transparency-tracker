import os
import pytest

from flask import Flask

from lxml import etree

from beta.infotest import process_orgid, process_publishers, process_sector
from beta.infotest import calc_networked_data_3_activity_score


class OrganisationMock:
    self_ref = ''

    def __init__(self, self_references_as_str=""):
        self.self_ref = self_references_as_str

class TestIndicatorNetworkedData:   

    @pytest.fixture()
    def flask_app(self):
        app = Flask('pytest_app', root_path=os.path.join(os.getcwd(), 'unittests'))
        app.config.from_pyfile(os.path.join('resources',
                                            'mock_flask_app_config.py'))
        return app


    @pytest.fixture()
    def org_id_prefixes(self, flask_app):
        with flask_app.app_context():
            org_ids = process_orgid()
        return set(org_ids)
    
    @pytest.fixture()
    def publishers_list(self, flask_app):
        with flask_app.app_context():
            _, publishers_by_ident =  process_publishers()
            publisher_ids = set(publishers_by_ident) 
        return set(publisher_ids)

    @pytest.fixture()
    def xm_dac_codes(self, flask_app):
        with flask_app.app_context():
            xm_dac_codes = set(process_sector())
        return set(xm_dac_codes)

    def test_activity_level_score_transactions_w_names(self, 
                                                       org_id_prefixes,
                                                       publishers_list,
                                                       xm_dac_codes):
        
        # test file `test_be-dgd-2021_1.xml` has been edited to test three conditions:
        # activity 1: 0 / 4 transactions have receiver names/refs: expected score: 0
        # activity 2: 3 / 4 transactions have receiver names, none w/refs: expected score: 0.75
        # activity 3: 4 / 4 transactions have receiver names, none w/refs: expected score: 1
        # activity 4: 2 / 5 transactions have receiver names, 1/5 valid ref: expected score: 0.6
        expected_results = [0, 0.75, 1, 0.6]

    
        org = OrganisationMock("XM-DAC-2-10")

        tree = etree.parse(os.path.join("unittests", "artefacts", "xml", "test_01_be-dgd-2021_1.xml"))

        activities = tree.xpath("iati-activity")

        for idx, activity in enumerate(activities):

            transactions = activity.xpath("transaction")

            explanation, score = calc_networked_data_3_activity_score(org, 
                                                                      transactions,
                                                                      org_id_prefixes,
                                                                      publishers_list,
                                                                      xm_dac_codes)
        
            assert score == expected_results[idx]
        

    def test_activity_level_score_transactions_w_refs(self, 
                                                      org_id_prefixes,
                                                      publishers_list,
                                                      xm_dac_codes):
        
        # test file `test_be-dgd-2021_1.xml` has been edited to test three conditions:
        # activity 1: 4 / 4 transactions have receiver refs w/valid prefix: expected score: 1
        # activity 2: 4 / 4 transactions have receiver publisher IDs in Registry but invalid prefixes: score: 1
        # activity 3: 2 / 4 transactions have receiver publisher IDs in Registry but invalid prefixes: score: 0.5
        # activity 4: 3 / 5 transactions have receiver w/valid XM-DAC codes: score: 0.6
        expected_results = [1, 1, 0.5, 0.6]
    
        org = OrganisationMock("XM-DAC-2-10")

        tree = etree.parse(os.path.join("unittests", "artefacts", "xml", "test_02_be-dgd-2021_1.xml"))

        activities = tree.xpath("iati-activity")

        for idx, activity in enumerate(activities):

            transactions = activity.xpath("transaction")

            explanation, score = calc_networked_data_3_activity_score(org, 
                                                                      transactions,
                                                                      org_id_prefixes,
                                                                      publishers_list,
                                                                      xm_dac_codes)
        
            assert score == expected_results[idx]
            

    def test_activity_level_score_excludes_self_ref(self, 
                                                    org_id_prefixes,
                                                    publishers_list,
                                                    xm_dac_codes):
        
        # test file `test_be-dgd-2021_1.xml` has been edited to test three conditions:
        # activity 1: 3 / 4 transactions have receiver names; one excluded due to self-ref: expected score: 1
        expected_results = [("score: 3 (passing transactions) / 3 (total transactions assessed)", 1),
                            ("No relevant transactions to assess", 'not relevant')]
    
        org = OrganisationMock("XM-DAC-2-10")

        tree = etree.parse(os.path.join("unittests", "artefacts", "xml", "test_03-be-dgd-excludes-self-refs.xml"))

        activities = tree.xpath("iati-activity")

        for idx, activity in enumerate(activities):

            transactions = activity.xpath("transaction")

            explanation, score = calc_networked_data_3_activity_score(org, 
                                                                      transactions,
                                                                      org_id_prefixes,
                                                                      publishers_list,
                                                                      xm_dac_codes)
        
            assert explanation == expected_results[idx][0]
            assert score == expected_results[idx][1]


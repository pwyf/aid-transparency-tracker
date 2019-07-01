from os.path import join

from flask import current_app
import iatikit

from . import utils
from iatidataquality import db
from iatidq.models import AggregateResult, Test


def get_current_countries(publisher, current_data):
    country_codes = []

    for activity in publisher.activities:
        idx = activity.etree.getparent().index(activity.etree)
        if current_data[activity.dataset.name][idx] is False:
            continue
        country_codes += activity.etree.xpath('recipient-country/@code')
        country_codes = list(set(country_codes))
    return country_codes


def country_strategy_or_mou(org, snapshot_date, current_data_results):
    def save_result(org_id, test_id, aggregateresult_type, score, total):
        ar = AggregateResult()
        ar.organisation_id = org_id
        ar.aggregateresulttype_id = aggregateresult_type
        ar.test_id = test_id
        ar.result_hierarchy = 0
        ar.results_data = score
        ar.results_num = total
        with db.session.begin():
            db.session.add(ar)

    iati_result_path = current_app.config.get('IATI_RESULT_PATH')
    snapshot_result_path = join(iati_result_path, snapshot_date)

    iati_data_path = current_app.config.get('IATI_DATA_PATH')
    snapshot_xml_path = join(iati_data_path, snapshot_date)
    publisher = iatikit.data(snapshot_xml_path).publishers.get(org.registry_slug)

    current_country_codes = get_current_countries(publisher, current_data_results)

    if current_country_codes == []:
        return

    country_strategies = []
    for activity in publisher.activities:
        idx = activity.etree.getparent().index(activity.etree)
        if current_data_results[activity.dataset.name][idx] is False:
            continue
        mous = activity.etree.xpath('document-link[category/@code="A09"]')
        if mous == []:
            continue
        country_strategies += activity.etree.xpath('recipient-country/@code')
        country_strategies = list(set(country_strategies))

    for organisation in publisher.organisations:
        country_strategies += organisation.etree.xpath('document-link[category/@code="B03"]/recipient-country/@code')
        country_strategies += organisation.etree.xpath('document-link[category/@code="B13"]/recipient-country/@code')
        country_strategies = list(set(country_strategies))

    country_strategies = [x for x in country_strategies
                          if x in current_country_codes]

    total = len(current_country_codes)
    score = 100. * len(country_strategies) / len(current_country_codes)

    test = Test.where(description=u'Strategy (country/sector) or Memorandum of Understanding').first()
    save_result(org.id, test.id, 1, score, total)
    save_result(org.id, test.id, 2, score, total)


#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import jsonify, render_template, flash, request, url_for
from flask_login import current_user

from . import app, usermanagement
from iatidq import dqorganisations, dqtests, dqindicators, dqcodelists, models
from sample_work import sample_work, test_mapping
from sample_work import db as sample_db


def memodict(f):
    """ Memoization decorator for a function taking a single argument """
    class memodict(dict):
        def __missing__(self, key):
            ret = self[key] = f(key)
            return ret
    return memodict().__getitem__

@memodict
def get_test_info(test_id):
    return dqtests.tests(test_id)

@memodict
def get_test_indicator_info(test_id):
    return dqindicators.testIndicator(test_id)

@memodict
def get_org_info(organisation_id):
    return models.Organisation.find_or_fail(organisation_id)

def get_response(kind, response):
    kind_data = test_mapping.kind_to_status[kind]
    response_data = kind_data.get(response)

    if response_data is not None:
        return response_data
    return {
              "text:": "not yet sampled",
              "button": "not yet sampled",
              "icon": "info-sign",
              "class": "warning",
            }

def kind_to_list(kind):
    kind_data = test_mapping.kind_to_status[kind]
    kind_data = map(lambda x: (x[1]), kind_data.items())
    return kind_data

def make_sample_json(work_item):
    def get_docs(xml_strings):

        def get_doc_from_xml(xml):
            if xml == None:
                return []
            document_category_codes = dqcodelists.reformatCodelist('DocumentCategory')
            document_links = sample_work.DocumentLinks(work_item["xml_data"],
                                               document_category_codes)
            docs = [ dl.to_dict() for dl in document_links.get_links() ]
            return docs

        data = [get_doc_from_xml(xml) for xml in xml_strings]
        return data[0]+data[1]

    def get_res(xml_strings):
        def get_res_from_xml(xml):
            if xml == None:
                return []
            results = sample_work.Results(work_item["xml_data"])
            res = [ ln.to_dict() for ln in results.get_results() ]
            return res

        data = [get_res_from_xml(xml) for xml in xml_strings]
        return data[0]+data[1]

    def get_locs(xml_strings):
        def get_loc_from_xml(xml):
            if xml == None:
                return []
            locations = sample_work.Locations(work_item["xml_data"])
            locs = [ ln.to_dict() for ln in locations.get_locations() ]
            return locs

        data = [get_loc_from_xml(xml) for xml in xml_strings]
        return data[0]+data[1]

    def get_conds(xml_strings):
        def get_cond_from_xml(xml):
            if xml == None:
                return []
            conditions = [sample_work.Conditions(work_item["xml_data"]).get_conditions()]
            return conditions
        data = [get_cond_from_xml(xml) for xml in xml_strings]
        return data[0]+data[1]

    xml_strings = [work_item["xml_data"],
                   work_item["xml_parent_data"]]
    docs = get_docs(xml_strings)


    if work_item["test_kind"] == "location":
        locs = get_locs(xml_strings)
    else:
        locs = []

    if work_item["test_kind"] == "result":
        res = get_res(xml_strings)
    else:
        res = []

    if work_item["test_kind"] == "conditions":
        conditions = get_conds(xml_strings)
    else:
        conditions = []

    activity_info = sample_work.ActivityInfo(work_item["xml_data"])

    work_item_test = get_test_info(work_item["test_id"])
    work_item_indicator = get_test_indicator_info(work_item["test_id"])
    work_item_org = get_org_info(work_item["organisation_id"])

    xml = work_item['xml_data']

    data = { "sample": {
                "iati-identifier": work_item["activity_id"],
                "documents": docs,
                "locations": locs,
                "results": res,
                "conditions": conditions,
                "sampling_id": work_item["uuid"],
                "test_id": work_item["test_id"],
                "organisation_id": work_item["organisation_id"],
                "activity_title": activity_info.title,
                "activity_description": activity_info.description,
                "test_kind": work_item["test_kind"],
                "xml": xml,
            },
            "headers": {
                "test_name": work_item_test.name,
                "test_description": work_item_test.description,
                "indicator_name": work_item_indicator.description,
                "indicator_description": work_item_indicator.longdescription,
                "organisation_name": work_item_org.organisation_name,
                "organisation_code": work_item_org.organisation_code,
            },
            "buttons": kind_to_list(work_item["test_kind"]),
            "unsure": work_item.get("unsure"),
            "response": {}
        }
    if 'response' in work_item:
        data['response'] = get_response(work_item["test_kind"],
                    work_item['response'])

    return data

# quick fix to make the sample list load faster
# (since that page is used a lot)
def make_simple_sample_json(work_item):
    work_item_org = get_org_info(work_item["organisation_id"])
    work_item_test = get_test_info(work_item["test_id"])

    data = { "sample": {
                "sampling_id": work_item["uuid"],
                "test_id": work_item["test_id"],
            },
            "headers": {
                "test_description": work_item_test.description,
                "organisation_name": work_item_org.organisation_name,
                "organisation_code": work_item_org.organisation_code,
            },
            "unsure": work_item["unsure"],
            "response": {}
        }
    if 'response' in work_item:
        data['response'] = get_response(work_item["test_kind"],
                    work_item['response'])

    return data

@app.route("/api/sampling/process/", methods=['POST'])
@app.route("/api/sampling/process/<response>", methods=['POST'])
@usermanagement.perms_required()
def api_sampling_process(response):
    data = request.form
    try:
        unsure = 'unsure' in data
        assert 'sampling_id' in data
        work_item_uuid = data["sampling_id"]
        response = int(response)

        create_or_update = sample_db.save_response(work_item_uuid, response, unsure)
        if create_or_update == "create":
            flash('Created response for that sample', 'success')
        else:
            flash('Updated response for that sample', 'success')
        return 'OK'
    except Exception as e:
        return 'ERROR'

@app.route("/api/sampling/")
@app.route("/api/sampling/<uuid>/")
@usermanagement.perms_required()
def api_sampling(uuid=None):
    if not uuid:
        try:
            work_items = sample_db.work_item_generator()
            results = make_sample_json(work_items)
        except sample_db.NoMoreSamplingWork:
            results = {
                "error": "Finished"
                }
        #except:
        #    results = {
        #        "error": "Unknown"
        #        }
    else:
        def make_wi(uuid):
            return sample_db.read_db_response(uuid=uuid)[0]
        results = make_sample_json(make_wi(uuid))
    return jsonify(results)


@app.route("/sampling/")
@app.route("/sampling/<uuid>/")
@usermanagement.perms_required()
def sampling(uuid=None):
    if uuid:
        next_url = url_for('sampling_list')
        api_sampling_url = url_for('api_sampling', uuid=uuid)
    else:
        next_url = ""
        api_sampling_url = url_for('api_sampling')

    return render_template("sampling.html",
         admin=usermanagement.check_perms('admin'),
         loggedinuser=current_user,
         next_url=next_url,
         api_process_url=url_for('api_sampling_process'),
         api_sampling_url=api_sampling_url)

@app.route("/sampling/list/")
@usermanagement.perms_required()
def sampling_list():
    page_size = 50

    current_page = int(request.args.get('page', 1))
    offset = (current_page - 1) * page_size
    limit = page_size

    total_samples = sample_db.count_all_samples()
    total_pages = total_samples / page_size + 1

    samples = []
    for wi in sample_db.read_db_response(offset=offset, limit=limit):
        samples.append(make_simple_sample_json(wi))

    return render_template(
        "sampling_list.html",
        admin=usermanagement.check_perms('admin'),
        loggedinuser=current_user,
        samples=samples,
        total_pages=total_pages,
        current_page=current_page)

@app.route("/sampling/orglist/")
@usermanagement.perms_required()
def sampling_orglist():
    orgtests = sample_db.get_total_results()
    data = sample_db.get_summary_org_test(orgtests)
    return render_template("sampling_org_tests.html",
         admin=usermanagement.check_perms('admin'),
         loggedinuser=current_user,
         orgtests=data)

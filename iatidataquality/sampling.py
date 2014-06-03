
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import login_required, current_user

from iatidataquality import app
from iatidataquality import db
import usermanagement

from iatidq import dqusers, util, dqorganisations

import unicodecsv
import json

import lxml.etree

import os
from sqlite3 import dbapi2 as sqlite
from sample_work import sample_work
from sample_work import db as sample_db

samplingdata = [{'iati-identifier': 'GB-123456',
                 'data': [{
                    'name': "Mid-term evaluation document for some project",
                    'url': "http://dfid.gov.uk/iati/gb-123456-midtermevaluation.doc",
                    'categories': ['Evaluation'],
                    },
                    {
                    'name': "Evaluation document for some project",
                    'url': "http://dfid.gov.uk/iati/gb-123456-evaluation.doc",
                    'categories': ['Evaluation'],
                    },
                    ],
                 'sampling_id': '1',
                 },
                {'iati-identifier': 'GB-123456',
                 'data': [{
                    'name': "Mid-term evaluation document for some project",
                    'url': "http://dfid.gov.uk/iati/gb-123456-midtermevaluation.doc",
                    'categories': ['Evaluation'],
                    },
                    {
                    'name': "Evaluation document for some project",
                    'url': "http://dfid.gov.uk/iati/gb-123456-evaluation.doc",
                    'categories': ['Evaluation'],
                    },
                    ],
                 'sampling_id': '2',
                 }]

def make_sample_json(work_item):
    document_links = sample_work.DocumentLinks(work_item["xml_data"])
    data_section = [ dl.to_dict() for dl in document_links.get_links() ]
    activity_info = sample_work.ActivityInfo(work_item["xml_data"])

    return {
        "iati-identifier": work_item["activity_id"],
        "data": data_section,
        "sampling_id": work_item["uuid"],
        "test_id": work_item["test_id"],
        "organisation_id": work_item["organisation_id"],
        "activity_title": activity_info.title,
        "activity_description": activity_info.description,
        "test_kind": work_item["test_kind"],
        }


@app.route("/api/sampling/process/<response>", methods=['POST'])
def api_sampling_process(response):
    data = request.form
    try:
        assert 'sampling_id' in data
        work_item_uuid = data["sampling_id"]
        response = int(response)
        filename = os.path.join(os.path.dirname(__file__), 
                                '../sample_work.db')

        database = sqlite.connect(filename)
        c = database.cursor()
        
        c.execute('''insert into sample_result ("uuid", "response")
                       values (?, ?);''', (work_item_uuid, response))
        database.commit()
        return 'OK'
    except Exception as e:
        return 'ERROR'

def work_item_generator():
    filename = os.path.join(os.path.dirname(__file__), 
                            '../sample_work.db')
    for wi in sample_db.read_db(filename):
        yield make_sample_json(wi)

work_items = work_item_generator()

@app.route("/api/sampling/")
def api_sampling():
    return json.dumps(work_items.next(), indent=2)

@app.route("/sampling/")
#@usermanagement.perms_required()
def sampling():
    return render_template("sampling.html",
         admin=usermanagement.check_perms('admin'),
         loggedinuser=current_user,
         samplingdata=samplingdata)

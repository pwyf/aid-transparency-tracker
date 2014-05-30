
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


@app.route("/api/sampling/")
def api_sampling():
    return json.dumps(samplingdata, indent=2)

@app.route("/sampling/")
#@usermanagement.perms_required()
def sampling():
    return render_template("sampling.html",
         admin=usermanagement.check_perms('admin'),
         loggedinuser=current_user,
         samplingdata=samplingdata)

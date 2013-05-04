
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
from sqlalchemy import func
from datetime import datetime

from iatidataquality import app
from iatidataquality import db

from iatidq import dqdownload, dqregistry, dqindicators, dqorganisations, dqpackages
import usermanagement

@app.route("/registry/refresh/")
@usermanagement.perms_required()
def registry_refresh():
    dqregistry.refresh_packages()
    return "Refreshed"

@app.route("/registry/download/")
@usermanagement.perms_required()
def registry_download():
    dqdownload.run()
    return "Downloading"


#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file

from iatidataquality import app
from iatidataquality import db

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

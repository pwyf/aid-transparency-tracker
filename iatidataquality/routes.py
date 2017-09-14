
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, \
    session, redirect, url_for, escape, Response, abort, send_file
from flask_login import current_user

from iatidataquality import app
from iatidataquality import db
import usermanagement

@app.route("/")
def home():
    return render_template("dashboard.html",
             admin=usermanagement.check_perms('admin'),
             intro_html=app.config.get('INTRO_HTML'),
             loggedinuser=current_user)

@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html",
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html", error=e,
             error_class=e.__class__.__name__,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user), 500

@app.route('/about/')
def about():
    return render_template("about.html", 
                           loggedinuser=current_user, 
                           admin=usermanagement.check_perms('admin'))


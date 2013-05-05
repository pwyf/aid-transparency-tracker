
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

from iatidataquality import app
from iatidataquality import db
import usermanagement

from iatidq import dqusers

import unicodecsv

@app.route("/users/")
@app.route("/user/<username>/")
@usermanagement.perms_required()
def users(username=None):
    if username:
        user=dqusers.user_by_username(username)
        return render_template("user.html", user=user)
    else:
        users=dqusers.user()
        return render_template("users.html", users=users)

@app.route("/users/new/", methods=['POST', 'GET'])
@app.route("/users/<username>/edit/", methods=['POST', 'GET'])
@usermanagement.perms_required()
def users_edit(username=None):
    if username:
        user = dqusers.user_by_username(username)
        if request.method == 'POST':
            return "handling edit"
            if aggregationtype:
                flash('Successfully updated user.', 'success')
            else:
                aggregationtype = {}
                flash('Could not update user.', 'error')
    else:
        if request.method == 'POST':
            user = dqusers.addUser({
                    'username': request.form['username'],
                    'password': request.form['password'],
                    'name': request.form['name'],
                    'email_address': request.form['email_address']
                    })
            if user:
                flash('Successfully added new user', 'success')
            else:
                flash('Could not add user user', 'error')
        else:
            user = {}

    return render_template("users_edit.html", 
                           user=user)

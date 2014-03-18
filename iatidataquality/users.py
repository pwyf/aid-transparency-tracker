
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

from iatidq import dqusers, util

import unicodecsv

@app.route("/users/")
@app.route("/user/<username>/")
@usermanagement.perms_required()
def users(username=None):
    if username:
        return redirect(url_for('users_edit', username=username))
    else:
        users=dqusers.user()
        return render_template("users.html", users=users,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

def returnOrNone(value):
    if (value ==''):
        return None
    return value

@app.route("/users/<username>/edit/addpermission/", methods=['POST'])
@usermanagement.perms_required()
def users_edit_addpermission(username):
    user = dqusers.user_by_username(username)
    data = {
        'user_id': user.id,
        'permission_name': request.form['permission_name'],
        'permission_method': returnOrNone(request.form['permission_method']),
        'permission_value': returnOrNone(request.form['permission_value'])
    }
    permission = dqusers.addUserPermission(data)
    if permission:
        return util.jsonify(permission.as_dict())
    else:
        return util.jsonify({"error": "Could not add permission"})

@app.route("/users/<username>/edit/deletepermission/", methods=['POST'])
@usermanagement.perms_required()
def users_edit_deletepermission(username):
    permission_id = request.form['permisison_id']
    permission = dqusers.deleteUserPermission(permission_id)
    if permission:
        return util.jsonify({"success": "Deleted permission"})
    else:
        return util.jsonify({"error": "Could not delete permission"})

@app.route("/users/new/", methods=['POST', 'GET'])
@app.route("/users/<username>/edit/", methods=['POST', 'GET'])
@usermanagement.perms_required()
def users_edit(username=None):
    user = {}
    permissions = {}

    if username:
        user = dqusers.user_by_username(username)
        permissions = dqusers.userPermissions(user.id)
        if request.method == 'POST':
            if user:
                user = dqusers.addUser({
                    'username': username,
                    'password': request.form['password'],
                    'name': request.form['name'],
                    'email_address': request.form['email_address'],
                    'organisation': request.form['organisation']
                    })
                flash('Successfully updated user.', 'success')
            else:
                user = {}
                flash('Could not update user.', 'error')
    else:
        if request.method == 'POST':
            user = dqusers.addUser({
                    'username': request.form['username'],
                    'password': request.form['password'],
                    'name': request.form['name'],
                    'email_address': request.form['email_address'],
                    'organisation': request.form['organisation']
                    })
            if user:
                flash('Successfully added new user', 'success')
            else:
                flash('Could not add user user', 'error')

    return render_template("users_edit.html", 
                           user=user,
                           permissions=permissions,
             admin=usermanagement.check_perms('admin'),
             loggedinuser=current_user)

@app.route("/users/<username>/delete/")
@usermanagement.perms_required()
def users_delete(username=None):
    if username:
        user = dqusers.deleteUser(username)
        flash('Successfully deleted user.', 'success')
    else:
        flash('No username provided.', 'error')
    return redirect(url_for('users'))


#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import render_template, flash, request, redirect, url_for
from flask_login import current_user

from . import usermanagement
from iatidq import dqusers, models, util


def get_users(username=None):
    if username:
        return redirect(url_for('users_edit', username=username))
    else:
        users = models.User.all()
        return render_template(
            "users.html", users=users,
            admin=usermanagement.check_perms('admin'),
            loggedinuser=current_user)


def returnOrNone(value):
    if (value == ''):
        return None
    return value


def users_edit_addpermission(username):
    user = models.User.where(username=username).first()
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


def users_edit_deletepermission(username):
    permission_id = request.form['permisison_id']
    permission = dqusers.deleteUserPermission(permission_id)
    if permission:
        return util.jsonify({"success": "Deleted permission"})
    else:
        return util.jsonify({"error": "Could not delete permission"})


def users_edit(username=None):
    user = {}
    permissions = {}

    if username:
        user = models.User.where(username=username).first()
        permissions = dqusers.userPermissions(user.id)
        if request.method == 'POST':
            if user:
                data = {
                    'username': username,
                    'password': request.form.get('password'),
                    'name': request.form['name'],
                    'email_address': request.form['email_address'],
                    'organisation': request.form['organisation']
                    }
                user = dqusers.updateUser(data)
                flash('Successfully updated user.', 'success')
            else:
                user = {}
                flash('Could not update user.', 'danger')
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
                return redirect(url_for('users_edit', username=user.username))
            else:
                flash('Could not add user', 'danger')

    organisations = models.Organisation.sort('organisation_name').all()
    return render_template("users_edit.html",
                           user=user,
                           permissions=permissions,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user,
                           organisations=organisations)


def users_delete(username=None):
    if username:
        dqusers.deleteUser(username)
        flash('Successfully deleted user.', 'success')
    else:
        flash('No username provided.', 'danger')
    return redirect(url_for('get_users'))

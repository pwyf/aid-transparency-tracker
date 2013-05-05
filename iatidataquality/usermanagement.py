
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file, current_app
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
from flask.ext.principal import Principal, Identity, AnonymousIdentity, \
     identity_changed, identity_loaded, Permission, RoleNeed, \
     UserNeed

from collections import namedtuple
from functools import partial, wraps
from iatidataquality import app
from iatidataquality import db
from iatidq import dqusers


users = [{
        'username': 'mark',
        'password': '1234',
        'name': 'Mark',
        'permissions': [{
            'permission_name': 'admin',
            'permission_method': 'full'
            }]
        },
        {
        'username': 'fred',
        'password': '1234',
        'name': 'Fred',
        'permissions': [{
            'permission_name': 'tests',
            'permission_method': 'edit',
            'permission_value': '1'
            },{
            'permission_name': 'tests',
            'permission_method': 'edit',
            'permission_value': '2'
            },{
            'permission_name': 'tests',
            'permission_method': 'edit',
            'permission_value': '3'
            }]
        }]
for user in users:
    dqusers.addUser(user)
    the_user = dqusers.user_by_username(user['username'])
    for permission in user['permissions']:
        
        permission["user_id"]=the_user.id
        dqusers.addUserPermission(permission)

principals = Principal(app)
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(id):
    return dqusers.user(id)

def role_permission(rolename):
    return Permission(RoleNeed(rolename))

TestNeed = namedtuple('test', ['method', 'value'])
EditTestNeed = partial(TestNeed, 'edit')

class EditTestPermission(Permission):
    def __init__(self, test_id):
        need = EditTestNeed(unicode(test_id))
        super(EditTestPermission, self).__init__(need)

OrganisationNeed = namedtuple('organisation', ['method', 'value'])
ViewOrganisationNeed = partial(OrganisationNeed, 'view')

class ViewOrganisationPermission(Permission):
    def __init__(self, organisation_code):
        need = ViewOrganisationNeed(unicode(organisation_code))
        super(ViewOrganisationPermission, self).__init__(need)

def check_perms(name, method=None, kwargs=None):
    #check to see if 
    if role_permission('admin').can():
        return True
    if (name == 'tests'):
        value = kwargs['id']
        if ((method=='edit') or (method=='delete')):
            return EditTestPermission(value).can()
    if (name == 'organisation'):
        if kwargs:
            value = kwargs['organisation_code']
            if (method=='view'):
                return ViewOrganisationPermission(value).can()
    return False

def perms_required(name=None, method=None, value=None):
    def wrap(f):
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            if not check_perms(name, method, kwargs):
                flash('You must log in to access that page.', 'error')
                return redirect(url_for('login', next=request.path))
            return f(*args, **kwargs)
        return wrapped_f
    return wrap

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user
    permissions = dqusers.userPermissions(identity.id)

    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))

    def set_permissions(permission):
        if (permission.permission_name=='tests' and permission.permission_method=='edit'):
            identity.provides.add(EditTestNeed(unicode(permission.permission_value)))
        if (permission.permission_name=='organisation' and permission.permission_method=='view'):
            identity.provides.add(ViewOrganisationNeed(unicode(permission.permission_value)))
        if (permission.permission_method=='role'):
            identity.provides.add(RoleNeed(permission.permission_name))

    for permission in permissions:
        set_permissions(permission)

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        user = dqusers.user_by_username(request.form["username"])
        if (user and user.check_password(request.form["password"])):
            remember = request.form.get("remember", "no") == "yes"
            if login_user(user, remember=remember):
                flash("Logged in!", "success")
                identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))
                return redirect(request.args.get("next") or url_for("home"))
            else:
                flash("Sorry, but you could not log in.", "error")
        else:
            flash(u"Invalid username or password.", "error")
    return render_template("login.html")

@app.route('/logout/')
@login_required
def logout():
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    flash('Logged out', 'success')
    return redirect(request.args.get('next') or '/')

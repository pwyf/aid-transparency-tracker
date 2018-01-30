
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from collections import namedtuple
from functools import partial, wraps

from flask import render_template, flash, request, session, redirect, url_for, current_app
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_principal import Principal, Identity, AnonymousIdentity, \
     identity_changed, identity_loaded, Permission, RoleNeed, \
     UserNeed

from . import app
from iatidq import dqusers, models, user_activity_types


principals = Principal(app)
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(id):
    return models.User.find(id)

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

EditOrganisationNeed = partial(OrganisationNeed, 'edit')

class EditOrganisationPermission(Permission):
    def __init__(self, organisation_code):
        need = EditOrganisationNeed(unicode(organisation_code))
        super(EditOrganisationPermission, self).__init__(need)

OrganisationFeedbackNeed = namedtuple('organisation_feedback',
                                      ['method', 'value'])
CreateOrganisationFeedbackNeed = partial(OrganisationFeedbackNeed, 'create')

class CreateOrganisationFeedbackPermission(Permission):
    def __init__(self, organisation_code):
        need = CreateOrganisationFeedbackNeed(unicode(organisation_code))
        super(CreateOrganisationFeedbackPermission, self).__init__(need)

class SurveyPermission(Permission):
    def __init__(self, name, method, value):
        need = (unicode(name), unicode(method), unicode(value))
        super(SurveyPermission, self).__init__(need)

def check_perms(name, method=None, kwargs=None):
    if role_permission('admin').can():
        return True

    restricted_methods = ['edit', 'delete', 'create']
    edit_methods =       ['edit', 'delete']

    if role_permission('super').can() and method not in restricted_methods:
        return True

    if (role_permission('super').can() and name=='survey_researcher'):
        return True

    if not name:
        return False

    if name == 'tests':
        value = kwargs['id']
        if method in edit_methods:
            return EditTestPermission(value).can()
        return False

    if name == 'organisation':
        if not kwargs:
            return False
        value = kwargs['organisation_code']
        if method == 'view':
            return ViewOrganisationPermission(value).can()
        if method == 'edit':
            return EditOrganisationPermission(value).can()
        return False

    if name == 'organisation_feedback':
        if not kwargs:
            return False
        value = kwargs['organisation_code']
        if method=='create':
            return CreateOrganisationFeedbackPermission(value).can()
        return False

    if name.startswith('survey'):
        if kwargs:
            value = kwargs['organisation_code']
            return SurveyPermission(unicode(name),
                                    unicode(method),
                                    unicode(value)).can()
        else:
            value = ""
            return SurveyPermission(name, method, value).can()

    return False

def perms_required(name=None, method=None, value=None):
    def wrap(f):
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            if not check_perms(name, method, kwargs):
                flash('You must log in to access that page.', 'danger')
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

    def set_survey_permissions(permission):
        identity.provides.add((unicode(permission.permission_name), unicode(permission.permission_method), unicode(permission.permission_value)))

    def set_permissions(permission):
        if (permission.permission_name=='tests' and permission.permission_method=='edit'):
            identity.provides.add(EditTestNeed(unicode(permission.permission_value)))
        if (permission.permission_name=='organisation' and permission.permission_method=='view'):
            identity.provides.add(ViewOrganisationNeed(unicode(permission.permission_value)))
        if (permission.permission_name=='organisation_feedback' and permission.permission_method=='create'):
            identity.provides.add(CreateOrganisationFeedbackNeed(unicode(permission.permission_value)))
        if (permission.permission_method=='role'):
            identity.provides.add(RoleNeed(permission.permission_name))
        if (permission.permission_name.startswith('survey')):
            set_survey_permissions(permission)

    #with db.session.begin():
    for permission in permissions:
        set_permissions(permission)

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        user = models.User.where(username=request.form["username"]).first()
        if (user and user.check_password(request.form["password"])):
            remember = request.form.get("remember", "no") == "yes"
            if login_user(user, remember=remember):
                flash("Logged in!", "success")
                dqusers.logUserActivity({
                    'user_id': user.id,
                    'ip_address': request.remote_addr,
                    'activity_type': user_activity_types.LOGGED_IN,
                    'activity_data': None
                })
                identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))
                if request.args.get("next"):
                    redir_url = request.script_root + request.args.get("next")
                else:
                    redir_url = url_for("home")
                return redirect(redir_url)
            else:
                flash("Sorry, but you could not log in.", "danger")
        else:
            flash(u"Invalid username or password.", "danger")
    return render_template("login.html",
             admin=check_perms('admin'),
             loggedinuser=current_user)

@app.route('/logout/')
@login_required
def logout():
    dqusers.logUserActivity({
        'user_id': current_user.id,
        'ip_address': request.remote_addr,
        'activity_type': user_activity_types.LOGGED_OUT,
        'activity_data': None
    })
    logout_user()

    # Remove session keys set by Flask-Principal
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    flash('Logged out', 'success')
    redir_url = url_for("home")
    return redirect(redir_url)

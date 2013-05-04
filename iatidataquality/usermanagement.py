
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file
from flask.ext.login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
from flask.ext.principal import Principal, Identity, AnonymousIdentity, \
     identity_changed

from iatidataquality import app
from iatidataquality import db

import os
import sys

current = os.path.dirname(os.path.abspath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)


class User(UserMixin):
    def __init__(self, name, id, active=True):
        self.name = name
        self.id = id
        self.active = active

    def is_active(self):
        return self.active

class Anonymous(AnonymousUser):
    name = u"Anonymous"


USERS = {
    1: User(u"admin", 1),
    3: User(u"notadmin", 3, False),
}

USER_NAMES = dict((u.name, u) for u in USERS.itervalues())

login_manager = LoginManager()

login_manager.anonymous_user = Anonymous
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"

@login_manager.user_loader
def load_user(id):
    return USERS.get(int(id))

login_manager.setup_app(app)

@app.route("/login/", methods=["GET", "POST"])
def login():
    if request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        if username in USER_NAMES:
            remember = request.form.get("remember", "no") == "yes"
            if login_user(USER_NAMES[username], remember=remember):
                flash("Logged in!", "success")
                return redirect(request.args.get("next") or url_for("index"))
            else:
                flash("Sorry, but you could not log in.", "error")
        else:
            flash(u"Invalid username.", "error")
    return render_template("login.html")

@app.route('/logout/')
@login_required
def logout():
    # Remove the user information from the session
    logout_user()
    flash('Logged out', 'success')
    return redirect(request.args.get('next') or '/')

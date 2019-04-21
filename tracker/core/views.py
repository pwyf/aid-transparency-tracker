"""Core views."""
from flask import Blueprint, render_template, abort, redirect, url_for
from flask_security.decorators import login_required
from flask_security.core import current_user

from . import models
from .utils import publisher_required


blueprint = Blueprint('core', __name__)


@blueprint.route('/')
@login_required
def home():
    """Home page."""
    if current_user.has_role('admin'):
        organisations = models.Organisation.query
    else:
        organisations = [o for o in models.Organisation.query
                         if current_user.has_role(organisation_id=o.id)]
        if len(organisations) == 1:
            return redirect(url_for('core.summary',
                                    org_id=organisations[0].id))

    return render_template('core/home.html', organisations=organisations)


@blueprint.route('/summary/<org_id>')
@login_required
@publisher_required
def summary(org_id):
    """Summary page."""
    try:
        organisation = models.Organisation.find_or_fail(org_id)
    except:
        return abort(404)

    return render_template('core/summary.html', organisation=organisation)

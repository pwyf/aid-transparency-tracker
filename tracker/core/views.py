"""Core views."""
from flask import Blueprint, render_template, abort

from . import models


blueprint = Blueprint('core', __name__, url_prefix='/', static_folder='../static')


@blueprint.route('/')
def home():
    """Home page."""
    organisations = models.Organisation.query
    return render_template('core/home.html', organisations=organisations)


@blueprint.route('/summary/<org_id>')
def summary(org_id):
    """Summary page."""
    try:
        organisation = models.Organisation.find_or_fail(org_id)
    except:
        return abort(404)
    return render_template('core/summary.html', organisation=organisation)

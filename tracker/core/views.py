"""Core views."""
from flask import Blueprint, render_template

from . import models


blueprint = Blueprint('core', __name__, url_prefix='/', static_folder='../static')


@blueprint.route('/')
def home():
    """Home page."""
    organisations = models.Organisation.query
    return render_template('core/home.html', organisations=organisations)

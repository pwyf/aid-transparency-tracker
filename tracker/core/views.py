"""Core views."""
from flask import Blueprint, render_template


blueprint = Blueprint('core', __name__, url_prefix='/', static_folder='../static')


@blueprint.route('/')
def home():
    """Home page."""
    return render_template('core/home.html')

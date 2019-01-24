"""Survey section, including homepage and signup."""
from flask import Blueprint, render_template


blueprint = Blueprint('survey', __name__, url_prefix='/survey', static_folder='../static')


@blueprint.route('/')
def main():
    """Main page."""
    return render_template('survey/index.html')

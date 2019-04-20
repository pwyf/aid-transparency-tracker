"""Survey section."""
from flask import Blueprint, render_template
from flask_security.decorators import login_required


blueprint = Blueprint('survey', __name__, url_prefix='/survey', static_folder='../static')


@blueprint.route('/')
@login_required
def home():
    """Main survey page."""
    return render_template('survey/index.html')

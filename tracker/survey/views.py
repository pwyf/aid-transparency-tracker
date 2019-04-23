"""Survey section."""
from flask import abort, Blueprint, render_template
from flask_security.decorators import login_required

from ..core.utils import publisher_required
from ..core.models import Component


blueprint = Blueprint('survey', __name__, url_prefix='/survey')


@blueprint.route('/<org:organisation>')
@login_required
@publisher_required
def home(organisation):
    """Main survey page."""
    if not organisation:
        return abort(404)

    components = Component.with_joined('indicators').all()

    return render_template('survey/index.html',
                           components=components,
                           organisation=organisation)

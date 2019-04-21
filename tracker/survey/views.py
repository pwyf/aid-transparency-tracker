"""Survey section."""
from flask import abort, Blueprint, render_template
from flask_security.decorators import login_required

from ..core import models
from ..core.utils import publisher_required


blueprint = Blueprint('survey', __name__, url_prefix='/survey')


@blueprint.route('/<org_id>')
@login_required
@publisher_required
def home(org_id):
    """Main survey page."""
    try:
        organisation = models.Organisation.find_or_fail(org_id)
    except:
        return abort(404)

    return render_template('survey/index.html', organisation=organisation)

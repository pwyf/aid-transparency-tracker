"""Survey section."""
from flask import abort, Blueprint, render_template
from flask_security.decorators import login_required
from flask_security.core import current_user

from ..core import models


blueprint = Blueprint('survey', __name__, url_prefix='/survey', static_folder='../static')


@blueprint.route('/<org_id>')
@login_required
def home(org_id):
    """Main survey page."""
    try:
        organisation = models.Organisation.find_or_fail(org_id)
    except:
        return abort(404)

    if not (current_user.has_role('admin') or
            current_user.has_role(organisation_id=organisation.id)):
        return abort(403)

    return render_template('survey/index.html', organisation=organisation)

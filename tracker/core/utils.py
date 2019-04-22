from functools import wraps

from werkzeug.routing import BaseConverter
from flask import abort
from flask_security.core import current_user

from . import models


def register_converters(app):
    class OrganisationConverter(BaseConverter):
        def to_python(self, value):
            with app.app_context():
                return models.Organisation.find(value)

        def to_url(self, organisation):
            return organisation.id

    app.url_map.converters['org'] = OrganisationConverter


def publisher_required(func):
    @wraps(func)
    def filter_non_org_admins(*args, **kwargs):
        organisation = kwargs.get('organisation')
        if not (current_user.has_role('admin') or
                current_user.has_role(organisation_id=organisation.id)):
            return abort(401)
        return func(*args, **kwargs)
    return filter_non_org_admins

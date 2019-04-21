from functools import wraps

from werkzeug.routing import BaseConverter
from flask import abort
from flask_security.core import current_user

from . import models


class OrganisationConverter(BaseConverter):
    def to_python(self, value):
        return models.Organisation.find(value)

    def to_url(self, organisation):
        return organisation.id


def publisher_required(func):
    @wraps(func)
    def filter_non_org_admins(*args, **kwargs):
        org_id = kwargs.get('org_id')
        if not (current_user.has_role('admin') or
                current_user.has_role(organisation_id=org_id)):
            return abort(401)
        return func(*args, **kwargs)
    return filter_non_org_admins

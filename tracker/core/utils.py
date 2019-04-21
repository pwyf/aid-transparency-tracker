from werkzeug.routing import BaseConverter

from . import models


class OrganisationConverter(BaseConverter):
    def to_python(self, value):
        return models.Organisation.find(value)

    def to_url(self, organisation):
        return organisation.id

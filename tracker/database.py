"""Database module, including the SQLAlchemy database object and DB-related utilities."""
from sqlalchemy_mixins import ActiveRecordMixin, ReprMixin, \
    SmartQueryMixin, SerializeMixin

from .extensions import db


class BaseModel(ReprMixin, db.Model, ActiveRecordMixin, SmartQueryMixin, SerializeMixin):
    __abstract__ = True

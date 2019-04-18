"""Database module, including the SQLAlchemy database object and DB-related utilities."""
from sqlalchemy_mixins import AllFeaturesMixin

from .extensions import db


class BaseModel(db.Model, AllFeaturesMixin):
    __abstract__ = True

'''This comes straight from the example here:

https://pythonhosted.org/Flask-Security/quickstart.html#id1
'''
from flask_security import UserMixin, RoleMixin

from ..database import db, BaseModel


roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('tracker_user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(BaseModel, RoleMixin):
    """A role for a user."""

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(BaseModel, UserMixin):
    """A user of the app."""

    __tablename__ = 'tracker_user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

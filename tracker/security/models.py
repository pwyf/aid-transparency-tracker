"""This comes straight from the example here:

https://pythonhosted.org/Flask-Security/quickstart.html#id1
"""
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
    organisation = db.Column(
        db.String(255),
        db.ForeignKey('organisation.id', ondelete='CASCADE'),
        nullable=True)


class User(BaseModel, UserMixin):
    """A user of the app."""

    __tablename__ = 'tracker_user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def has_role(self, *args, **kwargs):
        """Modifies has_role to respect kwargs, too."""

        # Super can do anything
        if 'super' in (r.name for r in self.roles):
            return True

        return any([all([getattr(r, k) == v
                         for k, v in kwargs.items()] +
                        [r.name == name for name in args])
                    for r in self.roles])

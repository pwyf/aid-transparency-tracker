"""Seed "admin" and "super" roles.

Revision ID: 410248dde743
Revises: 873290f6bdb9
Create Date: 2019-04-20 00:08:07.287610

"""
from tracker.extensions import security


# revision identifiers, used by Alembic.
revision = '410248dde743'
down_revision = '873290f6bdb9'
branch_labels = None
depends_on = None


def upgrade():
    # Create the admin role
    security.datastore.find_or_create_role(name='admin')
    # Create the superuser role
    security.datastore.find_or_create_role(name='super')
    security.datastore.commit()


def downgrade():
    pass

from ..database import db, BaseModel


class Organisation(BaseModel):
    """An index organisation."""

    __repr_attrs__ = ['name']

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    registry_slug = db.Column(db.String(255))
    test_condition = db.Column(db.String(255))


class Component(BaseModel):
    """An index methodology component. Indicators are grouped by these."""

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text(), nullable=False)


class Indicator(BaseModel):
    """An indicator of transparency."""

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    indicator_type = db.Column(db.String(255), nullable=False)
    component_id = db.Column(db.String(255), db.ForeignKey('component.id',
                             ondelete='CASCADE'), nullable=False)
    component = db.relationship('Component',
                                backref=db.backref('indicators', lazy=True))
    description = db.Column(db.Text(), nullable=False)
    order = db.Column(db.Integer(), nullable=False)
    ordinal = db.Column(db.Boolean, nullable=False)
    weight = db.Column(db.String(255), nullable=False)
    has_format = db.Column(db.Boolean, nullable=False)

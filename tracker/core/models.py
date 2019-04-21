from ..database import db, BaseModel


class Organisation(BaseModel):
    """An index organisation."""

    __repr_attrs__ = ['name']

    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    registry_slug = db.Column(db.String(255))
    test_condition = db.Column(db.String(255))


# class Indicator(BaseModel):
#     pass

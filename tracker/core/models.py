from ..database import db, BaseModel


class Organisation(BaseModel):
    """An index organisation."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    registry_slug = db.Column(db.String(255))
    test_condition = db.Column(db.String(255))

from ..database import db, BaseModel


class Organisation(BaseModel):
    """An index organisation."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    org_id = db.Column(db.String(255), unique=True, nullable=True)
    registry_handle = db.Column(db.String(255), nullable=True)

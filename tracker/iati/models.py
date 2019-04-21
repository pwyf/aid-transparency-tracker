# from ..database import db, BaseModel


# class IATISnapshot(BaseModel):
#     """Automated testrun of an organisation’s data snapshot."""

#     __repr_attrs__ = ['organisation_id', 'snapshot_date']

#     id = db.Column(db.Integer(), primary_key=True)
#     downloaded_on = db.Column(db.Date, nullable=False)
#     organisation_id = db.Column(
#         db.String(255), db.ForeignKey('organisation.id', ondelete='CASCADE'),
#         nullable=False)
#     organisation = db.relationship('Organisation',
#                                    backref=db.backref('snapshots', lazy=True))


# class IATITest(BaseModel):
#     id = db.Column(db.Integer(), primary_key=True)
#     name = db.Column(db.String(255))
#     feature_id = db.Column(
#         db.Integer(), db.ForeignKey('feature.id', ondelete='CASCADE'),
#         nullable=False)
#     feature = db.relationship('Feature',
#                               backref=db.backref('tests', lazy=True))
#     order = db.Column(db.Integer(), nullable=False)


# class IATISnapshotResult(BaseModel):
#     """Results per test for a given organisation snapshot."""

#     id = db.Column(db.Integer(), primary_key=True)
#     snapshot_id = db.Column(
#         db.Integer(), db.ForeignKey('iati_snapshot.id', ondelete='CASCADE'),
#         nullable=False)
#     snapshot = db.relationship('IATISnapshot',
#                                backref=db.backref('results', lazy=True))
#     test_id = db.Column(
#         db.Integer(), db.ForeignKey('iati_test.id', ondelete='CASCADE'),
#         nullable=False)
#     test = db.relationship('IATITest',
#                            backref=db.backref('results', lazy=True))

#     passes = db.Column(db.Integer(), nullable=False, default=0)
#     fails = db.Column(db.Integer(), nullable=False, default=0)
#     not_relevants = db.Column(db.Integer(), nullable=False, default=0)

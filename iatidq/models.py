
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_mixins import AllFeaturesMixin, ModelNotFoundError

from iatidataquality import db


class BaseModel(db.Model, AllFeaturesMixin):
    __abstract__ = True


class PackageStatus(BaseModel):
    __tablename__ = 'packagestatus'
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    runtime_datetime = db.Column(db.DateTime)

    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return unicode(self.runtime_datetime)+u' '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Runtime(BaseModel):
    __tablename__ = 'runtime'
    id = db.Column(db.Integer, primary_key=True)
    runtime_datetime = db.Column(db.DateTime, nullable=False)

    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return unicode(self.runtime_datetime)+u' '+unicode(self.id)

## IATI REGISTRY PACKAGEGROUPS AND PACKAGES

class PackageGroup(BaseModel):
    __tablename__ = 'packagegroup'
    id = db.Column(db.Integer, primary_key=True)
    man_auto = db.Column(db.UnicodeText)
    name = db.Column(db.UnicodeText, nullable=False)
    ckan_id = db.Column(db.UnicodeText)
    revision_id = db.Column(db.UnicodeText)
    title = db.Column(db.UnicodeText)
    created_date = db.Column(db.UnicodeText)
    state = db.Column(db.UnicodeText)
    publisher_iati_id = db.Column(db.UnicodeText)
    publisher_segmentation = db.Column(db.UnicodeText)
    publisher_type = db.Column(db.UnicodeText)
    publisher_ui = db.Column(db.UnicodeText)
    publisher_organization_type = db.Column(db.UnicodeText)
    publisher_frequency = db.Column(db.UnicodeText)
    publisher_thresholds = db.Column(db.UnicodeText)
    publisher_units = db.Column(db.UnicodeText)
    publisher_contact = db.Column(db.UnicodeText)
    publisher_agencies = db.Column(db.UnicodeText)
    publisher_field_exclusions = db.Column(db.UnicodeText)
    publisher_description = db.Column(db.UnicodeText)
    publisher_record_exclusions = db.Column(db.UnicodeText)
    publisher_timeliness = db.Column(db.UnicodeText)
    license_id = db.Column(db.UnicodeText)
    publisher_country = db.Column(db.UnicodeText)
    publisher_refs = db.Column(db.UnicodeText)
    publisher_constraints = db.Column(db.UnicodeText)
    publisher_data_quality = db.Column(db.UnicodeText)
    __table_args__ = (db.UniqueConstraint('name',),)

    def __init__(self, man_auto=None, name=None):
        if man_auto is not None:
            self.man_auto = man_auto
        if name is not None:
            self.name = name

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Package(BaseModel):
    __tablename__ = 'package'
    id = db.Column(db.Integer, primary_key=True)
    man_auto = db.Column(db.UnicodeText)
    source_url = db.Column(db.UnicodeText)
    package_ckan_id = db.Column(db.UnicodeText)
    package_name = db.Column(db.UnicodeText, nullable=False)
    package_title = db.Column(db.UnicodeText)
    package_license_id = db.Column(db.UnicodeText)
    package_license = db.Column(db.UnicodeText)
    package_metadata_created = db.Column(db.UnicodeText)
    package_metadata_modified = db.Column(db.UnicodeText)
    package_group_id = db.Column(db.Integer, db.ForeignKey('packagegroup.id', ondelete='CASCADE'))
    package_activity_from = db.Column(db.UnicodeText)
    package_activity_to = db.Column(db.UnicodeText)
    package_activity_count = db.Column(db.UnicodeText)
    package_country = db.Column(db.UnicodeText)
    package_archive_file = db.Column(db.UnicodeText)
    package_verified = db.Column(db.UnicodeText)
    package_filetype = db.Column(db.UnicodeText)
    package_revision_id = db.Column(db.UnicodeText)
    active = db.Column(db.Boolean)
    hash = db.Column(db.UnicodeText)
    deleted = db.Column(db.Boolean, default=False)
    __table_args__ = (db.UniqueConstraint('package_name'),)

    def __init__(self, man_auto=None, source_url=None):
        if man_auto is not None:
            self.man_auto = man_auto
        if source_url is not None:
            self.source_url = source_url

    def __repr__(self):
        source_url = self.source_url or "None"
        return source_url+u", "+str(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## RESULTS

class Result(BaseModel):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key=True)
    runtime_id = db.Column(db.Integer, db.ForeignKey('runtime.id', ondelete='CASCADE'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id', ondelete='CASCADE'), nullable=False)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id', ondelete='CASCADE'))
    test_id = db.Column(db.Integer, db.ForeignKey('test.id', ondelete='CASCADE'), nullable=False)
    result_data = db.Column(db.Integer, nullable=False)
    result_identifier = db.Column(db.UnicodeText)
    result_hierarchy = db.Column(db.Integer)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

db.Index('result_runpack',
         Result.runtime_id, Result.package_id, Result.result_identifier)
db.Index('result_test',
         Result.test_id)

class AggregateResult(BaseModel):
    __tablename__='aggregateresult'
    id = db.Column(db.Integer,primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id', ondelete='CASCADE'), nullable=False)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id', ondelete='CASCADE'))
    aggregateresulttype_id = db.Column(db.Integer, db.ForeignKey('aggregationtype.id', ondelete='CASCADE'),
                                    nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id', ondelete='CASCADE'), nullable=False)
    result_hierarchy = db.Column(db.Integer, nullable=False)
    results_data = db.Column(db.Float)
    results_num = db.Column(db.Integer)
    __table_args__ = (db.UniqueConstraint('package_id',
                                       'test_id',
                                       'result_hierarchy',
                                       'aggregateresulttype_id',
                                       'organisation_id'),)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# AggregationType allows for different aggregations
# Particularly used for looking only at current data
class AggregationType(BaseModel):
    __tablename__ = 'aggregationtype'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    description = db.Column(db.UnicodeText)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id', ondelete='CASCADE'))
    test_result = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Integer)

    def setup(self,
                 name,
                 description,
                 test_id,
                 test_result,
                 active,
                 id=None):
        self.name = name
        self.description = description
        self.test_id = test_id
        self.test_result = test_result
        self.active = active
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## TESTS

class Test(BaseModel):
    __tablename__ = 'test'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    description = db.Column(db.UnicodeText, nullable=False)
    test_group = db.Column(db.UnicodeText)
    file = db.Column(db.UnicodeText)
    line = db.Column(db.Integer)
    test_level = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean)

    def setup(self,
                 name,
                 description,
                 test_group,
                 test_level,
                 active,
                 id=None):
        self.name = name
        self.description = description
        self.test_group = test_group
        self.test_level = test_level
        self.active = active
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## CODELISTS

class Codelist(BaseModel):
    __tablename__ = 'codelist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    description = db.Column(db.UnicodeText)
    source = db.Column(db.UnicodeText)

    def setup(self,
                 name,
                 description,
                 id=None):
        self.name = name
        self.description = description
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class CodelistCode(BaseModel):
    __tablename__ = 'codelistcode'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    code = db.Column(db.UnicodeText, nullable=False)
    codelist_id = db.Column(db.Integer, db.ForeignKey('codelist.id', ondelete='CASCADE'), nullable=False)
    source = db.Column(db.UnicodeText)

    def setup(self,
                 name,
                 code,
                 codelist_id,
                 id=None):
        self.name = name
        self.code = code
        self.codelist_id = codelist_id
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## INDICATORS

class IndicatorGroup(BaseModel):
    __tablename__ = 'indicatorgroup'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    description = db.Column(db.UnicodeText)

    def setup(self,
                 name,
                 description,
                 id=None):
        self.name = name
        self.description = description
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Indicator(BaseModel):
    __tablename__ = 'indicator'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    description = db.Column(db.UnicodeText)
    longdescription = db.Column(db.UnicodeText)
    indicatorgroup_id = db.Column(db.Integer, db.ForeignKey('indicatorgroup.id', ondelete='CASCADE'),
                               nullable=False)
    indicator_type = db.Column(db.UnicodeText)
    indicator_category_name = db.Column(db.UnicodeText)
    indicator_subcategory_name = db.Column(db.UnicodeText)
    indicator_ordinal = db.Column(db.Boolean)
    indicator_noformat = db.Column(db.Boolean)
    indicator_order = db.Column(db.Integer, nullable=False)
    indicator_weight = db.Column(db.Float(precision=4))

    @property
    def indicator_category_name_text(self):
        return self.indicator_category_name

    @property
    def indicator_subcategory_name_text(self):
        return self.indicator_subcategory_name

    def setup(self,
                 name,
                 description,
                 longdescription,
                 indicatorgroup_id,
                 indicator_type,
                 indicator_category_name,
                 indicator_subcategory_name,
                 indicator_ordinal=None,
                 indicator_noformat=None,
                 indicator_order=None,
                 indicator_weight=None,
                 id=None):
        self.name = name
        self.description = description
        self.longdescription = longdescription
        self.indicatorgroup_id = indicatorgroup_id
        self.indicator_type = indicator_type
        self.indicator_category_name = indicator_category_name
        self.indicator_subcategory_name = indicator_subcategory_name
        self.indicator_ordinal = indicator_ordinal
        self.indicator_noformat = indicator_noformat
        self.indicator_order = indicator_order
        self.indicator_weight = indicator_weight
        if id is not None:
            self.id = id

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
       return d

class IndicatorTest(BaseModel):
    __tablename__ = 'indicatortest'
    id = db.Column(db.Integer, primary_key=True)
    indicator_id = db.Column(db.Integer, db.ForeignKey('indicator.id', ondelete='CASCADE'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (db.UniqueConstraint('test_id'), )

    def setup(self,
                 indicator_id,
                 test_id,
                 id=None):
        self.indicator_id = indicator_id
        self.test_id = test_id
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class IndicatorInfoType(BaseModel):
    __tablename__ = 'indicatorinfotype'
    id = db.Column(db.Integer, primary_key=True)
    indicator_id = db.Column(db.Integer, db.ForeignKey('indicator.id', ondelete='CASCADE'), nullable=False)
    infotype_id = db.Column(db.Integer, db.ForeignKey('info_type.id', ondelete='CASCADE'), nullable=False)

    def setup(self,
                 indicator_id,
                 infotype_id,
                 id=None):
        self.indicator_id = indicator_id
        self.infotype_id = infotype_id
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class OrganisationCondition(BaseModel):
    __tablename__ = 'organisationcondition'
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id', ondelete='CASCADE'),
                             nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id', ondelete='CASCADE'), nullable=False)
    operation = db.Column(db.Integer) # show (1) or don't show (0) result
    condition = db.Column(db.UnicodeText) # activity level, hierarchy 2
    condition_value = db.Column(db.UnicodeText) # True, 2, etc.
    description = db.Column(db.UnicodeText)
    file = db.Column(db.UnicodeText)
    line = db.Column(db.Integer)
    active = db.Column(db.Boolean)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class OrganisationConditionFeedback(BaseModel):
    __tablename__ ='organisationconditionfeedback'
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer,
                             db.ForeignKey('organisation.id', ondelete='CASCADE'),
                             nullable=False)
    uses = db.Column(db.UnicodeText)
    element = db.Column(db.UnicodeText)
    where = db.Column(db.UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Migration
"""
alter table organisationconditionfeedback
    alter column organisation_id type integer USING (organisation_id::integer);
alter table organisationconditionfeedback add constraint ofbkorg FOREIGN KEY (organisation_id) REFERENCES organisation (id) MATCH FULL;
"""

## ORGANISATIONS; RELATIONS WITH PACKAGES

class Organisation(BaseModel):
    __tablename__ = 'organisation'
    id = db.Column(db.Integer, primary_key=True)
    organisation_name = db.Column(db.UnicodeText, nullable=False)
    organisation_code = db.Column(db.UnicodeText, nullable=False)
    organisation_total_spend = db.Column(db.Float(precision=2))
    organisation_total_spend_source = db.Column(db.UnicodeText)
    organisation_currency = db.Column(db.UnicodeText)
    organisation_currency_conversion = db.Column(db.Float(precision=4))
    organisation_currency_conversion_source = db.Column(db.UnicodeText)
    organisation_largest_recipient = db.Column(db.UnicodeText)
    organisation_largest_recipient_source = db.Column(db.UnicodeText)
    frequency = db.Column(db.UnicodeText)
    frequency_comment = db.Column(db.UnicodeText)
    no_independent_reviewer=db.Column(db.Boolean)
    organisation_responded=db.Column(db.Integer)
    __table_args__ = (db.UniqueConstraint('organisation_name'),
                      db.UniqueConstraint('organisation_code'))
    # organisation_code is also used to communicate
    # with implementation schedules

    def setup(self,
                 organisation_name,
                 organisation_code,
                 organisation_total_spend=None,
                 organisation_total_spend_source=None,
                 organisation_currency=None,
                 organisation_currency_conversion=None,
                 organisation_currency_conversion_source=None,
                 organisation_largest_recipient=None,
                 organisation_largest_recipient_source=None,
                 id=None):
        self.organisation_name = organisation_name
        self.organisation_code = organisation_code
        self.organisation_total_spend = organisation_total_spend,
        self.organisation_currency = organisation_currency,
        self.organisation_currency_conversion = organisation_currency_conversion,
        self.organisation_currency_conversion_source = organisation_currency_conversion_source,
        self.organisation_largest_recipient = organisation_largest_recipient
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class OrganisationPackage(BaseModel):
    __tablename__ = 'organisationpackage'
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id', ondelete='CASCADE'),
                             nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id', ondelete='CASCADE'), nullable=False)
    condition = db.Column(db.UnicodeText)
    __table_args__ = (db.UniqueConstraint('organisation_id', 'package_id', name='_organisation_package_uc'),
                     )
    def setup(self,
                 organisation_id,
                 package_id,
                 condition=None,
                 id=None):
        self.organisation_id = organisation_id
        self.package_id = package_id
        self.condition = condition
        if id is not None:
            self.id = id

class OrganisationPackageGroup(BaseModel):
    __tablename__ = 'organisationpackagegroup'
    id = db.Column(db.Integer, primary_key=True)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id', ondelete='CASCADE'),
                             nullable=False)
    packagegroup_id = db.Column(db.Integer, db.ForeignKey('packagegroup.id', ondelete='CASCADE'),
                             nullable=False)
    condition = db.Column(db.UnicodeText)
    __table_args__ = (db.UniqueConstraint('organisation_id', 'packagegroup_id'),)

    def setup(self,
                 organisation_id,
                 packagegroup_id,
                 condition=None,
                 id=None):
        self.organisation_id = organisation_id
        self.packagegroup_id = packagegroup_id
        self.condition = condition
        if id is not None:
            self.id = id

## INFORESULTS
# TODO: IMPLEMENT
# ==> total amount of disbursements in this package
# e.g. 1 = total disbursements

class InfoResult(BaseModel):
    __tablename__ = 'info_result'
    id = db.Column(db.Integer, primary_key=True)
    runtime_id = db.Column(db.Integer, db.ForeignKey('runtime.id', ondelete='CASCADE'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id', ondelete='CASCADE'), nullable=False)
    info_id = db.Column(db.Integer, db.ForeignKey('info_type.id', ondelete='CASCADE'), nullable=False)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id', ondelete='CASCADE'))
    result_data = db.Column(db.Float)

class InfoType(BaseModel):
    __tablename__ = 'info_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText, nullable=False)
    description = db.Column(db.UnicodeText)
    level = db.Column(db.Integer, nullable=False)

    def setup(self,
                 name,
                 level,
                 description=None,
                 id=None):
        self.name = name
        self.level = level
        self.description = description
        if id is not None:
            self.id = id

## USERS

class User(BaseModel):
    __tablename__ = 'dquser'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.UnicodeText, nullable=False)
    name = db.Column(db.UnicodeText)
    email_address = db.Column(db.UnicodeText)
    reset_password_key = db.Column(db.UnicodeText)
    pw_hash = db.Column(db.String(255))
    organisation = db.Column(db.UnicodeText)
    children = db.relationship("UserPermission",
                    cascade="all, delete-orphan",
                    passive_deletes=True)
    __table_args__ = (db.UniqueConstraint('username',),)

    def setup(self,
                 username,
                 password,
                 name,
                 email_address=None,
                 organisation=None,
                 id=None):
        self.username = username
        self.pw_hash = generate_password_hash(password)
        self.name = name
        self.email_address = email_address
        self.organisation = organisation
        if id is not None:
            self.id = id

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

class UserPermission(BaseModel):
    __tablename__ = 'userpermission'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('dquser.id', ondelete='CASCADE'))
    permission_name = db.Column(db.UnicodeText) # survey_donorreview
    permission_method = db.Column(db.UnicodeText) # edit
    permission_value = db.Column(db.UnicodeText) # 1

    def setup(self,
                 user_id,
                 permission_name,
                 permission_method=None,
                 permission_value=None,
                 id=None):
        self.user_id = user_id
        self.permission_name = permission_name
        self.permission_method = permission_method
        self.permission_value = permission_value
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

## ORGANISATION SURVEYS

class OrganisationSurvey(BaseModel):
    __tablename__ = 'organisationsurvey'
    id = db.Column(db.Integer,primary_key=True)
    currentworkflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id', ondelete='CASCADE'),
                                nullable=False)
    currentworkflow_deadline = db.Column(db.DateTime)
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id', ondelete='CASCADE'),
                             nullable=False)
    __table_args__ = (db.UniqueConstraint('organisation_id',),)

    workflow = db.relationship('Workflow')

    def setup(self,
                 organisation_id,
                 currentworkflow_id,
                 currentworkflow_deadline=None,
                 id=None):
        self.organisation_id = organisation_id
        self.currentworkflow_id = currentworkflow_id
        self.currentworkflow_deadline = currentworkflow_deadline
        if id is not None:
            self.id = id

class OrganisationSurveyData(BaseModel):
    __tablename__ = 'organisationsurveydata'
    id = db.Column(db.Integer,primary_key=True)
    organisationsurvey_id = db.Column(db.Integer,
                                   db.ForeignKey('organisationsurvey.id', ondelete='CASCADE'),
                                   nullable=False)
    indicator_id = db.Column(db.Integer, db.ForeignKey('indicator.id', ondelete='CASCADE'), nullable=False)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflow.id', ondelete='CASCADE'), nullable=False)
    published_status_id = db.Column(db.Integer, db.ForeignKey('publishedstatus.id', ondelete='CASCADE'))
    published_source = db.Column(db.UnicodeText)
    published_comment = db.Column(db.UnicodeText)
    published_format_id = db.Column(db.Integer, db.ForeignKey('publishedformat.id', ondelete='CASCADE'))
    published_accepted = db.Column(db.Integer)
    ordinal_value = db.Column(db.Float(precision=2))
    __table_args__ = (db.UniqueConstraint('organisationsurvey_id',
                                       'indicator_id',
                                       'workflow_id'),)

    def setup(self,
                 organisationsurvey_id,
                 indicator_id,
                 workflow_id=None,
                 published_status_id=None,
                 published_source=None,
                 published_comment=None,
                 published_format_id=None,
                 published_accepted=None,
                 ordinal_value=None,
                 id=None):
        self.organisationsurvey_id = organisationsurvey_id
        self.workflow_id = workflow_id
        self.indicator_id = indicator_id
        self.published_status_id = published_status_id
        self.published_source = published_source
        self.published_comment = published_comment
        self.published_format_id = published_format_id
        self.published_accepted = published_accepted
        self.ordinal_value = ordinal_value

        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class PublishedFormat(BaseModel):
    __tablename__ = 'publishedformat'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText)
    title = db.Column(db.UnicodeText)
    format_class = db.Column(db.UnicodeText)
    format_value = db.Column(db.Float)

    def setup(self,
                 name,
                 title,
                 format_class,
                 format_value,
                 id=None):
        self.name = name
        self.title = title
        self.format_class = format_class
        self.format_value = format_value
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class PublishedStatus(BaseModel):
    __tablename__ = 'publishedstatus'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.UnicodeText)
    title = db.Column(db.UnicodeText)
    publishedstatus_class = db.Column(db.UnicodeText)
    publishedstatus_value = db.Column(db.Float)

    def setup(self,
                 name,
                 title,
                 publishedstatus_class,
                 publishedstatus_value,
                 id=None):
        self.name = name
        self.title = title
        self.publishedstatus_class = publishedstatus_class
        self.publishedstatus_value = publishedstatus_value
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Workflow(BaseModel):
    __tablename__='workflow'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.UnicodeText)
    title = db.Column(db.UnicodeText)
    order = db.Column(db.Integer)
    workflow_type_id = db.Column(db.Integer, db.ForeignKey('workflowtype.id', ondelete='CASCADE'))
    duration = db.Column(db.Integer)

    workflow_type = db.relationship('WorkflowType')

    def get_next(self):
        cls = self.__class__
        return cls.query.filter(
            cls.order > self.order
        ).order_by(
            cls.order
        ).first()

    def setup(self,
                 name,
                 title,
                 order,
                 workflow_type_id=None,
                 duration=None,
                 id=None):
        self.name = name
        self.title = title
        self.order = order
        self.workflow_type_id = workflow_type_id
        self.duration = duration
        if id is not None:
            self.id = id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# WorkflowType: define what sort of workflow this should be.
#   Will initially be hardcoded but this should make it easier
#   to expand and define later.
class WorkflowType(BaseModel):
    __tablename__='workflowtype'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.UnicodeText)

    def setup(self,
                 name,
                 id=None):
        self.name = name
        if id is not None:
            self.id = id


class UserActivity(BaseModel):
    __tablename__='useractivity'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('dquser.id', ondelete='CASCADE'))
    activity_type = db.Column(db.Integer)
    activity_data = db.Column(db.UnicodeText)
    ip_address = db.Column(db.UnicodeText)
    activity_date = db.Column(db.DateTime)


class SamplingFailure(BaseModel):
    __tablename__ = 'sampling_failure'
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisation.id', ondelete='CASCADE'),
                             primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id', ondelete='CASCADE'),
                     primary_key=True)

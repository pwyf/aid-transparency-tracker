
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from sqlalchemy import *
from iatidq import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

## TEST RUNTIME-SPECIFIC DATA

class PackageStatus(db.Model):
    __tablename__ = 'packagestatus'
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey('package.id'), nullable=False)
    status = Column(Integer, nullable=False)
    runtime_datetime = Column(DateTime)

    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return unicode(self.runtime_datetime)+u' '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Runtime(db.Model):
    __tablename__ = 'runtime'
    id = Column(Integer, primary_key=True)
    runtime_datetime = Column(DateTime, nullable=False)

    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return unicode(self.runtime_datetime)+u' '+unicode(self.id)

## IATI REGISTRY PACKAGEGROUPS AND PACKAGES

class PackageGroup(db.Model):
    __tablename__ = 'packagegroup'
    id = Column(Integer, primary_key=True)
    man_auto = Column(UnicodeText)
    name = Column(UnicodeText, nullable=False)
    ckan_id = Column(UnicodeText)
    revision_id = Column(UnicodeText)
    title = Column(UnicodeText)
    created_date = Column(UnicodeText)
    state = Column(UnicodeText)
    publisher_iati_id = Column(UnicodeText)
    publisher_segmentation = Column(UnicodeText)
    publisher_type = Column(UnicodeText)
    publisher_ui = Column(UnicodeText)
    publisher_organization_type = Column(UnicodeText)
    publisher_frequency = Column(UnicodeText)
    publisher_thresholds = Column(UnicodeText)
    publisher_units = Column(UnicodeText)
    publisher_contact = Column(UnicodeText)
    publisher_agencies = Column(UnicodeText)
    publisher_field_exclusions = Column(UnicodeText)
    publisher_description = Column(UnicodeText)
    publisher_record_exclusions = Column(UnicodeText)
    publisher_timeliness = Column(UnicodeText)
    license_id = Column(UnicodeText)
    publisher_country = Column(UnicodeText)
    publisher_refs = Column(UnicodeText)
    publisher_constraints = Column(UnicodeText)
    publisher_data_quality = Column(UnicodeText)
    __table_args__ = (UniqueConstraint('name',),)

    def __init__(self, man_auto=None, name=None):
        if man_auto is not None:
            self.man_auto = man_auto
        if name is not None:
            self.name = name

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Package(db.Model):
    __tablename__ = 'package'
    id = Column(Integer, primary_key=True)
    man_auto = Column(UnicodeText)
    source_url = Column(UnicodeText)
    package_ckan_id = Column(UnicodeText)
    package_name = Column(UnicodeText, nullable=False)
    package_title = Column(UnicodeText)
    package_license_id = Column(UnicodeText)
    package_license = Column(UnicodeText)
    package_metadata_created = Column(UnicodeText)
    package_metadata_modified = Column(UnicodeText)
    package_group = Column(Integer, ForeignKey('packagegroup.id'))
    package_activity_from = Column(UnicodeText)
    package_activity_to = Column(UnicodeText)
    package_activity_count = Column(UnicodeText)
    package_country = Column(UnicodeText)
    package_archive_file = Column(UnicodeText)   
    package_verified = Column(UnicodeText)  
    package_filetype = Column(UnicodeText)  
    package_revision_id = Column(UnicodeText)    
    active = Column(Boolean)
    hash = Column(UnicodeText)
    deleted = Column(Boolean, default=False)
    __table_args__ = (UniqueConstraint('package_name'),)

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

class Result(db.Model):
    __tablename__ = 'result'
    id = Column(Integer, primary_key=True)
    runtime_id = Column(Integer, ForeignKey('runtime.id'), nullable=False)
    package_id = Column(Integer, ForeignKey('package.id'), nullable=False)
    organisation_id = Column(Integer, ForeignKey('organisation.id'))
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    result_data = Column(Integer, nullable=False)
    result_identifier = Column(UnicodeText)
    result_hierarchy = Column(Integer)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

db.Index('result_runpack', 
         Result.runtime_id, Result.package_id, Result.result_identifier)
db.Index('result_test',
         Result.test_id)

# there should be a uniqueness constraint, roughly:
#
# alter table aggregateresult add unique  (
#   package_id, test_id, result_hierarchy, aggregateresulttype_id, 
#   organisation_id
# );
#
# but after normalisation the package/organisation thing should go away

class AggregateResult(db.Model):
    __tablename__='aggregateresult'
    id = Column(Integer,primary_key=True)
    package_id = Column(Integer, ForeignKey('package.id'), nullable=False)
    organisation_id = Column(Integer, ForeignKey('organisation.id'))
    aggregateresulttype_id = Column(Integer, ForeignKey('aggregationtype.id'),
                                    nullable=False)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    result_hierarchy = Column(Integer)
    results_data = Column(Float)
    results_num = Column(Integer)
    __table_args__ = (UniqueConstraint('package_id', 
                                       'test_id', 
                                       'result_hierarchy', 
                                       'aggregateresulttype_id', 
                                       'organisation_id'),)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# AggregationType allows for different aggregations
# Particularly used for looking only at current data
class AggregationType(db.Model):
    __tablename__ = 'aggregationtype'
    id = Column(Integer,primary_key=True)
    name = Column(UnicodeText, nullable=False)
    description = Column(UnicodeText)
    test_id = Column(Integer, ForeignKey('test.id'))
    test_result = Column(Integer, nullable=False)
    active = Column(Integer)

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

class Test(db.Model):
    __tablename__ = 'test'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    description = Column(UnicodeText, nullable=False)
    test_group = Column(UnicodeText)
    file = Column(UnicodeText)
    line = Column(Integer)
    test_level = Column(Integer, nullable=False)
    active = Column(Boolean)

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

class Codelist(db.Model):
    __tablename__ = 'codelist'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    description = Column(UnicodeText)
    source = Column(UnicodeText)

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

class CodelistCode(db.Model):
    __tablename__ = 'codelistcode'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    code = Column(UnicodeText, nullable=False)
    codelist_id = Column(Integer, ForeignKey('codelist.id'), nullable=False)
    source = Column(UnicodeText)

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

class IndicatorGroup(db.Model):
    __tablename__ = 'indicatorgroup'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    description = Column(UnicodeText)

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

class Indicator(db.Model):
    __tablename__ = 'indicator'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    description = Column(UnicodeText)
    longdescription = Column(UnicodeText)
    indicatorgroup_id = Column(Integer, ForeignKey('indicatorgroup.id'),
                               nullable=False)
    indicator_type = Column(UnicodeText)
    indicator_category_name = Column(UnicodeText)
    indicator_subcategory_name = Column(UnicodeText)
    indicator_ordinal = Column(Boolean)
    indicator_noformat = Column(Boolean)
    indicator_order = Column(Integer, nullable=False)
    indicator_weight = Column(Float(precision=4))

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
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class IndicatorTest(db.Model):
    __tablename__ = 'indicatortest'
    id = Column(Integer, primary_key=True)
    indicator_id = Column(Integer, ForeignKey('indicator.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    __table_args__ = (UniqueConstraint('test_id'), )

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

class IndicatorInfoType(db.Model):
    __tablename__ = 'indicatorinfotype'
    id = Column(Integer, primary_key=True)
    indicator_id = Column(Integer, ForeignKey('indicator.id'), nullable=False)
    infotype_id = Column(Integer, ForeignKey('info_type.id'), nullable=False)

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

class OrganisationCondition(db.Model):
    __tablename__ = 'organisationcondition'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisation.id'),
                             nullable=False)
    test_id = Column(Integer, ForeignKey('test.id'), nullable=False)
    operation = Column(Integer) # show (1) or don't show (0) result
    condition = Column(UnicodeText) # activity level, hierarchy 2
    condition_value = Column(UnicodeText) # True, 2, etc.
    description = Column(UnicodeText)
    file = Column(UnicodeText)
    line = Column(Integer)
    active = Column(Boolean)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class OrganisationConditionFeedback(db.Model):
    __tablename__ ='organisationconditionfeedback'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer,
                             ForeignKey('organisation.id'),
                             nullable=False)
    uses = Column(UnicodeText)
    element = Column(UnicodeText)
    where = Column(UnicodeText)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Migration
"""
alter table organisationconditionfeedback
    alter column organisation_id type integer USING (organisation_id::integer);
alter table organisationconditionfeedback add constraint ofbkorg FOREIGN KEY (organisation_id) REFERENCES organisation (id) MATCH FULL;
"""

## ORGANISATIONS; RELATIONS WITH PACKAGES

class Organisation(db.Model):
    __tablename__ = 'organisation'
    id = Column(Integer, primary_key=True)
    organisation_name = Column(UnicodeText, nullable=False)
    organisation_code = Column(UnicodeText, nullable=False)
    organisation_total_spend = Column(Float(precision=2))
    organisation_total_spend_source = Column(UnicodeText)
    organisation_currency = Column(UnicodeText)
    organisation_currency_conversion = Column(Float(precision=4))
    organisation_currency_conversion_source = Column(UnicodeText)
    organisation_largest_recipient = Column(UnicodeText)
    organisation_largest_recipient_source = Column(UnicodeText)
    frequency = Column(UnicodeText)
    frequency_comment = Column(UnicodeText)
    no_independent_reviewer=Column(Boolean)
    organisation_responded=Column(Integer)
    __table_args__ = (UniqueConstraint('organisation_name'),
                      UniqueConstraint('organisation_code'))
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

class OrganisationPackage(db.Model):
    __tablename__ = 'organisationpackage'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisation.id'),
                             nullable=False)
    package_id = Column(Integer, ForeignKey('package.id'), nullable=False)
    condition = Column(UnicodeText)
    __table_args__ = (UniqueConstraint('organisation_id', 'package_id', name='_organisation_package_uc'),
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

class OrganisationPackageGroup(db.Model):
    __tablename__ = 'organisationpackagegroup'
    id = Column(Integer, primary_key=True)
    organisation_id = Column(Integer, ForeignKey('organisation.id'),
                             nullable=False)
    packagegroup_id = Column(Integer, ForeignKey('packagegroup.id'),
                             nullable=False)
    condition = Column(UnicodeText)
    __table_args__ = (UniqueConstraint('organisation_id', 'packagegroup_id'),)

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

class InfoResult(db.Model):
    __tablename__ = 'info_result'
    id = Column(Integer, primary_key=True)
    runtime_id = Column(Integer, ForeignKey('runtime.id'), nullable=False)
    package_id = Column(Integer, ForeignKey('package.id'), nullable=False)
    info_id = Column(Integer, ForeignKey('info_type.id'), nullable=False)
    organisation_id = Column(Integer, ForeignKey('organisation.id'))
    result_data = Column(Float)
    
class InfoType(db.Model):
    __tablename__ = 'info_type'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    description = Column(UnicodeText)
    level = Column(Integer, nullable=False)

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

class User(db.Model):
    __tablename__ = 'dquser'
    id = Column(Integer, primary_key=True)
    username = Column(UnicodeText, nullable=False)
    name = Column(UnicodeText)
    email_address = Column(UnicodeText)
    reset_password_key = Column(UnicodeText)
    pw_hash = db.Column(String(255))
    organisation = Column(UnicodeText)
    children = db.relationship("UserPermission",
                    cascade="all, delete-orphan",
                    passive_deletes=True)
    __table_args__ = (UniqueConstraint('username',),)

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

class UserPermission(db.Model):
    __tablename__ = 'userpermission'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('dquser.id', ondelete='CASCADE'))
    permission_name = Column(UnicodeText) # survey_donorreview
    permission_method = Column(UnicodeText) # edit
    permission_value = Column(UnicodeText) # 1

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

class OrganisationSurvey(db.Model):
    __tablename__ = 'organisationsurvey'
    id = Column(Integer,primary_key=True)
    currentworkflow_id = Column(Integer, ForeignKey('workflow.id'), 
                                nullable=False)
    currentworkflow_deadline = Column(DateTime)
    organisation_id = Column(Integer, ForeignKey('organisation.id'), 
                             nullable=False)
    __table_args__ = (UniqueConstraint('organisation_id',),)
    
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

class OrganisationSurveyData(db.Model):
    __tablename__ = 'organisationsurveydata'
    id = Column(Integer,primary_key=True)
    organisationsurvey_id = Column(Integer, 
                                   ForeignKey('organisationsurvey.id'),
                                   nullable=False)
    indicator_id = Column(Integer, ForeignKey('indicator.id'), nullable=False)
    workflow_id = Column(Integer, ForeignKey('workflow.id'), nullable=False)
    published_status = Column(Integer, ForeignKey('publishedstatus.id'))
    published_source = Column(UnicodeText)
    published_comment = Column(UnicodeText)
    published_format = Column(Integer, ForeignKey('publishedformat.id'))
    published_accepted = Column(Integer)
    ordinal_value = Column(Float(precision=2))
    __table_args__ = (UniqueConstraint('organisationsurvey_id',
                                       'indicator_id',
                                       'workflow_id'),)

    def setup(self,
                 organisationsurvey_id,
                 indicator_id,
                 workflow_id=None,
                 published_status=None,
                 published_source=None,
                 published_comment=None,
                 published_format=None,
                 published_accepted=None,
                 ordinal_value=None,
                 id=None):
        self.organisationsurvey_id = organisationsurvey_id
        self.workflow_id = workflow_id
        self.indicator_id = indicator_id
        self.published_status = published_status
        self.published_source = published_source
        self.published_comment = published_comment
        self.published_format = published_format
        self.published_accepted = published_accepted
        self.ordinal_value = ordinal_value

        if id is not None:
            self.id = id

class PublishedFormat(db.Model):
    __tablename__ = 'publishedformat'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    title = Column(UnicodeText)
    format_class = Column(UnicodeText)
    format_value = Column(Float)
    
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

class PublishedStatus(db.Model):
    __tablename__ = 'publishedstatus'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    title = Column(UnicodeText)
    publishedstatus_class = Column(UnicodeText)
    publishedstatus_value = Column(Float)
    
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
    
class Workflow(db.Model):
    __tablename__='workflow'
    id = Column(Integer,primary_key=True)
    name = Column(UnicodeText)
    title = Column(UnicodeText)
    leadsto = Column(Integer, ForeignKey('workflow.id'))
    workflow_type = Column(Integer, ForeignKey('workflowtype.id'))
    duration = Column(Integer)
    
    def setup(self,
                 name,
                 title,
                 leadsto,
                 workflow_type=None,
                 duration=None,
                 id=None):
        self.name = name
        self.title = title
        self.leadsto = leadsto
        self.workflow_type = workflow_type
        self.duration = duration
        if id is not None:
            self.id = id

# WorkflowType: define what sort of workflow this should be.
#   Will initially be hardcoded but this should make it easier
#   to expand and define later.
class WorkflowType(db.Model):
    __tablename__='workflowtype'

    id = Column(Integer,primary_key=True)
    name = Column(UnicodeText)
    
    def setup(self,
                 name,
                 id=None):
        self.name = name
        if id is not None:
            self.id = id

class WorkflowNotification(db.Model):
    __tablename__='workflownotifications'
    id = Column(Integer, primary_key=True)
    workflow_from = Column(Integer, ForeignKey('workflow.id'))
    workflow_to = Column(Integer, ForeignKey('workflow.id'))
    workflow_notice = Column(UnicodeText)


class PackageTested(db.Model):
    __tablename__ = 'package_tested'
    package_id = Column(Integer, ForeignKey('package.id'), primary_key=True)
    runtime = Column(Integer, ForeignKey('package.id'), nullable=False)


class UserActivity(db.Model):
    __tablename__='useractivity'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('dquser.id'))
    activity_type = Column(Integer)
    activity_data = Column(UnicodeText)
    ip_address = Column(UnicodeText)
    activity_date = Column(DateTime)


class SamplingFailure(db.Model):
    __tablename__ = 'sampling_failure'
    organisation_id = Column(Integer, ForeignKey('organisation.id'), 
                             primary_key=True)
    test_id = Column(Integer, ForeignKey('test.id'),
                     primary_key=True)

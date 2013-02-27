from sqlalchemy import *
from db import app, db
from datetime import datetime

class PackageStatus(db.Model):
    __tablename__ = 'packagestatus'
    id = Column(Integer, primary_key=True)
    package_id = Column(Integer, ForeignKey('package.id'))
    status = Column(Integer)
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
    runtime_datetime = Column(DateTime)

    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return unicode(self.runtime_datetime)+u' '+unicode(self.id)

class PackageGroup(db.Model):
    __tablename__ = 'packagegroup'
    id = Column(Integer, primary_key=True)
    man_auto = Column(UnicodeText)
    name = Column(UnicodeText)
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
    package_name = Column(UnicodeText)
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

    def __init__(self, man_auto=None, source_url=None):
        if man_auto is not None:
            self.man_auto = man_auto
        if source_url is not None:
            self.source_url = source_url

    def __repr__(self):
        return self.source_url+u", "+self.id

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Tests - at activity or file level.
class Result(db.Model):
    __tablename__ = 'result'
    id = Column(Integer, primary_key=True)
    runtime_id = Column(Integer, ForeignKey('runtime.id'))
    package_id = Column(Integer, ForeignKey('package.id'))
    test_id = Column(Integer, ForeignKey('test.id'))
    result_data = Column(Integer)
    # result_identifier can be file or activity
    # The identifier for the element associated with this result
    # E.g. the releavnt activity identifier
    result_identifier = Column(UnicodeText)
    result_hierarchy = Column(Integer)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class AggregateResult(db.Model):
    __tablename__='aggregateresult'
    id = Column(Integer,primary_key=True)
    runtime_id=Column(Integer, ForeignKey('runtime.id'))
    package_id = Column(Integer, ForeignKey('package.id'))
    test_id = Column(Integer, ForeignKey('test.id'))
    result_hierarchy = Column(Integer)
    results_data = Column(Float)
    results_num = Column(Integer)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Test(db.Model):
    __tablename__ = 'test'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)
    test_group = Column(UnicodeText)
    file = Column(UnicodeText)
    line = Column(Integer)
    test_level = Column(Integer)
    active = Column(Boolean)

    def __repr__(self):
        return self.name+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class PublisherCondition(db.Model):
    __tablename__ = 'publishercondition'
    id = Column(Integer, primary_key=True)
    publisher_id = Column(Integer, ForeignKey('packagegroup.id'))
    test_id = Column(Integer, ForeignKey('test.id'))
    operation = Column(Integer) # show (1) or don't show (0) result
    condition = Column(UnicodeText) # activity level, hierarchy 2
    condition_value = Column(UnicodeText) # True, 2, etc.
    description = Column(UnicodeText)
    file = Column(UnicodeText)
    line = Column(Integer)
    active = Column(Boolean)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class TestCondition(db.Model):
    __tablename__ = 'testcondition'
    id = Column(Integer, primary_key=True)
    condition = Column(UnicodeText)
    description = Column(UnicodeText)
    file = Column(UnicodeText)
    line = Column(UnicodeText)
    test_level = Column(UnicodeText)
    active = Column(Boolean)

    def __repr__(self):
        return self.condition+u', '+unicode(self.id)

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# InfoResult
# ==> total amount of disbursements in this package
# e.g. 1 = total disbursements


class InfoResult(db.Model):
    __tablename__ = 'info_result'
    id = Column(Integer, primary_key=True)
    runtime_id = Column(Integer, ForeignKey('runtime.id'))
    package_id = Column(Integer, ForeignKey('package.id'))
    info_id = Column(Integer, ForeignKey('info_type.id'))
    result_data = Column(UnicodeText)
    

# InfoType
#

class InfoType(db.Model):
    __tablename__ = 'info_type'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)

    def __init__(self, man_auto, source_url):
        self.man_auto = man_auto
        self.source_url = source_url

    def __repr__(self):
        return self.source_url, self.id

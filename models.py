from sqlalchemy import *
from database import Base
from datetime import datetime

class Runtime(Base):
    __tablename__ = 'Runtime'
    id = Column(Integer, primary_key=True)
    runtime_datetime = Column(DateTime)

    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return self.runtime_datetime, self.id

class Package(Base):
    __tablename__ = 'Package'
    id = Column(Integer, primary_key=True)
    man_auto = Column(UnicodeText)
    source_url = Column(UnicodeText)
    package_ckan_id = Column(UnicodeText)
    package_name = Column(UnicodeText)
    package_title = Column(UnicodeText)

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
class Result(Base):
    __tablename__ = 'Result'
    id = Column(Integer, primary_key=True)
    runtime_id = Column(Integer, ForeignKey('Runtime.id'))
    package_id = Column(Integer, ForeignKey('Package.id'))
    test_id = Column(Integer, ForeignKey('Test.id'))
    result_data = Column(UnicodeText)
    # result_level can be file or activity
    result_level = Column(UnicodeText)
    result_identifier = Column(UnicodeText)

    def __init__(self, runtime_id=None, package_id=None, test_id=None, result_data=None, result_level=None, result_identifier=None):
        if self.runtime_id is not None: 
            self.runtime_id = runtime_id
        if self.package_id is not None: 
            self.package_id = package_id
        if self.test_id is not None: 
            self.test_id = test_id
        if self.result_data is not None: 
            self.result_data = result_data
        if self.result_level is not None: 
            self.result_level = result_level
        if self.result_identifier is not None: 
            self.result_identifier = result_identifier

    def __repr__(self):
        return self.source_url, self.id

class Test(Base):
    __tablename__ = 'Test'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)
    code = Column(UnicodeText)
    xpath = Column(Integer)

    def __init__(self, man_auto, source_url):
        self.man_auto = man_auto
        self.source_url = source_url

    def __repr__(self):
        return self.source_url, self.id

# InfoResult
# ==> total amount of disbursements in this package
# e.g. 1 = total disbursements


class InfoResult(Base):
    __tablename__ = 'InfoResult'
    id = Column(Integer, primary_key=True)
    runtime_id = Column(Integer, ForeignKey('Runtime.id'))
    package_id = Column(Integer, ForeignKey('Package.id'))
    info_id = Column(Integer, ForeignKey('InfoType.id'))
    result_data = Column(UnicodeText)

    def __init__(self, man_auto, source_url):
        self.man_auto = man_auto
        self.source_url = source_url

    def __repr__(self):
        return self.source_url, self.id

# InfoType
#

class InfoType(Base):
    __tablename__ = 'InfoType'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)

    def __init__(self, man_auto, source_url):
        self.man_auto = man_auto
        self.source_url = source_url

    def __repr__(self):
        return self.source_url, self.id

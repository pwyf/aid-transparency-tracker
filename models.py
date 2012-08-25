from sqlalchemy import *
from database import Base
from datetime import datetime

class Runtime(Base):
    __tablename__ = 'runtime'
    id = Column(Integer, primary_key=True)
    runtime_datetime = Column(DateTime)
    
    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return self.runtime_datetime, self.id

class Package(Base):
    __tablename__ = 'package'
    id = Column(Integer, primary_key=True)
    man_auto = Column(UnicodeText)
    source_url = Column(UnicodeText)
    package_ckan_id = Column(UnicodeText)
    package_name = Column(UnicodeText)
    package_title = Column(UnicodeText)

    def __init__(self, man_auto, source_url):
        self.man_auto = man_auto
        self.source_url = source_url

    def __repr__(self):
        return self.source_url, self.id

class Result(Base):
    __tablename__ = 'result'
    id = Column(Integer, primary_key=True)
    runtime_id = Column(UnicodeText)
    package_id = Column(UnicodeText)
    test_id = Column(UnicodeText)
    result_data = Column(UnicodeText)
    comments = Column(UnicodeText)

    def __init__(self, runtime_id, package_id, test_id, result_data, comments):
        self.runtime_id = runtime_id
        self.package_id = package_id
        self.test_id = test_id
        self.result_data = result_data
        self.comments = comments

    def __repr__(self):
        return self.source_url, self.id

class Tests(Base):
    __tablename__ = 'tests'
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    description = Column(UnicodeText)

    def __init__(self, man_auto, source_url):
        self.man_auto = man_auto
        self.source_url = source_url

    def __repr__(self):
        return self.source_url, self.id

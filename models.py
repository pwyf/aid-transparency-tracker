class runtime(db.Model):
    id = db.Column(Integer, primary_key=True)
    runtime_datetime = db.Column(DateTime)
    
    def __init__(self):
        self.runtime_datetime = datetime.utcnow()

    def __repr__(self):
        return self.runtime_datetime, self.id

class package(db.Model):
    id = db.Column(Integer, primary_key=True)
    man_auto = db.Column(UnicodeText)
    source_url = db.Column(UnicodeText)
    package_ckan_id = db.Column(UnicodeText)
    package_name = db.Column(UnicodeText)
    package_title = db.Column(UnicodeText)

    def __init__(self, man_auto, source_url):
        self.man_auto = man_auto
        self.source_url = source_url

    def __repr__(self):
        return self.source_url, self.id

class result(db.Model):
    id = db.Column(Integer, primary_key=True)
    runtime_id = db.Column(UnicodeText)
    package_id = db.Column(UnicodeText)
    test_id = db.Column(UnicodeText)
    result_data = db.Column(UnicodeText)
    comments = db.Column(UnicodeText)

    def __init__(self, runtime_id, package_id, test_id, result_data, comments):
        self.runtime_id = runtime_id
        self.package_id = package_id
        self.test_id = test_id
        self.result_data = result_data
        self.comments = comments

    def __repr__(self):
        return self.source_url, self.id

class tests(db.Model):
    id = db.Column(Integer, primary_key=True)
    name = db.Column(UnicodeText)
    description = db.Column(UnicodeText)

    def __init__(self, man_auto, source_url):
        self.man_auto = man_auto
        self.source_url = source_url

    def __repr__(self):
        return self.source_url, self.id

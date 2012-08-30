from iatidataquality import models, db
import re

hardcoded_tests = [
    (-2, 'url_exists', "Check that the xml file actually exists."),
    (-3, 'valid_xml', "Check that xml is valid"),
    (-4, 'schema_conformance', "Check that xml conforms to schema")
]
for hardcoded_test in hardcoded_tests:
    test = models.Test()
    test.id = hardcoded_test[0]
    test.name = hardcoded_test[1]
    test.description =  hardcoded_test[2]
    db.session.add(test)
    db.session.commit()

comment = re.compile('#')
blank = re.compile('^$')
filename = 'activity_tests.txt' 
for n, line in enumerate(open('tests/'+filename)):
    if comment.match(line) or blank.match(line):
        continue
    test = models.Test()
    test.name = line.strip('\n')
    test.file = filename
    test.line = n+1
    #test.description = value
    #test.test_group = value
    db.session.add(test)
    db.session.commit()



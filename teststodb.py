from iatidataquality import models, db
import re

hardcoded_tests = [
    (-2, 'url_exists', "Check that the xml file actually exists."),
    (-3, 'valid_xml', "Check that xml is valid"),
    (-4, 'schema_conformance', "Check that xml conforms to schyema")
]
for hardcoded_test in hardcoded_tests:
    if models.Test.query.filter(models.Test.id==hardcoded_test[0]).first():
        continue
    test = models.Test()
    test.id = hardcoded_test[0]
    test.name = hardcoded_test[1]
    test.description =  hardcoded_test[2]
    test.test_level = 2 # File
    test.active = True
    db.session.add(test)
    db.session.commit()

comment = re.compile('#')
conditions = re.compile('##C')
blank = re.compile('^$')
filename = 'activity_tests.txt' 
models.Test.query.filter(models.Test.test_level==1).update({models.Test.active: False})
for n, line in enumerate(open('tests/'+filename)):
    if conditions.match(line):
        print "broken"
        break
    if comment.match(line) or blank.match(line):
        print "found"
        continue
    testtext = line.strip('\n')
    test = models.Test.query.filter(models.Test.name==testtext).first()
    if not test:
        test = models.Test()
    test.name = testtext
    test.file = filename
    test.line = n+1
    test.test_level = 1 # Activity
    test.active = True
    #test.description = value
    #test.test_group = value
    db.session.add(test)
    db.session.commit()



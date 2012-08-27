from iatidataquality import models, db

test = models.Test()

import sys
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

import ast
filename = 'activity_tests' 
M = ast.parse(open('tests/'+filename+'.py').read())
for f in M.body:
    if isinstance(f, ast.FunctionDef):
        test = models.Test()
        test.name = f.name
        test.file = filename
        text =  ast.get_docstring(f)
        for line in text.split('\n'):
            key,value = line.split(': ')
            if key == 'Description':
                test.description = value
            elif key == 'Group':
                test.test_group = value
        db.session.add(test)
        db.session.commit()



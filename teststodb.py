import models
import database

import ast
M = ast.parse(open('iati_dq/activity_tests.py').read())
for f in M.body:
    if isinstance(f, ast.FunctionDef):
        test = models.Test()
        test.name = f.name
        text =  ast.get_docstring(f)
        for line in text.split('\n'):
            key,value = line.split(':')
            if key == 'Description':
                test.description = value
            elif key == 'Group':
                test.test_group = value
        database.db_session.add(test)
        database.db_session.commit()



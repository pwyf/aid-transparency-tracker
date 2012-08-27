import models
import database

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
        database.db_session.add(test)
        database.db_session.commit()



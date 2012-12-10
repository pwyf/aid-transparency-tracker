from iatidataquality import models, db
import re

comment = re.compile('^#')
blank = re.compile('^$')
filename = 'activity_tests_conditions.txt' 
models.TestCondition.query.update({models.TestCondition.active: False})
for n, line in enumerate(open('tests/'+filename)):
    if comment.match(line) or blank.match(line):
        continue
    conditiontext = line.strip('\n')
    try:
        result = re.split(" # ", conditiontext)
    except:
        pass
    if result:
        conditiontext = result[0]
        try:
            description = result[1]
        except IndexError:
            description = result[0]   
    condition = models.TestCondition.query.filter(models.TestCondition.condition==conditiontext).first()
    if not condition:
        condition = models.TestCondition()
    condition.condition = conditiontext
    condition.description = description
    condition.file = filename
    condition.line = n+1
    condition.test_level = 1 # Activity
    condition.active = True
    db.session.add(condition)
    db.session.commit()



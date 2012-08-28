import re
from functools import partial

def exist(activity, groups):
    return bool(activity.find(groups[0]).text)
def exist_or(activity, groups):
    return (bool(activity.find(element).text) or
            bool(activity.find(element2).text))
def exist_xor(activity, groups):
    return (bool(activity.find(element).text) != 
            bool(activity.find(element2).text))
def exist_times(actvity, groups):
    if groups[1] == "once":
        return False
def text(activity, groups):
    return bool(activity.find(groups[0]).text)

def fail(line):
    print 'Fail '+line

mappings = [
    ('(\S*) should have an? (\S*) with (\S*) (\S*)', exist),
    ('(\S*) should have an? (\S*)', exist),
    ('(\S*) should have text with more than (\S*) characters', text_chars),
    ('(\S*) should have text', text),
    ('(\S*) attribute (\S*) should sum to (.*)', exist),
    ('(\S*) attribute (\S*) should be an? (.*)', exist),
    ('(\S*) should be an? (.*)', exist),
    ('(\S*) should exist (\S*)', exist_times),
    ('(\S*) with (\S*) (\S*) should exist', exist),
    ('only one of (\S*) or (\S*) should exist', exist_xor),
    ('(\S*) or (\S*) should exist', exist_or),
    ('(\S*) should exist', exist),
    ('(.*)', fail)
]

for line in open('tests/activity_tests.txt'):
    for mapping in mappings:
        m = re.match('^'+mapping[0]+'$', line)
        if m:
            try:
                print partial(mapping[1], groups=m.groups())
            except TypeError:
                pass 
            break

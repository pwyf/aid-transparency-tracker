import re
import sys
from functools import partial

mappings = []

def add(regex):
    def append_to_mappings(fn):
        global mappings
        mappings.append((re.compile(regex),fn))
        return fn
    return append_to_mappings

def add_partial(regex):
    def append_to_mappings(fn):
        global mappings
        def partial_fn(groups):
            return partial(fn, groups=groups)
        mappings.append((re.compile(regex), partial_fn))
        return fn
    return append_to_mappings

@add_partial('(\S*) should have an? (\S*) with (\S*) (\S*)')
def subelement_with_attribute_exists(activity, groups):
    return bool(activity.xpath("//{}/{}/@{}='{}'".format(*groups)))

@add_partial('(\S*) should have an? (\S*)')
def subelement_exists(activity, groups):
    return bool(activity.xpath("//{}/{}".format(*groups)))

@add_partial('(\S*) should have text with more than (\S*) characters')
def text_chars(activity, groups):
    return ((thetitle is not None) and (len(thetitle)>10))

@add_partial('(\S*) should have text')
def text(activity, groups):
    return bool(activity.find(groups[0]).text)

@add_partial('(\S*) attribute (\S*) should sum to (.*)')
def attribute_sum(activity, groups):
    return bool(
        reduce(lambda x,y:x+int(y.get('percentage')),
        activity.findall(groups[0]), 0)
                == 100)

@add_partial('(\S*) attribute (\S*) should be an? (.*)')
def thisisbroke(activity, groups):
    return False
    #for element in activity.findall(group[0]):
#IMPLEMENTME
# try: int(activi)

@add_partial('(\S*) should exist (\S*)')
def exist_times(activity, groups):
    if groups[1] == "once":
        return False
#IMPLEMENTME


@add_partial('only one of (\S*) or (\S*) should exist')
def exist_xor(activity, groups):
    return (bool(activity.find(element).text) != 
            bool(activity.find(element2).text))

@add_partial('(\S*) or (\S*) should exist')
def exist_or(activity, groups):
    return (bool(activity.find(element).text) or
            bool(activity.find(element2).text))

@add_partial('(\S*) should exist')
def exist(activity, groups):
    return bool(activity.find(groups[0]).text)

@add_partial('(.*)')
def fail(line):
    print 'Fail '+line



for line in open('tests/activity_tests.txt'):
    for mapping in mappings:
        m = mapping[0].match(line)
        if m:
            try:
                print mapping[1]
            except TypeError:
                pass 
            break

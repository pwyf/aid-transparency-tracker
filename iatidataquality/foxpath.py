import re
import itertools
import mapping

class TestSyntaxError(Exception): pass

comment = re.compile('#')
blank = re.compile('^$')

def ignore_line(line):
    return bool(comment.match(line) or blank.match(line))

def generate_test_functions(tests):
    mappings = mapping.generate_mappings()

    def get_mappings(ms, line):
        for regex, lam in ms:
            yield regex.match(line), lam

    first_true = lambda tupl: bool(tupl.__getitem__(0))

    test_functions = {}

    tests = itertools.ifilter(lambda test: test.test_level == 1, tests)
    tests = itertools.ifilter(lambda test: not ignore_line(test.name), tests)

    def function_for_test(test):
        line = test.name

        match_data = get_mappings(mappings, line)
        matching_mappings = itertools.ifilter(first_true, match_data)

        try:
            m, lam = matching_mappings.next()
        except StopIteration:
            raise TestSyntaxError(line)

        return lam(m.groups())

    def id_of_test(test): return test.id

    def test_data(test):
        f = function_for_test(test)
        test_id = id_of_test(test)
        return test_id, f

    return dict(itertools.imap(test_data, tests))

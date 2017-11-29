from datetime import datetime
import json
import logging
from os.path import dirname, join
import re

from behave import given, then
from bdd_tester.exceptions import StepException


@given('file is an organisation file')
def given_org_file(context):
    if context.filetype != 'org':
        raise StepException(context, 'Not an organisation file')


@given('this test involves both organisation and activity files')
def given_mixed_content(context):
    raise StepException(context, 'Not possible to test')


@then('skip it')
def then_skip_it(context):
    pass


# NB the original PWYF test also checked non-empty
@then('`{xpath_expression}` should be present')
def then_is_present(context, xpath_expression):
    vals = context.xml.xpath(xpath_expression)
    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression)
        raise StepException(context, msg)


@then('every `{xpath_expression}` should be on the {codelist} codelist')
def then_every_on_codelist(context, xpath_expression, codelist):
    vals = context.xml.xpath(xpath_expression)

    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression)
        raise StepException(context, msg)

    codelist_path = join(dirname(__file__), 'codelists', '2',
                         codelist + '.json')
    with open(codelist_path) as f:
        j = json.load(f)
    codes = [x['code'] for x in j['data']]

    invalid_vals = []
    success = True
    for val in vals:
        if val not in codes:
            success = False
            invalid_vals.append(val)

    if not success:
        msg = '{invalid_vals} {isare} not on the {codelist} codelist'.format(
            invalid_vals=', '.join(invalid_vals),
            isare='is' if len(invalid_vals) == 1 else 'are',
            codelist=codelist,
        )
        raise StepException(context, msg)

    assert(True)


@then('at least one `{xpath_expression}` should be on the {codelist} codelist')
def then_at_least_one_on_codelist(context, xpath_expression, codelist):
    vals = context.xml.xpath(xpath_expression)

    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression)
        raise StepException(context, msg)

    codelist_path = join('codelists', '2', codelist + '.json')
    with open(codelist_path) as f:
        j = json.load(f)
    codes = [x['code'] for x in j['data']]

    for val in vals:
        if val in codes:
            assert(True)
            return

    msg = '{invalid_vals} {isare} not on the {codelist} codelist'.format(
        invalid_vals=', '.join(vals),
        isare='is' if len(vals) == 1 else 'are',
        codelist=codelist,
    )
    raise StepException(context, msg)


@given('the activity is current')
def given_activity_is_current(context):
    try:
        context.execute_steps('given `activity-status/@code` is 2')
        return
    except AssertionError as e:
        pass

    end_planned = 'activity-date[@type="3"]/@iso-date |' + \
                  'activity-date[@type="3"]/text() |' + \
                  'activity-date[@type="end-planned"]/@iso-date |' + \
                  'activity-date[@type="end-planned"]/text()'
    try:
        inp = 'given `{}` is less than 12 months ago'.format(end_planned)
        context.execute_steps(inp)
        assert(True)
        return
    except AssertionError as e:
        pass

    end_planned = 'activity-date[@type="4"]/@iso-date |' + \
                  'activity-date[@type="4"]/text() |' + \
                  'activity-date[@type="end-actual"]/@iso-date |' + \
                  'activity-date[@type="end-actual"]/text()'
    try:
        inp = 'given `{}` is less than 12 months ago'.format(end_planned)
        context.execute_steps(inp)
        assert(True)
        return
    except AssertionError as e:
        pass

    xpath_expr = 'transaction[transaction-type/@code="C"] |' + \
                 'transaction[transaction-type/@code="D"] |' + \
                 'transaction[transaction-type/@code="E"] |' + \
                 'transaction[transaction-type/@code="2"] |' + \
                 'transaction[transaction-type/@code="3"] |' + \
                 'transaction[transaction-type/@code="4"]'
    transactions = context.xml.xpath(xpath_expr)
    for transaction in transactions:
        transaction_date = 'transaction-date/@iso-date'
        inp = 'given `{}` is less than 12 months ago'.format(transaction_date)
        try:
            context.execute_steps(inp)
            assert(True)
            return
        except AssertionError as e:
            pass

    msg = 'Activity is not current'
    raise StepException(context, msg)


@then('`{xpath_expression}` should have at least {reqd_chars:d} characters')
def then_at_least_x_chars(context, xpath_expression, reqd_chars):
    vals = context.xml.xpath(xpath_expression)
    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression)
        raise StepException(context, msg)

    most_chars, most_str = max([(len(val), val) for val in vals])
    result = most_chars > reqd_chars

    if not result:
        msg = '`{}` has fewer than {} characters (it has {})'.format(
            xpath_expression,
            reqd_chars,
            most_chars,
        )
        raise StepException(context, msg)


@given('`{xpath_expression}` is one of {consts}')
def given_is_one_of_consts(context, xpath_expression, consts):
    consts_list = re.split(r', | or ', consts)
    vals = context.xml.xpath(xpath_expression)
    if len(vals) == 0:
        # explain = '{vals_explain} should be one of {const_explain}. ' + \
        #           'However, the activity doesn\'t contain that element'
        assert(True)
        return
    for val in vals:
        if val in consts_list:
            # explain = '{vals_explain} is one of {const_explain} ' + \
            #           '(it\'s {val})'
            assert(True)
            return
    msg = '`{}` is not one of {} (it\'s {})'.format(
        xpath_expression,
        consts,
        val,
    )
    raise StepException(context, msg)


@given('`{xpath_expression}` is not one of {consts}')
def given_is_not_one_of_consts(context, xpath_expression, consts):
    consts_list = re.split(r', | or ', consts)
    vals = context.xml.xpath(xpath_expression)
    if len(vals) == 0:
        assert(True)
        return
    for val in vals:
        if val in consts_list:
            msg = '`{}` is one of {} (it\'s {})'.format(
                xpath_expression,
                consts,
                val,
            )
            raise StepException(context, msg)
    assert(True)
    return


def mkdate(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


@given('`{xpath_expression}` is at least {months_ahead:d} months ahead')
def given_at_least_x_months_ahead(context, xpath_expression, months_ahead):
    dates = context.xml.xpath(xpath_expression)

    if len(dates) == 0:
        msg = '`{0}` is not present, so assuming it is not at ' + \
              'least {1} months ahead'.format(
                  xpath_expression,
                  months_ahead,
              )
        raise StepException(context, msg)

    valid_dates = list(filter(
        lambda x: x, [mkdate(date_str) for date_str in dates]))
    if not valid_dates:
        # explain = '{date} does not use format YYYY-MM-DD, so ' \
        #           'assuming it is not at least {months} months ahead'
        # explain = explain.format(date=dates[0], months=months)
        msg = '`{}` does not use format YYYY-MM-DD, so assuming it ' + \
              'is not at least {} months ahead'.format(
                  dates[0],
                  months_ahead,
              )
        raise StepException(context, msg)

    max_date = max(valid_dates)
    prefix = ''
    if len(valid_dates) > 1 and max_date != min(valid_dates):
        prefix = 'the latest '

    year_diff = max_date.year - context.today.year
    month_diff = 12 * year_diff + max_date.month - context.today.month
    if month_diff == months_ahead:
        success = max_date.day > context.today.day
    else:
        success = month_diff > months_ahead
    if not success:
        msg = '{}`{}` is less than {} months ahead'.format(
            prefix,
            xpath_expression,
            months_ahead,
        )
        raise StepException(context, msg)


@given('`{xpath_expression}` is less than {months_ago:d} months ago')
def given_is_less_than_x_months_ago(context, xpath_expression, months_ago):
    dates = context.xml.xpath(xpath_expression)

    if len(dates) == 0:
        msg = '{xpath_expression} is not present, so assuming it is ' + \
              'not less than {months_ago} months ago'
        msg = msg.format(xpath_expression=xpath_expression,
                         months_ago=months_ago)
        raise StepException(context, msg)

    valid_dates = list(filter(
        lambda x: x, [mkdate(date_str) for date_str in dates]))
    if not valid_dates:
        msg = '{xpath_expression} ({date}) does not use format ' + \
              'YYYY-MM-DD, so assuming it is not less than {months_ago} ' + \
              'months ago'
        msg = msg.format(xpath_expression=xpath_expression,
                         date=dates[0], months_ago=months_ago)
        raise StepException(context, msg)

    max_date = max(valid_dates)
    prefix = ''
    if len(valid_dates) > 1 and max_date != min(valid_dates):
        prefix = 'the most recent '

    current_date = context.today
    if max_date > current_date:
        # msg = '{prefix}{xpath_expression} ({max_date}) is in the future'
        assert(True)
        return
    year_diff = current_date.year - max_date.year
    month_diff = 12 * year_diff + current_date.month - max_date.month
    if month_diff == months_ago:
        result = max_date.day > current_date.day
    else:
        result = month_diff < months_ago

    if result:
        assert(True)
        return

    msg = '{prefix}{xpath_expression} ({max_date}) is not less than ' + \
          '{months_ago} months ago'
    msg = msg.format(prefix=prefix, xpath_expression=xpath_expression,
                     max_date=max_date, months_ago=months_ago)
    raise StepException(context, msg)


@given('`{xpath_expression}` is not {const}')
def given_is_not_const(context, xpath_expression, const):
    vals = context.xml.xpath(xpath_expression)
    for val in vals:
        if val == const:
            msg = '`{}` is {}'.format(
                xpath_expression,
                const,
            )
            raise StepException(context, msg)
    assert(True)


@given('`{xpath_expression}` is {const}')
def given_is_const(context, xpath_expression, const):
    vals = context.xml.xpath(xpath_expression)
    for val in vals:
        if val == const:
            assert(True)
            return
    msg = '`{}` is not {} (it\'s {})'.format(
        xpath_expression,
        const,
        val,
    )
    raise StepException(context, msg)


@then('`{xpath_expression}` should be available forward {period}')
def then_is_available_forward(context, xpath_expression, period):
    vals = context.xml.xpath(xpath_expression)

    def max_date(dates, default):
        dates = list(filter(
            lambda x: x is not None, [mkdate(d) for d in dates]))
        if dates == []:
            return default
        return max(dates)

    # Window start is from today onwards. We're only interested in budgets
    # that start or end after today.

    # Window period is for the next 365 days. We don't want to look later
    # than that; we're only interested in budgets that end before then.
    #
    # We get the latest date for end and start; 365 days fwd
    # if there are no dates

    def check_after(element, today):
        dates = element.xpath('period-start/@iso-date|period-end/@iso-date')
        dates = list(filter(
            lambda x: x is not None, [mkdate(d) for d in dates]))
        return any([date >= today for date in dates])

    def max_budget_length(element, max_budget_length):
        # NB this will error if there's no period-end/@iso-date
        try:
            start = mkdate(element.xpath('period-start/@iso-date')[0])
            end = mkdate(element.xpath('period-end/@iso-date')[0])
            within_length = ((end-start).days <= max_budget_length)
        except TypeError:
            return False
        return within_length

    # We set a maximum number of days for which a budget can last,
    # depending on the number of quarters that should be covered.
    if period == 'quarterly':
        max_days = 94
    else:
        # annually
        max_days = 370

    # A budget has to be:
    # 1) period-end after reference date
    # 2) a maximum number of days, depending on # of qtrs.
    for element in vals:
        after_ref = check_after(element, context.today)
        within_length = max_budget_length(element, max_days)
        if after_ref and within_length:
            assert(True)
            return

    msg = 'Failed'
    raise StepException(context, msg)


@then('`{xpath_expression}` should be available {years:d} year forward')
@then('`{xpath_expression}` should be available {years:d} years forward')
def then_is_available_x_years_forward(context, xpath_expression, years):
    budgets = context.xml.xpath(xpath_expression)
    # TODO
    raise StepException(context, '')


@then('`{xpath_expression1}` should start with either ' +
      '`{xpath_expression2}` or `{xpath_expression3}`')
def then_should_start_with_either(context, xpath_expression1,
                                  xpath_expression2, xpath_expression3):
    vals = context.xml.xpath(xpath_expression1)
    prefix1 = context.xml.xpath(xpath_expression2)
    prefix2 = context.xml.xpath(xpath_expression3)

    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression1)
        raise StepException(context, msg)

    target = vals[0]

    if len(prefix1) > 0 and len(prefix1[0]) > 0:
        prefix1 = prefix1[0]
        if target.startswith('{}-'.format(prefix1)):
            assert(True)
            return
        else:
            msg = '`{}` doesn\'t start with {}'.format(
                xpath_expression1,
                prefix1
            )
    elif len(prefix2) and len(prefix2[0]) > 0:
        prefix2 = prefix2[0]
        if target.startswith('{}-'.format(prefix2)):
            assert(True)
            return
        else:
            msg = '`{}` doesn\'t start with {}'.format(
                xpath_expression1,
                prefix2
            )
    else:
        msg = '`{}` or `{}` not found'.format(
            xpath_expression2, xpath_expression3)
    raise StepException(context, msg)


def either_or(context, tmpl, xpath_expressions):
    exceptions = []
    for xpath_expression in xpath_expressions:
        try:
            context.execute_steps(tmpl.format(
                expression=xpath_expression)
            )
            assert(True)
            return
        except AssertionError as e:
            msg = str(e).split('StepException: ')[1].strip()
            exceptions.append(msg)

    msg = ' and '.join(exceptions)
    raise StepException(context, msg)


@given('either `{xpath_expression1}` or `{xpath_expression2}` {statement}')
def given_either_or(context, xpath_expression1, xpath_expression2, statement):
    xpath_expressions = [xpath_expression1, xpath_expression2]
    tmpl = 'given `{{expression}}` {statement}'.format(
        statement=statement,
    )
    either_or(context, tmpl, xpath_expressions)


@then('either `{xpath_expression1}` or `{xpath_expression2}` {statement}')
def then_either_or(context, xpath_expression1, xpath_expression2, statement):
    xpath_expressions = [xpath_expression1, xpath_expression2]
    tmpl = 'then `{{expression}}` {statement}'.format(
        statement=statement,
    )
    either_or(context, tmpl, xpath_expressions)


@then('either every `{xpath_expression1}` or ' +
      '`{xpath_expression2}` {statement}')
def then_either_every_or(context, xpath_expression1,
                         xpath_expression2, statement):
    xpath_expressions = [xpath_expression1, xpath_expression2]
    tmpl = 'then every `{{expression}}` {statement}'.format(
        statement=statement,
    )
    either_or(context, tmpl, xpath_expressions)

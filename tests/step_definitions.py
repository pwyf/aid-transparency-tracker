from datetime import datetime, timedelta
import re

from foxpath import given, then, StepException


@given(r'file is an organisation file')
def given_org_file(xml, **kwargs):
    if xml.tag != 'iati-organisation':
        raise StepException('Not an organisation file')


@given(r'this test involves both organisation and activity files')
def given_mixed_content(xml, **kwargs):
    raise StepException('Not possible to test')


@given(r'an activity')
def an_activity(xml, **kwargs):
    pass


@then(r'skip it')
def then_skip_it(xml, **kwargs):
    pass


# NB the original PWYF test also checked non-empty
@then(r'`([^`]+)` should be present')
def then_is_present(xml, xpath_expression, **kwargs):
    vals = xml.xpath(xpath_expression)
    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression)
        raise StepException(msg)


@then(r'every `([^`]+)` should be on the ([^ ]+) codelist')
def then_every_on_codelist(xml, xpath_expression, codelist, **kwargs):
    vals = xml.xpath(xpath_expression)

    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression)
        raise StepException(msg)

    codes = kwargs.get('codelists', {}).get(codelist, [])

    invalid_vals = []
    success = True
    for val in vals:
        if val not in codes:
            success = False
            invalid_vals.append(val)

    if not success:
        msg = '{invalid_vals} {isare} not on the ' + \
              '{codelist} codelist'
        msg = msg.format(
            invalid_vals=', '.join(invalid_vals),
            isare='is' if len(invalid_vals) == 1 else 'are',
            codelist=codelist,
        )
        raise StepException(msg)

    assert(True)


@then(r'at least one `([^`]+)` should be on the ([^ ]+) codelist')
def then_at_least_one_on_codelist(xml, xpath_expression, codelist, **kwargs):
    vals = xml.xpath(xpath_expression)

    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression)
        raise StepException(msg)

    codes = kwargs.get('codelists', {}).get(codelist, [])

    for val in vals:
        if val in codes:
            assert(True)
            return

    msg = '{invalid_vals} {isare} not on the {codelist} codelist'.format(
        invalid_vals=', '.join(vals),
        isare='is' if len(vals) == 1 else 'are',
        codelist=codelist,
    )
    raise StepException(msg)


@given(r'the activity is current')
def given_activity_is_pretend_current(xml, **kwargs):
    # This is a sneaky hack, just to speed things up.
    # We actually apply the "then it should be current"
    # test separately, and filter all activities on
    # that.
    #
    # It's just faster that way.
    pass


@then(r'it should be current')
def then_activity_is_really_current(xml, **kwargs):
    try:
        given_is_const(xml, 'activity-status/@code', '2')
        return
    except StepException:
        pass

    end_planned = 'activity-date[@type="3"]/@iso-date |' + \
                  'activity-date[@type="end-planned"]/@iso-date'
    try:
        given_is_less_than_x_months_ago(xml, end_planned, 12, **kwargs)
        assert(True)
        return
    except StepException:
        pass

    end_actual = 'activity-date[@type="4"]/@iso-date |' + \
                 'activity-date[@type="end-actual"]/@iso-date'
    try:
        given_is_less_than_x_months_ago(xml, end_actual, 12, **kwargs)
        assert(True)
        return
    except StepException:
        pass

    xpath_expr = 'transaction[transaction-type/@code="C"] |' + \
                 'transaction[transaction-type/@code="D"] |' + \
                 'transaction[transaction-type/@code="E"] |' + \
                 'transaction[transaction-type/@code="2"] |' + \
                 'transaction[transaction-type/@code="3"] |' + \
                 'transaction[transaction-type/@code="4"]'
    transactions = xml.xpath(xpath_expr)
    for transaction in transactions:
        transaction_date = 'transaction-date/@iso-date'
        try:
            given_is_less_than_x_months_ago(transaction, transaction_date, 12, **kwargs)
            assert(True)
            return
        except StepException:
            pass

    msg = 'Activity is not current'
    raise StepException(msg)


@then(r'`([^`]+)` should have at least (\d+) characters')
def then_at_least_x_chars(xml, xpath_expression, reqd_chars, **kwargs):
    reqd_chars = int(reqd_chars)
    vals = xml.xpath(xpath_expression)
    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression)
        raise StepException(msg)

    most_chars, most_str = max([(len(val), val) for val in vals])
    result = most_chars >= reqd_chars

    if not result:
        msg = '`{}` has fewer than {} characters (it has {})'.format(
            xpath_expression,
            reqd_chars,
            most_chars,
        )
        raise StepException(msg)


@given(r'`([^`]+)` is one of ((?:\w+, )*\w+ or \w+)')
def given_is_one_of_consts(xml, xpath_expression, consts, **kwargs):
    consts_list = re.split(r', | or ', consts)
    vals = xml.xpath(xpath_expression)
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
    raise StepException(msg)


@given(r'`([^`]+)` is not any of ((?:\w+, )*\w+ or \w+)')
def given_is_not_one_of_consts(xml, xpath_expression, consts, **kwargs):
    consts_list = re.split(r', | or ', consts)
    vals = xml.xpath(xpath_expression)
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
            raise StepException(msg)
    assert(True)
    return


def mkdate(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return None


@given(r'`([^`]+)` is at least (\d+) months ahead')
def given_at_least_x_months_ahead(xml, xpath_expression,
                                  months_ahead, **kwargs):
    dates = xml.xpath(xpath_expression)
    months_ahead = int(months_ahead)

    if len(dates) == 0:
        msg = '`{0}` is not present, so assuming it is not at ' + \
              'least {1} months ahead'
        msg = msg.format(
                  xpath_expression,
                  months_ahead,
              )
        raise StepException(msg)

    valid_dates = list(filter(
        lambda x: x, [mkdate(date_str) for date_str in dates]))
    if not valid_dates:
        # explain = '{date} does not use format YYYY-MM-DD, so ' \
        #           'assuming it is not at least {months} months ahead'
        # explain = explain.format(date=dates[0], months=months)
        msg = '`{}` does not use format YYYY-MM-DD, so assuming it ' + \
              'is not at least {} months ahead'
        msg = msg.format(
                  dates[0],
                  months_ahead,
              )
        raise StepException(msg)

    max_date = max(valid_dates)
    prefix = ''
    if len(valid_dates) > 1 and max_date != min(valid_dates):
        prefix = 'the latest '

    today = kwargs.get('today')
    year_diff = max_date.year - kwargs.get('today').year
    month_diff = 12 * year_diff + max_date.month - today.month
    if month_diff == months_ahead:
        success = max_date.day >= today.day
    else:
        success = month_diff > months_ahead
    if not success:
        msg = '{}`{}` is less than {} months ahead'.format(
            prefix,
            xpath_expression,
            months_ahead,
        )
        raise StepException(msg)


@given(r'`([^`]+)` is less than (\d+) months ago')
def given_is_less_than_x_months_ago(xml, xpath_expression,
                                    months_ago, **kwargs):
    dates = xml.xpath(xpath_expression)

    if len(dates) == 0:
        msg = '{xpath_expression} is not present, so assuming it is ' + \
              'not less than {months_ago} months ago'
        msg = msg.format(xpath_expression=xpath_expression,
                         months_ago=months_ago)
        raise StepException(msg)

    valid_dates = list(filter(
        lambda x: x, [mkdate(date_str) for date_str in dates]))
    if not valid_dates:
        msg = '{xpath_expression} ({date}) does not use format ' + \
              'YYYY-MM-DD, so assuming it is not less than {months_ago} ' + \
              'months ago'
        msg = msg.format(xpath_expression=xpath_expression,
                         date=dates[0], months_ago=months_ago)
        raise StepException(msg)

    max_date = max(valid_dates)
    prefix = ''
    if len(valid_dates) > 1 and max_date != min(valid_dates):
        prefix = 'the most recent '

    current_date = kwargs.get('today')
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
    raise StepException(msg)


@given(r'`([^`]+)` is not ([^ ]+)')
def given_is_not_const(xml, xpath_expression, const, **kwargs):
    vals = xml.xpath(xpath_expression)
    for val in vals:
        if val == const:
            msg = '`{}` is {}'.format(
                xpath_expression,
                const,
            )
            raise StepException(msg)
    assert(True)


@given(r'`([^`]+)` is ([^ ]+)')
def given_is_const(xml, xpath_expression, const, **kwargs):
    vals = xml.xpath(xpath_expression)
    for val in vals:
        if val == const:
            assert(True)
            return
    msg = '`{}` is not {} (it\'s {})'.format(
        xpath_expression,
        const,
        val,
    )
    raise StepException(msg)


@then(r'`([^`]+)` should be available forward (annually|quarterly)')
def then_is_available_forward(xml, xpath_expression, period, **kwargs):
    vals = xml.xpath(xpath_expression)

    # Window start is from the reference date onwards.
    # We're only interested in budgets that start or end
    # after the reference date.

    # Window period is for the 365 days following the reference date.
    # We don't want to look later than that; we're only interested
    # in budgets that end before then.
    #
    # We get the latest date for end and start; 365 days forward
    # if there are no dates

    def check_after(element, today):
        dates = element.xpath('period-start/@iso-date | period-end/@iso-date')
        dates = list(filter(
            lambda x: x is not None, [mkdate(d) for d in dates]))
        return any([date >= today for date in dates])

    def max_budget_length(element, max_budget_length):
        try:
            start = mkdate(element.xpath('period-start/@iso-date')[0])
            end = mkdate(element.xpath('period-end/@iso-date')[0])
            within_length = ((end-start).days <= max_budget_length)
        except TypeError:
            return False
        except IndexError:
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
        after_ref = check_after(element, kwargs.get('today'))
        within_length = max_budget_length(element, max_days)
        if after_ref and within_length:
            assert(True)
            return

    msg = 'Failed'
    raise StepException(msg)


@then(r'`([^`]+)` should be available (\d+) years? forward')
def then_is_available_x_years_forward(xml, xpath_expression,
                                      years, **kwargs):
    budgets = xml.xpath(xpath_expression)
    today = kwargs.get('today')
    years = int(years)

    for budget in budgets:
        try:
            budget_end_str = budget.find('period-end').get('iso-date')
        except AttributeError:
            continue
        budget_end = mkdate(budget_end_str)
        if budget_end is None:
            continue
        future_date = today + timedelta(days=(365 * (years - 1)))
        future_plus_oneyear = future_date + timedelta(days=365)

        if budget_end >= future_date:
            if budget_end <= future_plus_oneyear:
                return True

    msg = '{} isn\'t between {} and {}'.format(
        budget_end, future_date, future_plus_oneyear
        )
    raise StepException(msg)


@then(r'`([^`]+)` should start with either `([^`]+)` or `([^`]+)`')
def then_should_start_with_either(xml, xpath_expression1, xpath_expression2,
                                  xpath_expression3, **kwargs):
    vals = xml.xpath(xpath_expression1)

    if len(vals) == 0:
        msg = '`{}` not found'.format(xpath_expression1)
        raise StepException(msg)

    target = vals[0]

    prefixes = []
    for xpath in [xpath_expression2, xpath_expression3]:
        prefix = xml.xpath(xpath)
        if len(prefix) > 0 and len(prefix[0]) > 0:
            prefixes.append(prefix[0])

    if prefixes == []:
        msg = '`{}` or `{}` not found'.format(
            xpath_expression2, xpath_expression3)
        raise StepException(msg)

    for prefix in prefixes:
        if target.startswith('{}-'.format(prefix)):
            assert(True)
            return

    msg = '{} doesn\'t start with either `{}` or `{}`'.format(
        target, xpath_expression2, xpath_expression3)
    raise StepException(msg)


@given(r'either `([^`]+)` is present, or `([^`]+)` is one of ' +
       r'((?:\w+, )*\w+ or \w+)')
def given_either_or(xml, xpath_expression1, xpath_expression2,
                    consts, **kwargs):
    try:
        then_is_present(xml, xpath_expression1, **kwargs)
        return
    except StepException:
        pass

    given_is_one_of_consts(xml, xpath_expression2, consts, **kwargs)

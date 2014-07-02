from lxml import etree
import datetime
import re
from iatidq import dqcodelists

# Tested against:
#   asdb-org.xml; minbuza_nl-organisation.xml; dfid-org.xml; 
#   acdi_cida-org.xml; bmz-org.xml
# ausaid-org.xml is empty
"""filename = 'data/acdi_cida-org.xml'
doc = etree.parse(filename)"""

def fixVal(value):
    try:
        return float(value)
    except ValueError:
        pass
    try:
        value = value.replace(',','')
        return float(value)
    except ValueError:
        pass
    return float(value.replace('.0',''))    

def date_later_than_now(date):
    try:
        if datetime.datetime.strptime(date, "%Y-%m-%d") > datetime.datetime.utcnow():
            return True
    except Exception:
        # Some dates are not real dates...
        pass
    return False

def budget_within_year_scope(budget_end, year):

    # Check that the budget ends at least N years ahead, but not
    # N+1 years ahead (because then it counts as the following year,
    # so out of scope).

    # Budgets are now within scope if they run until the end of
    # 2014 (maximum 177 days).

    try:
        now = datetime.datetime.now()
        date_budget_end = datetime.datetime.strptime(budget_end, "%Y-%m-%d")

        future = datetime.timedelta(days=177+(365*(year-1)))
        future_plus_oneyear = future+datetime.timedelta(days=365)

        if ((date_budget_end > (now+future)) and 
            (date_budget_end < (now+future_plus_oneyear))):
            return True
    except Exception:
        # Some dates are not real dates...
        pass

    return False

def total_future_budgets(doc):

    # Checks if total budgets are available for each of
    # the next three years.

    total_budgets = doc.xpath("//total-budget[period-end/@iso-date]")
    years = [0, 1, 2, 3]
    out = {}

    def get_budget_per_year(year, out, total_budget):
        budget_start = total_budget.find('period-start').get('iso-date')
        budget_end = total_budget.find('period-end').get('iso-date')
       
        if budget_within_year_scope(budget_end, year):
            out[year] = {
                'available': True,
                'amount': fixVal(total_budget.find('value').text)
            }
        return out

    def get_budgets(total_budgets, year, out):
        out[year] = {'available': False,
                     'amount': 0 }
        out = [get_budget_per_year(year, out, total_budget) for total_budget in total_budgets]
        return out

    [get_budgets(total_budgets, year, out) for year in years]
    
    return out

def total_country_budgets(doc, totalbudgets):
    
    # Checks if country budgets are available for each
    # of the next three years and what % published
    # recipient country budgets are of the total
    # published budget.
    # Will return 0 if no total budget could be found.

    rb_xpath = "//recipient-country-budget[period-end/@iso-date]"
    recipient_country_budgets = doc.xpath(rb_xpath)
    budgetdata = { 
        'summary': {
            'num_countries': 0, 
            'total_amount': {0:0, 1:0, 2:0, 3:0}, 
            'total_pct': {0:0.00, 1:0.00,2:0.00,3:0.00}, 
            'total_pct_all_years': 0.00
        },
        'countries': {}
    }
    years = [0, 1, 2, 3]

    def get_country_data(budget, budgetdata, year):
        country = budget.find('recipient-country').get('code')
        country_budget_end = budget.find('period-end').get('iso-date')
        if budget_within_year_scope(country_budget_end, year):
            if country in budgetdata['countries']:
                budgetdata['countries'][country][year] = budget.find('value').text
            else:
                budgetdata['countries'][country] = {
                    year: budget.find('value').text,
                    'name': budget.find('recipient-country').text
                }
            budgetdata['summary']['total_amount'][year]+=fixVal(budget.find('value').text)
        return budgetdata

    def make_country_budget(year, budgetdata, 
            recipient_country_budgets):
        return [get_country_data(budget, budgetdata, 
            year) for budget in recipient_country_budgets]

    [make_country_budget(year, budgetdata, 
        recipient_country_budgets) for year in years]

    def getCPAAdjustedPercentage(total_countries, total_year):
        cpa = 0.2136
        total_cpa_adjusted = float(total_year)*cpa
        
        percentage = (float(total_countries)/float(total_cpa_adjusted))*100
        if percentage > 100:
            return 100.00
        else:
            return percentage

    def get_a_total_budget_over_zero(totalbudgets):
        years = [0, 1, 2, 3]
        for year in years:
            if totalbudgets[year]['amount'] > 0:
                return totalbudgets[year]['amount']
        return 0.00

    def generate_total_years_data(budgetdata, year):
        total_countries = budgetdata['summary']['total_amount'][year]
        total_all = totalbudgets[year]['amount']
        try:
            budgetdata['summary']['total_pct'][year] = getCPAAdjustedPercentage(total_countries, total_all)
        except ZeroDivisionError:
            # Use current year's budget
            try:
                budgetdata['summary']['total_pct'][year] = getCPAAdjustedPercentage(total_countries, 
                                get_a_total_budget_over_zero(totalbudgets))
            except ZeroDivisionError:
                budgetdata['summary']['total_pct'][year] = 0.00
        budgetdata['summary']['num_countries'] = len(budgetdata['countries'])
        return budgetdata
    
    data = [generate_total_years_data(budgetdata, year) for year in years]

    total_pcts = budgetdata['summary']['total_pct'].items()

    # For scoring, restrict to forward years (year >=1)
    total_pcts = dict(filter(lambda x: x[0]>=1, total_pcts))
    total_pcts = total_pcts.values()

    # Return average of 3 forward years
    budgetdata['summary']['total_pct_all_years'] = (reduce(lambda x, y: float(x) + float(y), total_pcts) / float(len(total_pcts)))
    return budgetdata

def total_country_budgets_single_result(doc):
    return total_country_budgets(doc, total_future_budgets(doc))['summary']['total_pct_all_years']

def country_strategy_papers(doc):
    countries = all_countries(doc)

    # Is there a country strategy paper for each 
    # country? (Based on the list of countries that
    # have an active country budget.)

    if len(countries)==0:
        return 0.00

    total_countries = len(countries)
    strategy_papers = doc.xpath("//document-link[category/@code='B03']")

    countrycodelist = dqcodelists.reformatCodelist("countriesbasic")

    for code, name in countries.items():
        # Some donors have not provided the name of the country; the
        # country code could theoretically be looked up to find the 
        # name of the country
        name = getCountryName(code, name, countrycodelist)
        for strategy_paper in strategy_papers:
            if name is not None:
                title = strategy_paper.find('title').text.upper()
                name = name.upper()
                if re.compile("(.*)"+name+"(.*)").match(title):
                    try:
                        countries.pop(code)
                    except Exception:
                        pass
    print "Remaining countries are", countries
    return 100-(float(len(countries))/float(total_countries))*100

def getCountryName(code, name, countrycodelist):
    if name is not None:
        return name
    else:
        try:
            return countrycodelist[code]
        except Exception:
            return None

def budget_has_value(recipient_country_budget):
    try:
        value = recipient_country_budget.xpath('value')[0].text
        assert int(float(value))>0
    except Exception:
        return False
    return True

def all_countries(doc):

    # Get all countries that have any budget data at all,
    # as long as the country is active (budget end
    # date later than today).

    countries = {}
    recipient_country_budgets = doc.xpath("//recipient-country-budget[period-end/@iso-date]")
    for recipient_country_budget in recipient_country_budgets:
        country_budget_date = recipient_country_budget.find('period-end').get('iso-date')

        # Check if the country is still active: if there is 
        # an end date later than today, then include it
        if (date_later_than_now(country_budget_date) and budget_has_value(recipient_country_budget)):
            code = recipient_country_budget.find('recipient-country').get('code')
            name = recipient_country_budget.find('recipient-country').text
            countries[code] = name
    return countries

def total_budgets_available(doc):
    future_years = total_future_budgets(doc)
    # Only look for future years >=1, i.e. exclude
    # current year.
    future_years = dict(filter(lambda x: x[0]>=1, future_years.items()))

    available = 0
    for year, data in future_years.items():
        if data['available'] == True:
            available+=1
    return (float(available)/3.0)*100

"""print "Total budgets..."
print total_budgets_available(doc)

print "Total country budgets..."    
print total_country_budgets_single_result(doc)

print "Country strategy papers"
print country_strategy_papers(doc)"""

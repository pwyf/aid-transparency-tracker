from lxml import etree
import datetime
import re
# Tested against:
#   asdb-org.xml; minbuza_nl-organisation.xml; dfid-org.xml; 
#   acdi_cida-org.xml; bmz-org.xml
# ausaid-org.xml is empty
filename = 'data/asdb-org.xml'
doc = etree.parse(filename)

def fixVal(value):
    try:
        return int(value)
    except ValueError:
        pass
    try:
        value = value.replace(',','')
        return int(value)
    except ValueError:
        pass
    return int(value.replace('.0',''))    

def budget_within_year_scope(budget_end, year):

    # Check that the budget ends at least N years ahead, but not
    # N+1 years ahead (because then it counts as the following year,
    # so out of scope).

    now = datetime.datetime.now()
    date_budget_end = datetime.datetime.strptime(budget_end, "%Y-%m-%d")

    future = datetime.timedelta(days=365*year)
    future_plus_oneyear = future+datetime.timedelta(days=365)

    if ((date_budget_end > (now+future)) and 
        (date_budget_end < (now+future_plus_oneyear))):
        return True

    return False

def total_future_budgets(doc):

    # Checks if budgets are available for each of
    # the next three years.

    total_budgets = doc.xpath("//total-budget[period-end/@iso-date]")
    years = [1, 2, 3]
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
            'total_amount': {1:0, 2:0, 3:0}, 
            'total_pct': {1:0.00,2:0.00,3:0.00}, 
            'total_pct_all_years': 0.00
        },
        'countries': {}
    }
    years = [1, 2, 3]

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

    def make_country_budget_per_year(years, budgetdata, 
        recipient_country_budgets):
        return [make_country_budget(year, budgetdata, 
        recipient_country_budgets) for year in years]

    make_country_budget_per_year(years, budgetdata, recipient_country_budgets)

    def generate_total_years_data(budgetdata, year):
        total_countries = budgetdata['summary']['total_amount'][year]
        total_all = totalbudgets[year]['amount']
        try:
            budgetdata['summary']['total_pct'][year] = ((float(total_countries)/float(total_all))*100)
        except ZeroDivisionError:
            budgetdata['summary']['total_pct'][year] = 0.00
        budgetdata['summary']['num_countries'] = len(budgetdata['countries'])
        return budgetdata
    
    data = [generate_total_years_data(budgetdata, year) for year in years]

    total_pcts=budgetdata['summary']['total_pct'].values()
    # Return average of 3 years
    budgetdata['summary']['total_pct_all_years'] = (reduce(lambda x, y: float(x) + float(y), total_pcts) / float(len(total_pcts)))
    return budgetdata

def total_country_budgets_single_result(doc):
    return total_country_budgets(doc, total_future_budgets(doc))['summary']['total_pct_all_years']

def country_strategy_papers(doc, countries):

    # Is there a country strategy paper for each 
    # country? (Based on the list of countries that
    # have an active country budget.)

    if len(countries)==0:
        return 0.00

    total_countries = len(countries)
    strategy_papers = doc.xpath("//document-link[category/@code]")

    for code, name in countries.items():
        for strategy_paper in strategy_papers:
            title = strategy_paper.find('title').text
            if re.compile("(.*)"+name+"(.*)").match(title):
                try:
                    countries.pop(code)
                except Exception:
                    pass
    return 100-(float(len(countries))/float(total_countries))*100

def date_later_than_now(date):
    if datetime.datetime.strptime(date, "%Y-%m-%d") > datetime.datetime.utcnow():
        return True
    return False

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
        if (date_later_than_now(country_budget_date)):
            code = recipient_country_budget.find('recipient-country').get('code')
            name = recipient_country_budget.find('recipient-country').text
            countries[code] = name
    return countries

print "Total budgets..."
print total_future_budgets(doc)

print "Total country budgets..."    
print total_country_budgets_single_result(doc)

print "Country strategy papers"
print country_strategy_papers(doc, all_countries(doc))

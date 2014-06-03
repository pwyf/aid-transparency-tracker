
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db, app

import models
import csv
import util
import unicodecsv

def importIndicatorDescriptions():
    indicatorgroup_name = app.config["INDICATOR_GROUP"]
    filename = 'tests/indicators.csv'
    return importIndicatorDescriptionsFromFile(indicatorgroup_name, filename)

def importIndicatorDescriptionsFromFile(indicatorgroup_name, filename):
    with file(filename) as fh:
        return _importIndicatorDescriptions(indicatorgroup_name, 
                                                   fh, True)

def _importIndicatorDescriptions(indicatorgroup_name, fh, local):
    checkIG = indicatorGroups(indicatorgroup_name)
    if checkIG:
        indicatorgroup = checkIG
    else:
        indicatorgroup = addIndicatorGroup({"name": indicatorgroup_name,
                                            "description": ""
                                            })
    rows = unicodecsv.DictReader(fh)

    for row in rows:
        data = {}
        data['name']=row['name']
        data['description']=row['description']
        data['longdescription']=row['longdescription']
        data['indicator_type']=row['indicator_type']
        data['indicator_category_name']=row['indicator_category_name']
        data['indicator_subcategory_name']=row['indicator_subcategory_name']
        data['indicator_order']=row['order']
        data['indicator_ordinal']=row['ordinal'].startswith('1')
        data['indicator_weight']=row['weight']
        data['indicator_noformat']=row['noformat'].startswith('1')
        data['indicatorgroup_id']=indicatorgroup.id

        checkI = indicators(indicatorgroup_name, data['name'])
        if checkI:
            indicator = updateIndicator(indicatorgroup_name, data['name'], data)
        else:
            indicator = addIndicator(data)

def importIndicators():
    filename = 'tests/tests.csv'
    indicatorgroup_id = app.config["INDICATOR_GROUP"]
    with file(filename) as fh:
        return _importIndicators(indicatorgroup_name, fh, True, False)

def importIndicatorsFromFile(indicatorgroup_name, filename, infotype=False):
    with file(filename) as fh:
        return _importIndicators(indicatorgroup_name, fh, True, infotype)

def _importIndicators(indicatorgroup_name, fh, local, infotype):
    checkIG = indicatorGroups(indicatorgroup_name)
    if checkIG:
        indicatorgroup = checkIG
    else:
        indicatorgroup = addIndicatorGroup({"name": indicatorgroup_name,
                                            "description": ""
                                            })
        
    data = unicodecsv.DictReader(fh)

    for row in data:
        if infotype:
            infotype = models.InfoType.query.filter(models.InfoType.name==row['infotype_name']).first()
            if not infotype:
                continue
            
            indicator_name = row['indicator_name']
            if (indicator_name == ""):
                continue
            
            checkI = indicators(indicatorgroup_name, indicator_name)
            if checkI:
                indicator = checkI
            else:
                indicator = addIndicator({
                                "name" : indicator_name,
                                "description" : "",
                                "indicatorgroup_id" : indicatorgroup.id
                            })
            addIndicatorInfoType({
                                "infotype_id" : infotype.id,
                                "indicator_id" : indicator.id
                            })
        else:
            test = models.Test.query.filter(models.Test.name==row['name']).first()

            if not test:
                continue
            
            indicator_name = row['name']
            if (indicator_name == ""):
                continue
            
            checkI = indicators(indicatorgroup_name, indicator_name)
            if checkI:
                indicator = checkI
            else:
                import pprint
                pprint.pprint(row)
                indicator = addIndicator({
                                "name" : indicator_name,
                                "description" : "",
                                "indicatorgroup_id" : indicatorgroup.id,
                                "order": row["order"]
                            })
            addIndicatorTest({
                                "test_id" : test.id,
                                "indicator_id" : indicator.id
                            })
            
    print "Imported successfully"
    return True

def indicatorGroups(indicatorgroup=None):
    if indicatorgroup is None:
        indicatorgroups = models.IndicatorGroup.query.all()
    else:
        indicatorgroups = models.IndicatorGroup.query.filter_by(name=indicatorgroup).first()
    return indicatorgroups

def indicators_subset(indicatorgroup=None, indicator_type=None):
    indicators = db.session.query(models.Indicator
                ).filter(models.IndicatorGroup.name==indicatorgroup
                ).filter(models.Indicator.indicator_type==indicator_type
                ).join(models.IndicatorGroup
                ).order_by(models.Indicator.indicator_type,
                           models.Indicator.indicator_category_name,
                           models.Indicator.indicator_subcategory_name
                ).all()
    return indicators

def indicators(indicatorgroup=None, indicator=None):
    if indicator is None:
        indicators = db.session.query(models.Indicator
                    ).filter(models.IndicatorGroup.name==indicatorgroup
                    ).join(models.IndicatorGroup
                    ).order_by(models.Indicator.indicator_order
                    ).all()
    else:
        indicators = db.session.query(models.Indicator
                    ).filter(models.IndicatorGroup.name==indicatorgroup,
                             models.Indicator.name==indicator
                    ).join(models.IndicatorGroup
                    ).order_by(models.Indicator.indicator_order
                    ).first()
    return indicators

def indicatorsTests(indicatorgroup_name):
    indicators = db.session.query(models.Indicator,
                                  models.Test
                ).filter(models.IndicatorGroup.name==indicatorgroup_name
                ).outerjoin(models.IndicatorTest
                ).outerjoin(models.Test
                ).order_by(models.Indicator.indicator_order
                ).all()
    return indicators

def addIndicatorGroup(data):
    checkIG = models.IndicatorGroup.query.filter_by(name=data["name"]).first()
    if not checkIG:
        with db.session.begin():
            newIG = models.IndicatorGroup()
            newIG.setup(
                name = data["name"],
                description = data["description"]
                )
            db.session.add(newIG)
        return newIG
    else:
        return False

def updateIndicatorGroup(indicatorgroup, data):
    checkIG = models.IndicatorGroup.query.filter_by(name=indicatorgroup).first()
    if (checkIG is not None):
        with db.session.begin():
            checkIG.name = data["name"]
            checkIG.description = data["description"]
            db.session.add(checkIG)
        return checkIG
    else:
        return False


def deleteIndicatorGroup(indicatorgroup):
    checkIG = models.IndicatorGroup.query.filter_by(name=indicatorgroup).first()
    if (checkIG is not None):
        checkI = models.Indicator.query.filter_by(indicatorgroup_id=checkIG.id).all()

        with db.session.begin():
            for I in checkI:
                checkIT = models.IndicatorTest.query.filter_by(
                    indicator_id=I.id).all()
                for IT in checkIT:
                    db.session.delete(IT)
                db.session.delete(I)
            db.session.delete(checkIG)
        return True
    else:
        return False

def addIndicator(data):
    checkI = models.Indicator.query.filter_by(name=data["name"], indicatorgroup_id=data["indicatorgroup_id"]).first()
    if not checkI:
        with db.session.begin():
            newI = models.Indicator()
            newI.setup(
                name = data["name"],
                description = data["description"],
                longdescription = data.get("longdescription"),
                indicatorgroup_id = data.get('indicatorgroup_id'),
                indicator_type = data.get("indicator_type"),
                indicator_category_name = data.get("indicator_category_name"),
                indicator_subcategory_name = data.get("indicator_subcategory_name"),
                indicator_ordinal = data.get("indicator_ordinal", False),
                indicator_noformat = data.get("indicator_noformat", None),
                indicator_order = data.get("indicator_order", None),
                indicator_weight = data.get("indicator_weight", None)
                )
            db.session.add(newI)
        return newI
    else:
        return False

def updateIndicator(indicatorgroup, indicator, data):
    checkI = db.session.query(models.Indicator
                ).filter(models.Indicator.name==indicator, 
                         models.IndicatorGroup.name==indicatorgroup
                ).join(models.IndicatorGroup
                ).first()
    if (checkI is not None):
        with db.session.begin():
            checkI.name = data["name"]
            checkI.description = data["description"]
            checkI.longdescription = data.get("longdescription")
            checkI.indicatorgroup_id = int(data["indicatorgroup_id"])
            checkI.indicator_type = data.get("indicator_type")
            checkI.indicator_category_name = data.get("indicator_category_name")
            checkI.indicator_subcategory_name = data.get("indicator_subcategory_name")
            checkI.indicator_ordinal = data.get("indicator_ordinal", None)
            checkI.indicator_noformat = data.get("indicator_noformat", None)
            checkI.indicator_order = data.get("indicator_order", None)
            checkI.indicator_weight = data.get("indicator_weight", None)
            db.session.add(checkI)
        return checkI
    else:
        return False


def getIndicatorByName(indicator_name):
    return db.session.query(models.Indicator.name==indicator_name).first()


def deleteIndicator(indicatorgroup, indicator):
    checkI = db.session.query(models.Indicator
                ).filter(models.Indicator.name==indicator, 
                         models.IndicatorGroup.name==indicatorgroup
                ).join(models.IndicatorGroup
                ).first()
    if (checkI is not None):
        with db.session.begin():
            checkIT = models.IndicatorTest.query.filter_by(indicator_id=checkI.id).all()
            for IT in checkIT:
                db.session.delete(IT)

            db.session.delete(checkI)
        return True
    else:
        return False

def indicatorTests(indicatorgroup_name, indicator_name):
    indicatorTests = db.session.query(models.Test,
                                      models.IndicatorTest
                ).filter(models.Indicator.name==indicator_name
                ).filter(models.IndicatorGroup.name==indicatorgroup_name
                ).join(models.IndicatorTest
                ).join(models.Indicator
                ).all()
    if indicatorTests:
        return indicatorTests
    else:
        return False

def testIndicator(test_id):
    testIndicator = db.session.query(models.Indicator
                ).filter(models.Test.id==test_id
                ).join(models.IndicatorTest
                ).join(models.Test
                ).first()
    if testIndicator:
        return testIndicator
    else:
        return False

def addIndicatorTest(data):
    checkIT = models.IndicatorTest.query.filter_by(test_id=data["test_id"], indicator_id=data["indicator_id"]).first()
    if not checkIT:
        with db.session.begin():
            newIT = models.IndicatorTest()
            newIT.setup(
                indicator_id = data["indicator_id"],
                test_id = data["test_id"]
                )
            db.session.add(newIT)
        return newIT
    else:
        return False

def addIndicatorInfoType(data):
    checkIIT = models.IndicatorInfoType.query.filter_by(infotype_id=data["infotype_id"], indicator_id=data["indicator_id"]).first()
    if not checkIIT:
        with db.session.begin():
            newIIT = models.IndicatorInfoType()
            newIIT.setup(
                infotype_id = data["infotype_id"],
                indicator_id = data["indicator_id"]
                )
            db.session.add(newIIT)
        return newIIT
    else:
        return False

def deleteIndicatorTest(indicatortest_id):
    checkIT = models.IndicatorTest.query.filter_by(id=indicatortest_id).first()
    if checkIT:
        with db.session.begin():
            db.session.delete(checkIT)
        return checkIT
    else:
        return False

def allTests():
    checkT = models.Test.query.all()
    if checkT:
        return checkT
    else:
        return False

def indicatorGroupTests(indicatorgroup_name=None, option=None):
    if (option != "no"):
        checkIGT = db.session.query(models.Indicator.name,
                                    models.Indicator.description,
                                    models.Test.name,
                                    models.Test.description,
                                    models.Test.test_level
                                ).filter(models.IndicatorGroup.name==indicatorgroup_name
                                ).join(models.IndicatorGroup
                                ).join(models.IndicatorTest
                                ).join(models.Test
                                ).all()
    else:
        checkIGT = db.session.query(models.Test.name,
                                    models.Test.description,
                                    models.Test.test_level
                                ).outerjoin(models.IndicatorTest, models.IndicatorTest.test_id==models.Test.id
                                ).outerjoin(models.Indicator
                                ).outerjoin(models.IndicatorGroup
                                ).filter(models.IndicatorGroup.id==None
                                ).filter(models.Test.id>0
                                ).all()
    if checkIGT:
        return checkIGT
    else:
        return False

def disableUnassociatedTests(indicatorgroup_name):
    utests = db.session.query(models.Test
                                ).outerjoin(models.IndicatorTest, models.IndicatorTest.test_id==models.Test.id
                                ).outerjoin(models.Indicator
                                ).outerjoin(models.IndicatorGroup
                                ).filter(models.IndicatorGroup.id==None
                                ).filter(models.Test.id>0
                                ).all()
    count =0
    with db.session.begin():
        for utest in utests:
            utest.active=False
            db.session.add(utest)
            count +=1
    print "Deactivated", count, "tests"
    return count

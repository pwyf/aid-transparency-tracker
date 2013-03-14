
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

import models
import csv
import util
import unicodecsv

def importIndicators(indicatorgroup_name="pwyf2013", filename='tests/activity_tests.csv', local=True):

    f = util.stream_of_file(filename, local)
    if not f:
        return False

    checkIG = indicatorGroups(indicatorgroup_name)
    if checkIG:
        indicatorgroup = checkIG
    else:
        indicatorgroup = addIndicatorGroup({"name": indicatorgroup_name,
                                            "description": ""
                                            })
        
    data = unicodecsv.DictReader(f)

    for row in data:
        test = models.Test.query.filter(models.Test.name==row['test']).first()

        if not test:
            continue
        
        indicator_name = row['group']
        
        checkI = indicators(indicatorgroup_name, indicator_name)
        if checkI:
            indicator = checkI
        else:
            indicator = addIndicator({
                            "name" : indicator_name,
                            "description" : "",
                            "indicatorgroup_id" : indicatorgroup.id
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

def indicators(indicatorgroup=None, indicator=None):
    if indicator is None:
        indicators = db.session.query(models.Indicator
                    ).filter(models.IndicatorGroup.name==indicatorgroup
                    ).join(models.IndicatorGroup
                    ).all()
    else:
        indicators = db.session.query(models.Indicator
                    ).filter(models.IndicatorGroup.name==indicatorgroup,
                             models.Indicator.name==indicator
                    ).join(models.IndicatorGroup
                    ).first()
    return indicators

def addIndicatorGroup(data):
    checkIG = models.IndicatorGroup.query.filter_by(name=data["name"]).first()
    if not checkIG:
        newIG = models.IndicatorGroup()
        newIG.setup(
            name = data["name"],
            description = data["description"]
        )
        db.session.add(newIG)
        db.session.commit()
        return newIG
    else:
        return False

def updateIndicatorGroup(indicatorgroup, data):
    checkIG = models.IndicatorGroup.query.filter_by(name=indicatorgroup).first()
    if (checkIG is not None):
        checkIG.name = data["name"]
        checkIG.description = data["description"]
        db.session.add(checkIG)
        db.session.commit()
        return checkIG
    else:
        return False


def deleteIndicatorGroup(indicatorgroup):
    checkIG = models.IndicatorGroup.query.filter_by(name=indicatorgroup).first()
    if (checkIG is not None):
        checkI = models.Indicator.query.filter_by(indicatorgroup_id=checkIG.id).all()
        for I in checkI:
            checkIT = models.IndicatorTest.query.filter_by(indicator_id=I.id).all()
            for IT in checkIT:
                db.session.delete(IT)
            db.session.delete(I)
        db.session.delete(checkIG)
        db.session.commit()
        return True
    else:
        return False

def addIndicator(data):
    checkI = models.Indicator.query.filter_by(name=data["name"], indicatorgroup_id=data["indicatorgroup_id"]).first()
    if not checkI:
        newI = models.Indicator()
        newI.setup(
            name = data["name"],
            description = data["description"],
            indicatorgroup_id = data["indicatorgroup_id"]
        )
        db.session.add(newI)
        db.session.commit()
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
        checkI.name = data["name"]
        checkI.description = data["description"]
        checkI.indicatorgroup_id = int(data["indicatorgroup_id"])
        db.session.add(checkI)
        db.session.commit()
        return checkI
    else:
        return False

def deleteIndicator(indicatorgroup, indicator):
    checkI = db.session.query(models.Indicator
                ).filter(models.Indicator.name==indicator, 
                         models.IndicatorGroup.name==indicatorgroup
                ).join(models.IndicatorGroup
                ).first()
    if (checkI is not None):
        checkIT = models.IndicatorTest.query.filter_by(indicator_id=checkI.id).all()
        for IT in checkIT:
            db.session.delete(IT)

        db.session.delete(checkI)
        db.session.commit()
        return True
    else:
        return False

def indicatorTests(indicator_name):
    indicatorTests = db.session.query(models.Test,
                                      models.IndicatorTest
                ).filter(models.Indicator.name==indicator_name
                ).join(models.IndicatorTest
                ).join(models.Indicator
                ).all()
    if indicatorTests:
        return indicatorTests
    else:
        return False

def addIndicatorTest(data):
    checkIT = models.IndicatorTest.query.filter_by(test_id=data["test_id"], indicator_id=data["indicator_id"]).first()
    if not checkIT:
        newIT = models.IndicatorTest()
        newIT.setup(
            indicator_id = data["indicator_id"],
            test_id = data["test_id"]
        )
        db.session.add(newIT)
        db.session.commit()
        return newIT
    else:
        return False

def deleteIndicatorTest(indicatortest_id):
    checkIT = models.IndicatorTest.query.filter_by(id=indicatortest_id).first()
    if checkIT:
        db.session.delete(checkIT)
        db.session.commit()
        return checkIT
    else:
        return False

def allTests():
    checkT = models.Test.query.all()
    if checkT:
        return checkT
    else:
        return False

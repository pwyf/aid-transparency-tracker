
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

def aggregationTypes(aggregationtype_id=None):
    if aggregationtype_id is None:
        checkATs = db.session.query(models.AggregationType,
                                    models.Test
                            ).outerjoin(models.Test
                            ).all()
    else:
        checkATs = models.AggregationType.query.filter_by(id=aggregationtype_id).first()
    return checkATs

def allAggregationTypes():
    return db.session.query(models.AggregationType).all()

def addAggregationType(data):
    checkAT = models.AggregationType.query.filter_by(name=data["name"]).first()
    if not checkAT:
        with db.session.begin():
            newAT = models.AggregationType()
            newAT.setup(
                name = data["name"],
                description = data["description"],
                test_id = data["test_id"],
                test_result = data["test_result"],
                active = 1
                )
            db.session.add(newAT)
        return newAT
    else:
        return False

def updateAggregationType(aggregationtype_id, data):
    checkAT = models.AggregationType.query.filter_by(id=aggregationtype_id).first()
    if (checkAT is not None):
        with db.session.begin():
            checkAT.name = data["name"]
            checkAT.description = data["description"]
            checkAT.test_id = data["test_id"]
            checkAT.test_result = data["test_result"]
            db.session.add(checkAT)
        return checkAT
    else:
        return False

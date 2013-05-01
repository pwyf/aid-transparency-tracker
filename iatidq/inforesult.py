
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db
import datetime
from lxml import etree

import models
import itertools

def inforesult_total_disbursements_commitments(data):
    def values():
        for t in data.xpath("""//transaction[transaction-type[@code="D" or @code="E"]]/value"""):
            yield t.text

    def ints():
        for v in values():
            try:
                yield int(v)
            except:
                pass

    total = sum([ i for i in ints() ])

    return str(total)

def inforesult_total_disbursements_commitments_current(data):
    oneyear_ago = (datetime.datetime.utcnow()-datetime.timedelta(days=365))
    
    def values():
        for t in data.xpath("""//transaction[transaction-type[@code="D" or @code="E"]]"""):
            transaction_date = t.find('transaction-date').get('iso-date')
            transaction_date_date = datetime.datetime.strptime(transaction_date, "%Y-%m-%d")
            if transaction_date_date > oneyear_ago:
                yield t.find('value').text

    def ints():
        for v in values():
            try:
                yield int(v)
            except:
                pass

    total = sum([ i for i in ints() ])

    return str(total)


def info_results(package_id, runtime_id):
    info_results = db.session.query(models.InfoResult, models.InfoType).filter(
        models.InfoResult.package_id == package_id
        ).filter(
        models.InfoResult.runtime_id == runtime_id
        ).all()

    def results():
        for r, it in info_results:
            yield (it.name, r.result_data)

    return dict([i for i in results()])

def add_type(name, description):
    checkIRT = models.InfoType.query.filter(name=name).first()
    if not checkIRT:
        it = models.InfoType()
        it.name = name
        it.description = description
        db.session.add(it)
        db.session.commit()
        return it
    else:
        return checkIRT


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
import unicodecsv

def inforesult_total_disbursements_commitments(data):
    def values():
        # Data will be a list of iati-activities, generated
        # by an xpath expression
        for d in data:
            for t in d.xpath("""transaction[transaction-type[@code="D" or @code="E"]]/value"""):
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
        # Data will be a list of iati-activities, generated
        # by an xpath expression
        for d in data:
            for t in d.xpath("""transaction[transaction-type[@code="D" or @code="E"]]"""):
                try:
                    transaction_date = t.find('transaction-date').get('iso-date')
                    transaction_date_date = datetime.datetime.strptime(transaction_date, "%Y-%m-%d")
                    if transaction_date_date > oneyear_ago:
                        yield t.find('value').text
                except AttributeError:
                    # No transaction date
                    pass

    def ints():
        for v in values():
            try:
                yield int(v)
            except:
                pass

    total = sum([ i for i in ints() ])
    return str(total)

def info_results(package_id, runtime_id, organisation_id):
    info_results = db.session.query(models.InfoResult, models.InfoType).filter(
        models.InfoResult.package_id == package_id
        ).filter(
        models.InfoResult.runtime_id == runtime_id,
        models.InfoResult.organisation_id == organisation_id
        ).all()

    def results():
        for r, it in info_results:
            yield (it.name, r.result_data)

    return dict([i for i in results()])

def add_type(name, description):
    checkIRT = models.InfoType.query.filter(name=name).first()
    if not checkIRT:
        with db.session.begin():
            it = models.InfoType()
            it.name = name
            it.description = description
            db.session.add(it)
        return it
    else:
        return checkIRT

def returnLevel(row, level):
    if (('infotype_level' in row) and (row['infotype_level'] != "")):
        return row['infotype_level']
    else:
        return level

def _importInfoTypesFromFile(fh, filename, level=1, local=True):
    data = unicodecsv.DictReader(fh)

    for row in data:
        infotype = models.InfoType.query.filter(models.InfoType.name==row['infotype_name']).first()

        with db.session.begin():
            if not infotype:
                infotype = models.InfoType()

            infotype.setup(
                name = row['infotype_name'],
                level = returnLevel(row, level),
                description = row['infotype_description']
                )
            db.session.add(infotype)

    print "Imported successfully"
    return True

def importInfoTypesFromFile(filename, level):
    with file(filename) as fh:
        return _importInfoTypesFromFile(fh, filename, level=level, local=True)

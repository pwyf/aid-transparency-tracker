
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from iatidq import db

from lxml import etree

import models
import itertools

def infotest1(data):

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


def infotest2(data):
    return "result2"


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
    it = models.InfoType()
    it.name = name
    it.description = description
    db.session.add(it)
    db.session.commit()

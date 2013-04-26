
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

import models

def infotest1(filename):
    return "result1"


def infotest2(filename):
    return "result2"


def info_results(package_id, runtime_id):
    info_results = models.InfoResult.query.filter(
        models.InfoResult.package_id == package_id
        ).filter(
        models.InfoResult.runtime_id == runtime_id
        ).all()

    def results():
        for r in info_results:
            yield (r.info_id, r.result_data)

    return dict([i for i in results()])

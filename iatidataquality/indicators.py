
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from io import StringIO, BytesIO

from flask import abort, render_template, flash, request, redirect, url_for, send_file
from flask_login import current_user
import csv

from . import app, usermanagement
from iatidq import dqindicators, dqorganisations, models, util


def indicatorgroups():
    return redirect(url_for('get_indicators', indicatorgroup=app.config["INDICATOR_GROUP"]))


def indicators_import():
    if dqindicators.importIndicators():
        flash('Successfully imported your indicators', 'success')
    else:
        flash('Could not import your indicators', 'danger')
    return redirect(url_for('indicatorgroups'))


def indicatorgroups_edit(indicatorgroup=None):
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description']
        }
        indicatorgroup = dqindicators.updateIndicatorGroup(indicatorgroup, data)
        flash('Successfully updated IndicatorGroup', 'success')
    else:
        indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)
    return render_template("indicatorgroups_edit.html",
                           indicatorgroup=indicatorgroup,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user)


def indicatorgroups_delete(indicatorgroup=None):
    indicatorgroup = dqindicators.deleteIndicatorGroup(indicatorgroup)
    flash('Successfully deleted IndicatorGroup', 'success')
    return redirect(url_for('indicatorgroups'))


def indicatorgroups_new():
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description']
        }
        indicatorgroup = dqindicators.addIndicatorGroup(data)
        if indicatorgroup:
            flash('Successfully added IndicatorGroup.', 'success')
        else:
            flash("Couldn't add IndicatorGroup. Maybe one already exists with the same name?", 'danger')
    else:
        indicatorgroup = None
    return render_template("indicatorgroups_edit.html",
                           indicatorgroup=indicatorgroup,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user)


def indicators_comparison(indicatorgroup, indicator):
    indicator = dqindicators.getIndicatorByName(indicator)
    organisations = models.Organisation.sort('organisation_name').all()

    return render_template("indicator_comparison.html",
                           loggedinuser=current_user,
                           indicator=indicator,
                           organisations=organisations)


def get_indicators(indicatorgroup=None):
    indicators = dqindicators.indicatorsTests(indicatorgroup)
    if not indicators:
        return abort(404)

    indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)

    its = {}
    for indicator in indicators:
        ind_id = indicator.Indicator.id
        if ind_id not in its:
            its[ind_id] = {}
        its[ind_id].update(indicator.Indicator.as_dict())
        its[ind_id]["indicator_type"] = its[ind_id]["indicator_type"].title()
        if its[ind_id]["indicator_category_name"]:
            its[ind_id]["indicator_type"] += " - " + its[ind_id]["indicator_category_name"]
        if True:
            if ('test' not in its[ind_id]):
                its[ind_id]['test'] = []
        if indicator.Test:
            test_data = indicator.Test.as_dict()
            test_data['test_id'] = test_data['id']
            del(test_data['id'])
            its[ind_id]['test'].append(test_data)
        its[ind_id]["links"] = {
            "edit": url_for('indicators_edit',
                            indicatorgroup=indicatorgroup.name,
                            indicator=indicator.Indicator.name),
            "delete": url_for('indicators_delete',
                              indicatorgroup=indicatorgroup.name,
                              indicator=indicator.Indicator.name)
            }

    its = util.resort_indicator_tests(its)

    links = {
        "edit_group": url_for('indicatorgroups_edit',
                              indicatorgroup=indicatorgroup.name),
        "delete_group": url_for('indicatorgroups_delete',
                                indicatorgroup=indicatorgroup.name),
        "new_indicator": url_for('indicators_new',
                                 indicatorgroup=indicatorgroup.name),
        "csv_assoc_tests": url_for('indicatorgroup_tests_csv',
                                   indicatorgroup=indicatorgroup.name),
        "csv_unassoc_tests": url_for('indicatorgroup_tests_csv',
                                     indicatorgroup=indicatorgroup.name,
                                     option="no")
        }

    indicator_data = list(its.values())

    json_data = {
        "indicator": indicator_data,
        "indicatorgroup": indicatorgroup.as_dict(),
        "links": links
    }

    return render_template("indicators.html",
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user,
                           **json_data)


def indicatorgroup_tests_csv(indicatorgroup=None, option=None):
    strIO = StringIO()
    if (option != "no"):
        fieldnames = "test_name test_description test_level indicator_name indicator_description".split()
    else:
        fieldnames = "test_name test_description test_level".split()
    out = csv.DictWriter(strIO, fieldnames=fieldnames)
    headers = {}
    for fieldname in fieldnames:
        headers[fieldname] = fieldname
    out.writerow(headers)
    data = dqindicators.indicatorGroupTests(indicatorgroup, option)

    for d in data:
        if (option !="no"):
            out.writerow({"test_name": d[2],
                          "test_description": d[3],
                          "test_level": d[4],
                          "indicator_name": d[0],
                          "indicator_description": d[1], })
        else:
            out.writerow({"test_name": d[0],
                          "test_description": d[1],
                          "test_level": d[2]})
    strIO.seek(0)
    if option ==None:
        option = ""

    # send_file wants bytes in python3 - this converts the StringIO to BytesIO
    bytesIO = BytesIO()
    bytesIO.write(strIO.getvalue().encode('utf-8'))
    bytesIO.seek(0)
    strIO.close()

    return send_file(bytesIO,
                     download_name=indicatorgroup + "_" + option + "tests.csv",
                     as_attachment=True)


def indicators_new(indicatorgroup=None):
    indicatorgroups = dqindicators.indicatorGroups()
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'indicatorgroup_id': request.form['indicatorgroup_id'],
            'longdescription': request.form.get("longdescription"),
            'indicator_type': request.form.get("indicator_type"),
            'indicator_category_name': request.form.get("indicator_category_name"),
            'indicator_subcategory_name': request.form.get("indicator_subcategory_name"),
            'indicator_ordinal': request.form.get("indicator_ordinal", None),
            'indicator_noformat': request.form.get("indicator_noformat", None),
            'indicator_order': request.form.get("indicator_order", None),
            'indicator_weight': request.form.get("indicator_weight", None)
        }
        indicator = dqindicators.addIndicator(data)
        if indicator:
            flash('Successfully added Indicator.', 'success')
        else:
            flash("Couldn't add Indicator. Maybe one already exists with the same name?", 'danger')
    else:
        indicator = None
    return render_template("indicator_edit.html",
                           indicatorgroups=indicatorgroups,
                           indicator=indicator,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user)


def indicators_edit(indicatorgroup=None, indicator=None):
    indicatorgroups = dqindicators.indicatorGroups()
    if (request.method == 'POST'):
        data = {
            'name': request.form['name'],
            'description': request.form['description'],
            'indicatorgroup_id': request.form['indicatorgroup_id'],
            'longdescription': request.form['longdescription'],
            'indicator_type': request.form.get("indicator_type"),
            'indicator_category_name': request.form.get("indicator_category_name"),
            'indicator_subcategory_name': request.form.get("indicator_subcategory_name"),
            'indicator_ordinal': request.form.get("indicator_ordinal", None),
            'indicator_noformat': request.form.get("indicator_noformat", None),
            'indicator_order': request.form.get("indicator_order", None),
            'indicator_weight': request.form.get("indicator_weight", None)
        }
        indicator = dqindicators.updateIndicator(indicatorgroup, indicator, data)
        flash('Successfully updated Indicator', 'success')
    else:
        indicator = dqindicators.indicators(indicatorgroup, indicator)
    return render_template("indicator_edit.html",
                           indicatorgroups=indicatorgroups,
                           indicator=indicator,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user)


def indicators_delete(indicatorgroup=None, indicator=None):
    indicator = dqindicators.deleteIndicator(indicatorgroup, indicator)
    flash('Successfully deleted Indicator', 'success')
    return redirect(url_for('get_indicators', indicatorgroup=indicatorgroup))


def indicatortests(indicatorgroup=None, indicator=None):
    alltests = dqindicators.allTests()
    indicator = dqindicators.indicators(indicatorgroup, indicator)
    indicatorgroup = dqindicators.indicatorGroups(indicatorgroup)
    if (request.method == 'POST'):
        for test in request.form.getlist('test'):
            data = {
                    'indicator_id': indicator.id,
                    'test_id': test
            }
            if dqindicators.addIndicatorTest(data):
                flash('Successfully added test to your indicator.', 'success')
            else:
                flash("Couldn't add test to your indicator.", 'danger')
    indicatortests = dqindicators.indicatorTests(indicatorgroup.name, indicator.name)
    return render_template("indicatortests.html",
                           indicatorgroup=indicatorgroup,
                           indicator=indicator,
                           indicatortests=indicatortests,
                           alltests=alltests,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user)


def indicatortests_delete(indicatorgroup=None, indicator=None, indicatortest=None):
    if dqindicators.deleteIndicatorTest(indicatortest):
        flash('Successfully removed test from indicator ' + indicator + '.', 'success')
    else:
        flash('Could not remove test from indicator ' + indicator + '.', 'danger')
    return redirect(url_for('indicatortests', indicatorgroup=indicatorgroup, indicator=indicator))

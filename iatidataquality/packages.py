
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import abort, render_template, flash, request, redirect, url_for
from flask_login import current_user

from . import usermanagement
from iatidq import dqregistry, dqorganisations, dqpackages
from iatidq.models import Organisation, Package


def integerise(data):
    try:
        return int(data)
    except ValueError:
        return None
    except TypeError:
        return None


def packages_manage():
    if request.method != 'POST':
        pkgs = Package.query.order_by(Package.package_name).all()
        return render_template("packages_manage.html",
                               pkgs=pkgs,
                               admin=usermanagement.check_perms('admin'),
                               loggedinuser=current_user)

    if "refresh" in request.form:
        dqregistry.refresh_packages()
        flash("Refreshed packages from Registry", "success")
    else:
        data = []
        for package in request.form.getlist('package'):
            try:
                request.form["active_"+package]
                active = True
            except Exception:
                active = False
            data.append((package, active))
        dqregistry.activate_packages(data)
        flash("Updated packages", "success")
    return redirect(url_for('packages_manage'))


def packages_edit(package_name=None):
    if request.method == 'GET':
        if package_name is not None:
            package = dqpackages.packages_by_name(package_name)
            # Get only first organisation (this is a hack,
            # but unlikely we will need to add a package
            # to more than one org)
            try:
                package_org_id = dqpackages.packageOrganisations(package.id)[0].Organisation.id
            except IndexError:
                package_org_id = None
            if package.man_auto == 'auto':
                flash("That package is not a manual package, so it can't be edited.", 'danger')
                return redirect(url_for('get_packages'))
        else:
            package = {}
            package_org_id = ""
        organisations = Organisation.sort('organisation_name').all()
        return render_template("package_edit.html",
                               package=package,
                               package_org_id=package_org_id,
                               organisations=organisations,
                               admin=usermanagement.check_perms('admin'),
                               loggedinuser=current_user)
    else:
        if 'active' in request.form:
            active = True
        else:
            active = False

        data = {
            'package_name': request.form.get('package_name'),
            'package_title': request.form.get('package_title'),
            'source_url': request.form.get('source_url'),
            'man_auto': 'man',
            'active': active,
            'hash': request.form.get('hash')
        }
        package_org_id = request.form.get('organisation')
        if package_name is not None:
            pkg = dqpackages.packages_by_name(package_name)
            data['package_id'] = pkg.id
            package = dqpackages.updatePackage(data)
            mode = 'updated'
        else:
            data['package_name'] = 'manual_' + data['package_name']
            package = dqpackages.addPackage(data)
            mode = 'added'
        if package:
            if (package_org_id is not None) and (package_org_id != ""):
                dqorganisations.addOrganisationPackage({
                    'organisation_id': package_org_id,
                    'package_id': package.id,
                    'condition': None
                })
            # TODO: attach package to organisation
            flash("Successfully "+mode+" package.", 'success')
            return redirect(url_for('packages_edit', package_name=package.package_name))
        else:
            flash("There was an error, and the package could not be "+mode+".", "danger")
            organisations = Organisation.sort('organisation_name').all()
            data['package_name'] = request.form.get('package_name')
        return render_template("package_edit.html",
                               package=data,
                               package_org_id=package_org_id,
                               organisations=organisations,
                               admin=usermanagement.check_perms('admin'),
                               loggedinuser=current_user)


def get_packages(package_name=None):
    if package_name is None:
        packages = Package.query.filter_by(active=True).order_by(
            Package.package_name).all()
        return render_template("packages.html",
                               packages=packages,
                               admin=usermanagement.check_perms('admin'),
                               loggedinuser=current_user)

    # Get package data
    package = Package.query.filter_by(
        package_name=package_name
    ).first()
    if not package:
        return abort(404)
    organisations = dqpackages.packageOrganisations(package.id)

    return render_template("package.html", package=package,
                           organisations=organisations,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user)

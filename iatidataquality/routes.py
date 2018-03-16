
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import render_template, send_from_directory
from flask_login import current_user

from . import app, api, aggregationtypes, indicators, \
              organisations_feedback, organisations, \
              packages, publisher_conditions, registry, \
              sampling, surveys, tests, usermanagement, users


@app.route("/")
def home():
    return render_template("dashboard.html",
                           admin=usermanagement.check_perms('admin'),
                           intro_html=app.config.get('INTRO_HTML'),
                           loggedinuser=current_user)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html",
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html", error=e,
                           error_class=e.__class__.__name__,
                           admin=usermanagement.check_perms('admin'),
                           loggedinuser=current_user), 500


@app.route('/about/')
def about():
    return render_template("about.html",
                           loggedinuser=current_user,
                           admin=usermanagement.check_perms('admin'))


@app.route("/login/", methods=["GET", "POST"])
def login():
    return usermanagement.login()


@app.route('/logout/')
def logout():
    return usermanagement.logout()


@app.route("/aggregationtypes/")
@app.route("/aggregationtypes/<aggregationtype_id>/")
@usermanagement.perms_required()
def aggtypes(aggregationtype_id=None):
    return aggregationtypes.aggregationtypes(aggregationtype_id)


@app.route("/aggregationtypes/new/", methods=['POST', 'GET'])
@app.route("/aggregationtypes/<aggregationtype_id>/edit/",
           methods=['POST', 'GET'])
@usermanagement.perms_required()
def aggregationtypes_edit(aggregationtype_id=None):
    return aggregationtypes.aggregationtypes_edit(aggregationtype_id)


@app.route("/api/")
def api_index():
    return api.api_index()


@app.route("/api/tests/")
def api_tests():
    return api.api_tests()


@app.route("/api/tests/<test_id>")
def api_test(test_id):
    return api.api_test(test_id)


@app.route("/api/packages/active/")
def api_packages_active():
    return api.api_packages_active()


@app.route("/api/packages/")
def api_packages():
    return api.api_packages()


@app.route("/api/packages/run/<package_id>/")
def api_package_run(package_id):
    return api.api_package_run(package_id)


@app.route("/api/packages/status/<package_id>/")
def api_package_status(package_id):
    return api.api_package_status(package_id)


@app.route('/api/packages/<package_name>')
def api_package(package_name):
    return api.api_package(package_name)


@app.route('/api/publishers/<publisher_id>')
def api_publisher_data(publisher_id):
    return api.api_publisher_data(publisher_id)


@app.route('/api/packages/<package_name>/hierarchy/<hierarchy_id>/tests/<test_id>/activities')
@app.route('/api/packages/<package_name>/tests/<test_id>/activities')
def api_package_activities(package_name, test_id, hierarchy_id=None):
    return api.api_package_activities(package_name, test_id, hierarchy_id)


@app.route('/api/publishers/<packagegroup_name>/hierarchy/<hierarchy_id>/tests/<test_id>/activities')
@app.route('/api/publishers/<packagegroup_name>/tests/<test_id>/activities')
def api_publisher_activities(packagegroup_name, test_id, hierarchy_id=None):
    return api.api_publisher_activities(packagegroup_name, test_id, hierarchy_id)


@app.route('/api/organisations/<organisation_code>/hierarchy/<hierarchy_id>/tests/<test_id>/activities')
@app.route('/api/organisations/<organisation_code>/tests/<test_id>/activities')
def api_organisation_activities(organisation_code, test_id, hierarchy_id=None):
    return api.api_organisation_activities(organisation_code, test_id, hierarchy_id)


@app.route("/api/sample/process/", methods=['POST'])
@usermanagement.perms_required()
def api_sampling_process():
    return sampling.api_sampling_process()


@app.route("/api/sample/")
@app.route("/api/sample/<uuid>/")
@usermanagement.perms_required()
def api_sampling(uuid=None):
    return sampling.api_sampling(uuid)


@app.route("/samples/")
@usermanagement.perms_required()
def sampling_list():
    return sampling.sampling_list()


@app.route("/samples/summary/")
@usermanagement.perms_required()
def sampling_summary():
    return sampling.sampling_summary()


@app.route("/sample/<uuid>/")
@usermanagement.perms_required()
def sampling_sample(uuid):
    return sampling.sampling(uuid)


@app.route("/organisations/<organisation_code>/feedback/", methods=['POST', 'GET'])
@usermanagement.perms_required('organisation_feedback', 'create')
def organisation_feedback(organisation_code=None):
    return organisations_feedback.organisation_feedback(organisation_code)


@app.route("/registry/refresh/")
@usermanagement.perms_required()
def registry_refresh():
    return registry.registry_refresh()


@app.route("/registry/download/")
@usermanagement.perms_required()
def registry_download():
    return registry.registry_download()


@app.route("/registry/deleted/")
@usermanagement.perms_required()
def registry_deleted():
    return registry.registry_deleted()


@app.route("/users/")
@app.route("/user/<username>/")
@usermanagement.perms_required()
def get_users(username=None):
    return users.get_users(username)


@app.route("/users/<username>/edit/addpermission/", methods=['POST'])
@usermanagement.perms_required()
def users_edit_addpermission(username):
    return users.users_edit_addpermission(username)


@app.route("/users/<username>/edit/deletepermission/", methods=['POST'])
@usermanagement.perms_required()
def users_edit_deletepermission(username):
    return users.users_edit_deletepermission(username)


@app.route("/users/new/", methods=['POST', 'GET'])
@app.route("/users/<username>/edit/", methods=['POST', 'GET'])
@usermanagement.perms_required()
def users_edit(username=None):
    return users.users_edit(username)


@app.route("/users/<username>/delete/")
@usermanagement.perms_required()
def users_delete(username=None):
    return users.users_delete(username)


@app.route("/packages/manage/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def packages_manage():
    return packages.packages_manage()


@app.route("/packages/new/", methods=['POST', 'GET'])
@app.route("/packages/<package_name>/edit/", methods=['POST', 'GET'])
def packages_edit(package_name=None):
    return packages.packages_edit(package_name)


@app.route("/packages/")
@app.route("/packages/<package_name>/")
def get_packages(package_name=None):
    return packages.get_packages(package_name)


@app.route("/indicators/")
def indicatorgroups():
    return indicators.indicatorgroups()


@app.route("/indicators/import/")
@usermanagement.perms_required()
def indicators_import():
    return indicators.indicators_import()


@app.route("/indicators/<indicatorgroup>/edit/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def indicatorgroups_edit(indicatorgroup=None):
    return indicators.indicatorgroups_edit(indicatorgroup)


@app.route("/indicators/<indicatorgroup>/delete/")
@usermanagement.perms_required()
def indicatorgroups_delete(indicatorgroup=None):
    return indicators.indicatorgroups_delete(indicatorgroup)


@app.route("/indicators/new/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def indicatorgroups_new():
    return indicators.indicatorgroups_new()


@app.route("/indicators/<indicatorgroup>/comparison/<indicator>")
def indicators_comparison(indicatorgroup, indicator):
    return indicators.indicators_comparison(indicatorgroup, indicator)


@app.route("/indicators/<indicatorgroup>/")
def get_indicators(indicatorgroup=None):
    return indicators.get_indicators(indicatorgroup)


@app.route("/indicators/<indicatorgroup>_tests.csv")
@app.route("/indicators/<indicatorgroup>_<option>tests.csv")
def indicatorgroup_tests_csv(indicatorgroup=None, option=None):
    return indicators.indicatorgroup_tests_csv(indicatorgroup, option)


@app.route("/indicators/<indicatorgroup>/new/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def indicators_new(indicatorgroup=None):
    return indicators.indicators_new(indicatorgroup)


@app.route("/indicators/<indicatorgroup>/<indicator>/edit/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def indicators_edit(indicatorgroup=None, indicator=None):
    return indicators.indicators_edit(indicatorgroup, indicator)


@app.route("/indicators/<indicatorgroup>/<indicator>/delete/")
@usermanagement.perms_required()
def indicators_delete(indicatorgroup=None, indicator=None):
    return indicators.indicators_delete(indicatorgroup, indicator)


@app.route("/indicators/<indicatorgroup>/<indicator>/", methods=['GET', 'POST'])
def indicatortests(indicatorgroup=None, indicator=None):
    return indicators.indicatortests(indicatorgroup, indicator)


@app.route("/indicators/<indicatorgroup>/<indicator>/<indicatortest>/delete/")
@usermanagement.perms_required()
def indicatortests_delete(indicatorgroup=None, indicator=None, indicatortest=None):
    return indicators.indicatortests_delete(indicatorgroup, indicator, indicatortest)


@app.route("/organisations/coverage/")
@usermanagement.perms_required()
def organisations_coverage():
    return organisations.organisations_coverage()


@app.route("/organisations/<organisation_code>/index/")
@usermanagement.perms_required('organisation', 'view')
def organisations_index(organisation_code=None):
    return organisations.organisations_index(organisation_code)


@app.route("/organisations/")
@app.route("/organisations/<organisation_code>/")
def get_organisations(organisation_code=None):
    return organisations.get_organisations(organisation_code)


@app.route("/organisations/new/", methods=['GET','POST'])
@usermanagement.perms_required()
def organisation_new():
    return organisations.organisation_new()


@app.route("/organisations/<organisation_code>/publication/")
@usermanagement.perms_required('organisation', 'view')
def organisation_publication(organisation_code=None, aggregation_type=2):
    return organisations.organisation_publication(organisation_code, aggregation_type)


@app.route("/organisations/<organisation_code>/publication/detail/")
def organisation_publication_detail(organisation_code=None):
    return organisations.organisation_publication_detail(organisation_code)


@app.route("/organisations/publication_index_history.csv")
@usermanagement.perms_required()
def all_organisations_publication_index_csv_history():
    return organisations.all_organisations_publication_index_csv_history()


@app.route("/organisations/publication_index.csv")
@usermanagement.perms_required()
def all_organisations_publication_index_csv():
    return organisations.all_organisations_publication_index_csv()


@app.route("/organisations/publication.csv")
@usermanagement.perms_required()
def all_organisations_publication_csv():
    return organisations.all_organisations_publication_csv()


@app.route("/organisations/<organisation_code>/publication.csv")
@usermanagement.perms_required('organisation', 'view')
def organisation_publication_csv(organisation_code=None):
    return organisations.organisation_publication_csv(organisation_code)


@app.route("/organisations/<organisation_code>/edit/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def organisation_edit(organisation_code=None):
    return organisations.organisation_edit(organisation_code)


@app.route("/organisations/<organisation_code>/<package_name>/<organisationpackage_id>/delete/")
@usermanagement.perms_required()
def organisationpackage_delete(organisation_code=None, package_name=None,
                               organisationpackage_id=None):
    return organisations.organisationpackage_delete(organisation_code, package_name, organisationpackage_id)


@app.route("/organisation_conditions/clear/")
@usermanagement.perms_required()
def organisationfeedback_clear():
    return publisher_conditions.organisationfeedback_clear()


@app.route("/organisation_conditions/")
@app.route("/organisation_conditions/<id>/")
@usermanagement.perms_required()
def organisation_conditions(id=None):
    return publisher_conditions.organisation_conditions(id)


@app.route("/organisation_conditions/<int:id>/delete/")
@usermanagement.perms_required()
def organisation_condition_delete(id=None):
    return publisher_conditions.organisation_condition_delete(id)


@app.route("/organisation_conditions/import_feedback/", methods=['POST'])
@usermanagement.perms_required()
def import_feedback():
    return publisher_conditions.import_feedback()


@app.route("/organisation_conditions/<id>/edit/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def organisation_conditions_editor(id=None):
    return publisher_conditions.organisation_conditions_editor(id)


@app.route("/organisation_conditions/new/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def organisation_conditions_new(id=None):
    return publisher_conditions.organisation_conditions_new(id)


@app.route("/organisation_conditions/import/step<step>", methods=['GET', 'POST'])
@app.route("/organisation_conditions/import/", methods=['GET', 'POST'])
@usermanagement.perms_required()
def import_organisation_conditions(step=None):
    return publisher_conditions.import_organisation_conditions(step)


@app.route("/organisation_conditions/export/")
def export_organisation_conditions():
    return publisher_conditions.export_organisation_conditions()


@app.route("/surveys/admin/")
@usermanagement.perms_required()
def surveys_admin():
    return surveys.surveys_admin()


@app.route("/surveys/create/", methods=["GET", "POST"])
@app.route("/surveys/<organisation_code>/create/", methods=["GET", "POST"])
def create_survey(organisation_code=None):
    return surveys.create_survey(organisation_code)


@app.route("/organisations/<organisation_code>/survey/repair/")
@usermanagement.perms_required('survey', 'view')
def organisation_survey_repair(organisation_code):
    return surveys.organisation_survey_repair(organisation_code)


@app.route("/organisations/<organisation_code>/survey/")
@usermanagement.perms_required('survey', 'view')
def organisation_survey(organisation_code=None):
    return surveys.organisation_survey(organisation_code)


@app.route("/organisations/<organisation_code>/survey/<workflow_name>/", methods=["GET", "POST"])
def organisation_survey_edit(organisation_code=None, workflow_name=None):
    return surveys.organisation_survey_edit(organisation_code, workflow_name)


@app.route("/tests/")
@app.route("/tests/<id>/")
def get_tests(id=None):
    return tests.get_tests(id)


@app.route("/tests/<id>/edit/", methods=['GET', 'POST'])
@usermanagement.perms_required('tests', 'edit', '<id>')
def tests_editor(id=None):
    return tests.tests_editor(id)


@app.route("/tests/<id>/delete/")
@usermanagement.perms_required('tests', 'delete', '<id>')
def tests_delete(id=None):
    return tests.tests_delete(id)


@app.route("/tests/new/", methods=['GET', 'POST'])
@usermanagement.perms_required('tests', 'new')
def tests_new():
    return tests.tests_new()


@app.route("/tests/import/", methods=['GET', 'POST'])
def import_tests():
    return tests.import_tests()


@app.route("/rawdata/<filename>")
def rawdata(filename):
    return send_from_directory(app.config.get('DATA_STORAGE_DIR'), filename)

from flask import Flask
import json
import models
import database

app = Flask(__name__)
app.config.from_pyfile('config.py')

@app.route("/packages/")
def packages():
    packages = database.db_session.query(models.Package).all()
    package_links = map(lambda package: "/packages/" + package.package_name, packages)
    return json.dumps(package_links)

@app.route('/packages/<package_name>')
def package(package_name):
    package = database.db_session.query(models.Package).filter(models.Package.package_name == package_name).first()
    return json.dumps(package.as_dict())

if __name__ == '__main__':
    app.debug = True
    database.init_db()
    app.run()

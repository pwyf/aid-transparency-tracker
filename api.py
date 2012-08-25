from flask import Flask
import json
app = Flask(__name__)

@app.route('/organisation/<package_id>')
def organisation(package_id):
    organisation = {"package_id": package_id }
    return json.dumps(organisation)

if __name__ == '__main__':
    app.debug = True
    app.run()

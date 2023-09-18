from werkzeug.exceptions import HTTPException
from flask import Flask, jsonify
import logging, subprocess

# Import the required adaptors and blueprints
from submitter.apis.v1.api import v1blueprint
from submitter.apis.v2.controller import v2blueprint
from submitter.adaptors.k8s_adaptor import KubernetesAdaptor
from submitter.adaptors.occopus_adaptor import OccopusAdaptor

app = Flask(__name__)

kubernetes_adaptor = KubernetesAdaptor()
occopus_adaptor = OccopusAdaptor()

app.register_blueprint(v1blueprint)
app.register_blueprint(v2blueprint, url_prefix="/v2.0/")

@app.route('/v2.0/docs/openapi.json')
def host_openapi():
    return app.send_static_file('openapi.json')

@app.route('/v2.0/swagger')
def host_swagger():
    return app.send_static_file('index.html')

@app.errorhandler(HTTPException)
def not_found_errors(error):
    return (
        {"message": str(error)},
        getattr(error, "code", 500),
    )

if __name__ == "__main__":
    app.run(debug=True)

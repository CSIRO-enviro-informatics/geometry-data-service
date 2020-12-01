import logging
import _config as conf
import pyldapi
from flask import Flask
from controller import pages, classes
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.middleware.proxy_fix import ProxyFix


app = Flask(__name__, template_folder=conf.TEMPLATES_DIR, static_folder=conf.STATIC_DIR)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)
CORS(app,  resources={r"/*": {"origins": "*"}})
app.register_blueprint(pages.pages)
app.register_blueprint(classes.classes)
app.config['CORS_HEADERS'] = 'Content-Type'



### swagger specific ###
SWAGGER_URL = '/api/doc'
API_URL = '/static/openapi.json'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Geometry Data Service API"
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
### end swagger specific ###


# run the Flask app
if __name__ == '__main__':
    logging.basicConfig(filename=conf.LOGFILE,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')

    app.run(host="0.0.0.0", port=int("3000"), debug=conf.DEBUG)

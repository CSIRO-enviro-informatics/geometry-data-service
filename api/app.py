import logging
import _config as conf
import pyldapi
from flask import Flask
from controller import pages, classes


app = Flask(__name__, template_folder=conf.TEMPLATES_DIR, static_folder=conf.STATIC_DIR)

app.register_blueprint(pages.pages)
app.register_blueprint(classes.classes)


# run the Flask app
if __name__ == '__main__':
    logging.basicConfig(filename=conf.LOGFILE,
                        level=logging.DEBUG,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s')

    app.run(host="0.0.0.0", port=int("3000"), debug=conf.DEBUG)

'''makes note_app a module'''
import os
from flask import Flask
from flask_cors import CORS
from instance.config import config_classes
from lms_app.db_config.database import DatabaseConnect
from lms_app.v1 import v1_blueprint as v1
    

def create_app(flask_environment=os.environ.get('BASE_ENVIRONMENT')):
    '''This method creates the flask instance and returns it.'''
    app = Flask(__name__)
    base_config_obj = config_classes[flask_environment]
    app.config.from_object(base_config_obj)
    app.config["SWAGGER_UI_JSONEDITOR"] = True
    db_url = base_config_obj.DATABASE_URL
    db_instance = DatabaseConnect(db_url)
    db_instance.create_schemas()
    CORS(app)
    app.register_blueprint(v1)

    return app

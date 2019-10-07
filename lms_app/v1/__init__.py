from flask import Blueprint
from flask_restplus import Api

from lms_app.v1.views.user_views import user_api
from lms_app.v1.views.loan_view import loans_api

v1_blueprint = Blueprint("lms_api_v1", __name__)
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}
api = Api(
    v1_blueprint,
    authorizations=authorizations,
    title='Loan Management System API',
    version='1.0',
    description="loan management system simulations"
)

api.add_namespace(user_api, path="/auth")
api.add_namespace(loans_api, path="/loans")

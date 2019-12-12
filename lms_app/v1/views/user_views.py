import os
from flask import request, make_response, jsonify
from flask_restplus import Resource

from lms_app.v1.validators import user_model_validators
from lms_app.v1.models.user_models import UserModel
from lms_app.v1.serializers import user_serializers
from instance.config import config_classes


user_api = user_serializers.UserDataModel().api
register_input = user_serializers.UserDataModel().this_user
login_input = user_serializers.UserDataModel().login_user

parser = user_api.parser()
parser.add_argument(
    "Authorization", type=str, location="headers",
    help="Access Token", required=True
)


@user_api.route("/register")
class RegisterUser(Resource):

    @user_api.expect(register_input, validate=True)
    def post(self):
        """Register app users"""
        token = request.headers.get('Authorization')
        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        user_model = UserModel(config_obj.DATABASE_URL)

        this_user = user_model.decode_token(token)
        if not this_user:
            pack = {
                "status": 401,
                "message": "UNAUTHORIZED"
            }
            answer = make_response(jsonify(pack), 401)
            answer.content_type = 'application/json;charset=utf-8'
            return answer
        current_user_name = this_user["username"] or ""
        this_user = user_model.verify_current_user(current_user_name)
        user_input = request.get_json() or {}
        schema = user_model_validators.RegisterUserSchema(context=this_user)
        result = schema.load(user_input)

        if not ("errors" in result.keys()):
            person = user_model.register_user(user_input)
            answer = make_response(jsonify(person), 201)
            answer.content_type = 'application/json;charset=utf-8'
            return answer
        pack = {
            "status": 400,
            "message": "Bad Request",
            "data": result.errors
        }
        answer = make_response(jsonify(pack), 400)
        answer.content_type = 'application/json;charset=utf-8'
        return answer


@user_api.route("/login")
class LoginUser(Resource):
    
    @user_api.expect(login_input, validate=True)
    def post(self):
        """Login authenticated users"""
        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        user_model = UserModel(config_obj.DATABASE_URL)

        user_input = request.get_json() or {}
        schema = user_model_validators.LoginSchema()
        result = schema.load(user_input)

        if "errors" in result.keys():
            pack = {
                "status": 400,
                "message": "Bad Request",
                "data": result.errors
            }
            answer = make_response(jsonify(pack), 400)
            answer.content_type = 'application/json;charset=utf-8'
            return answer
        reg_reply = user_model.login(user_input)
        if reg_reply["status"] == 200:
            answer = make_response(jsonify(reg_reply), 200)
            answer.content_type = 'application/json;charset=utf-8'
            return answer
        answer = make_response(jsonify(reg_reply), 401)
        answer.content_type = 'application/json;charset=utf-8'
        return answer


@user_api.route("/profile/<username>")
class GetAProfile(Resource):

    def get(self, username):
        """Get user profile"""
        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        user_model = UserModel(config_obj.DATABASE_URL)
        user_data = user_model.get_a_user(username)
        profile_data = None
        reply = {}
        if not user_data:
            pack = {
                "status": 404,
                "message": "User not found",
                "data": {}
            }
            answer = make_response(jsonify(pack), 404)
            answer.content_type = 'application/json;charset=utf-8'
            return answer
        profile_data = user_model.get_a_profile(user_data["user_id"])
        reply["user_data"] = user_data
        reply["profile_data"] = profile_data
        answer = make_response(jsonify(reply), 200)
        answer.content_type = 'application/json;charset=utf-8'
        return answer


@user_api.route("/officers")
class GetAllOfficers(Resource):

    def get(self):
        """Fetch all officers"""
        token = request.headers.get('Authorization')
        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        user_model = UserModel(config_obj.DATABASE_URL)
        user_data = user_model.get_all_officers()

        token = user_model.decode_token(str(token))
        if not (token and token["role"] == "CREDIT_MANAGER"):
            pack = {
                "status": 401,
                "message": "Unauthorized"
            }
            answer = make_response(jsonify(pack), 401)
            answer.content_type = 'application/json;charset=utf-8'
            return answer
        if not user_data:
            pack = {
                "status": 404,
                "message": "No officer has been found."
            }
            answer = make_response(jsonify(pack), 404)
            answer.content_type = 'application/json;charset=utf-8'
            return answer
        reply = {}
        reply["status"] = 200
        reply["message"] = "SUCCESS"
        reply["data"] = user_data
        answer = make_response(jsonify(reply), 200)
        answer.content_type = 'application/json;charset=utf-8'
        return answer


@user_api.route("/officer/<username>/farmers")
class GetAllFarmers(Resource):
    """Fetch all farmers. Access only to agents own farmers
    and to the credit_manager"""

    def get(self, username):
        """Get an officers farmers"""
        token = request.headers.get('Authorization')
        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        user_model = UserModel(config_obj.DATABASE_URL)

        token = user_model.decode_token(token)
        if not (token):
            pack = {
                "status": 401,
                "message": "Unauthorized"
            }
            answer = make_response(jsonify(pack), 401)
            answer.content_type = 'application/json;charset=utf-8'
            return answer
        token_verify = user_model.verify_current_user(token["username"])
        reply = {}

        if token_verify:
            reply = user_model.get_all_farmers_for_officer(username)
        answer = make_response(jsonify(reply), reply["status"])
        answer.content_type = 'application/json;charset=utf-8'
        return answer

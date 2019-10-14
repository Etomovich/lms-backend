import os
from flask import request, make_response, jsonify
from flask_restplus import Resource

from lms_app.v1.validators import loan_model_validator
from lms_app.v1.models.loan_models import LoanModel
from lms_app.v1.serializers import loans_serializers
from instance.config import config_classes

loans_api = loans_serializers.LoansDataModel().api
ask_loan_input = loans_serializers.LoansDataModel().ask_loan
edit_loan_input = loans_serializers.LoansDataModel().edit_loan
proccess_farmer_loan = (
    loans_serializers.LoansDataModel().process_farmer_loan
)
farmer_pay_input = loans_serializers.LoansDataModel().farmer_payment
edit_pay_input = loans_serializers.LoansDataModel().edit_farmer_payment
verify_loan_payment = (
    loans_serializers.LoansDataModel().verify_loan_payment
)

parser = loans_api.parser()
parser.add_argument(
    "Authorization", type=str, location="headers",
    help="Access Token", required=True
)


@loans_api.route("/farmer/loan")
class CreateLoan(Resource):
    @loans_api.expect(ask_loan_input, validate=True)
    def post(self):
        """Ask for a loan from the company"""
        token = request.headers.get('Authorization')
        
        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)

        # Verify user
        user = loan_model.decode_token(token)
        if not user:
            pack = {
                "status": 401,
                "message": "UNAUTHORIZED"
            }
            answer = make_response(jsonify(pack), 401)
            answer.content_type = 'application/json;charset=utf-8'
            return answer
        user = loan_model.verify_current_user(user["username"])

        # Verify user input
        user_input = request.get_json() or {}
        schema = loan_model_validator.AskLoan()
        result = schema.load(user_input)
        if "errors" in result.keys():
            answer = make_response(
              loan_model.return_data(400, "BAD REQUEST", result.errors), 400
            )
            return answer
        
        # Ask for loan
        ask_reply = loan_model.ask_for_loan(user_input["amount_requested"])
        answer = make_response(
              ask_reply, ask_reply["status"]
            )
        return answer


@loans_api.route("/farmer/loan/<int:loan_id>")
class EditLoan(Resource):
    @loans_api.expect(edit_loan_input, validate=True)
    def put(self, loan_id):
        """Edit loan details before being processed"""
        token = request.headers.get('Authorization')
        
        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)

        # Verify user input
        user_input = request.get_json() or {}
        schema = loan_model_validator.AskLoan()
        result = schema.load(user_input)
        if "errors" in result.keys():
            answer = make_response(
              loan_model.return_data(400, "BAD REQUEST", result.errors), 400
            )
            return answer

        # Edit loan
        user = loan_model.decode_token(token)
        if user and "username" in user.keys():
            loan_model.verify_current_user(user["username"])
            response_data = loan_model.update_loan_amount(
                loan_id, user_input["amount_requested"]
            )
            return make_response(
              response_data, response_data["status"]
            )
        pack = {
                "status": 401,
                "message": "UNAUTHORIZED"
            }
        answer = make_response(jsonify(pack), 401)
        answer.content_type = 'application/json;charset=utf-8'
        return answer

    @loans_api.expect(proccess_farmer_loan, validate=True)
    def patch(self, loan_id):
        """Process farmer loan by the Loan Officer."""
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)

        # Verify user input
        user_input = request.get_json() or {}
        schema = loan_model_validator.ProcessLoan()
        result = schema.load(user_input)
        if "errors" in result.keys():
            answer = make_response(
              loan_model.return_data(400, "BAD REQUEST", result.errors), 400
            )
            return answer

        # Process loan
        user = loan_model.decode_token(token)
        if user and "username" in user.keys():
            loan_model.verify_current_user(user["username"])
            response_data = loan_model.process_loan(
                loan_id, user_input
            )
            return make_response(
              response_data, response_data["status"]
            )
        pack = {
            "status": 401,
            "message": "UNAUTHORIZED"
        }
        answer = make_response(jsonify(pack), 401)
        answer.content_type = 'application/json;charset=utf-8'
        return answer

    def delete(self, loan_id):
        """Delete the loan requested that has not yet been processed."""
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)
        if token and "username" in token:
            loan_model.verify_current_user(token["username"])
        response_data = loan_model.delete_a_loan(loan_id)
        return make_response(
            response_data, response_data["status"]
        )


@loans_api.route("/farmer/loan-payment/<int:loan_id>")
class PayLoan(Resource):
    @loans_api.expect(farmer_pay_input, validate=True)
    def post(self, loan_id):
        """Pay for a loan you owe the company."""
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)

        # Verify user input
        user_input = request.get_json() or {}
        schema = loan_model_validator.MakePayment()
        result = schema.load(user_input)
        if "errors" in result.keys():
            answer = make_response(
              loan_model.return_data(400, "BAD REQUEST", result.errors), 400
            )
            return answer

        # Pay loan
        user = loan_model.decode_token(token)
        if user and "username" in user.keys():
            loan_model.verify_current_user(user["username"])
            response_data = loan_model.make_loan_payment(
                loan_id, user_input["amount_paid"],
                user_input["payment_info"], user_input["pay_date"]
            )
            return make_response(
              response_data, response_data["status"]
            )
        pack = {
                "status": 401,
                "message": "UNAUTHORIZED"
            }
        answer = make_response(jsonify(pack), 401)
        answer.content_type = 'application/json;charset=utf-8'
        return answer


@loans_api.route("/farmer/payment/<int:payment_id>")
class FarmerEditPayment(Resource):
    @loans_api.expect(edit_pay_input, validate=True)
    def put(self, payment_id):
        """Farmer edit his/her pay before being verified by the company"""
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)

        # Verify user input
        user_input = request.get_json() or {}
        schema = loan_model_validator.EditPayment()
        result = schema.load(user_input)
        if "errors" in result.keys():
            answer = make_response(
              loan_model.return_data(400, "BAD REQUEST", result.errors), 400
            )
            return answer

        # Edit payment
        user = loan_model.decode_token(token)
        if user and "username" in user.keys():
            loan_model.verify_current_user(user["username"])
            response_data = loan_model.edit_loan_payment(
                payment_id, user_input,
            )
            return make_response(
              response_data, response_data["status"]
            )
        pack = {
                "status": 401,
                "message": "UNAUTHORIZED"
            }
        answer = make_response(jsonify(pack), 401)
        answer.content_type = 'application/json;charset=utf-8'
        return answer

    @loans_api.expect(verify_loan_payment, validate=True)
    def patch(self, payment_id):
        """Verify loan payment by the agent"""
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)

        # Verify user input
        user_input = request.get_json() or {}
        schema = loan_model_validator.VerifyPayment()
        result = schema.load(user_input)
        if "errors" in result.keys():
            answer = make_response(
              loan_model.return_data(400, "BAD REQUEST", result.errors), 400
            )
            return answer

        # Verify payment
        user = loan_model.decode_token(token)
        if user and "username" in user.keys():
            loan_model.verify_current_user(user["username"])
            response_data = loan_model.verify_farmer_payment(
                payment_id, user_input["approved"]
            )
            return make_response(
              response_data, response_data["status"]
            )
        pack = {
            "status": 401,
            "message": "UNAUTHORIZED"
        }
        answer = make_response(jsonify(pack), 401)
        answer.content_type = 'application/json;charset=utf-8'
        return answer

    def delete(self, payment_id):
        """Delete the payment described."""
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)
        if token and "username" in token:
            loan_model.verify_current_user(token["username"])
        response_data = loan_model.delete_payment(payment_id)
        return make_response(
            response_data, response_data["status"]
        )


@loans_api.route("/farmer/<int:farmer_id>/loan-records")
class GetFarmerLoanRecords(Resource):
    def get(self, farmer_id):
        """Get a farmers loan records."""
        user = None
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)
        if token:
            user = loan_model.decode_token(token)
        if "username" in user:
            loan_model.verify_current_user(user["username"])
        response_data = loan_model.get_a_farmers_loan_records(farmer_id)
        return make_response(
            response_data, response_data["status"]
        )


@loans_api.route("/loan/<int:loan_id>/payment-records")
class GetPaymentRecords(Resource):
    def get(self, loan_id):
        """Get payment record for a given loan ID."""
        """Get loan given the loan ID"""
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)
        token = loan_model.decode_token(token)
        if token and "username" in token:
            loan_model.verify_current_user(token["username"])
        response_data = loan_model.get_payment_records(loan_id)
        return make_response(
            response_data, response_data["status"]
        )


@loans_api.route("/loan/<int:loan_id>/get")
class GetLoan(Resource):
    def get(self, loan_id):
        """Get loan given the loan ID"""
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)
        token = loan_model.decode_token(token)
        if token and "username" in token:
            loan_model.verify_current_user(token["username"])
        response_data = loan_model.get_loan_given_load_id(loan_id)
        return make_response(
            response_data, response_data["status"]
        )


@loans_api.route("/payment/<int:payment_id>/get")
class GetPayment(Resource):
    def get(self, payment_id):
        """Get payment given the payment ID"""
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)
        token = loan_model.decode_token(token)
        if token and "username" in token:
            loan_model.verify_current_user(token["username"])
        response_data = loan_model.get_payment_given_pay_id(payment_id)
        return make_response(
            response_data, response_data["status"]
        )


@loans_api.route("/fetch-all/admin-window")
class GetAllDatabaseLoans(Resource):
    def get(self):
        """Get all loans saved in the database."""
        user = None
        token = request.headers.get('Authorization')

        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        config_obj = config_classes[flask_environment]
        loan_model = LoanModel(config_obj.DATABASE_URL)
        if token:
            user = loan_model.decode_token(token)
        if "username" in user:
            loan_model.verify_current_user(user["username"])
        response_data = loan_model.get_db_loans()
        return make_response(
            response_data, response_data["status"]
        )
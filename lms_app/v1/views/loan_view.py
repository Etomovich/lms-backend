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
        user_model = LoanModel(config_obj.DATABASE_URL)


@loans_api.route("/farmer/loan/<int:loan_id>")
class EditLoan(Resource):
    @loans_api.expect(edit_loan_input, validate=True)
    def put(self, loan_id):
        """Edit loan details before being processed"""

    @loans_api.expect(proccess_farmer_loan, validate=True)
    def patch(self, loan_id):
        """Process farmer loan by the Loan Officer."""

    def delete(self, loan_id):
        """Delete the loan requested that has not yet been processed."""


@loans_api.route("/farmer/payment")
class PayLoan(Resource):
    @loans_api.expect(farmer_pay_input, validate=True)
    def post(self):
        """Pay for a loan you owe the company."""


@loans_api.route("/farmer/payment/<int:payment_id>")
class FarmerEditLoan(Resource):
    @loans_api.expect(farmer_pay_input, validate=True)
    def put(self, payment_id):
        """Farmer edit his/her pay before being verified by the company"""

    @loans_api.expect(verify_loan_payment, validate=True)
    def patch(self, payment_id):
        """Verify loan payment by the agent"""

    def delete(self, payment_id):
        """Delete the payment described."""


@loans_api.route("/farmer/<int:farmer_id>/loan-records")
class GetFarmerLoanRecords(Resource):
    def get(self, farmer_id):
        """Get a farmers loan records."""


@loans_api.route("/loan/<int:loan_id>/payment-records")
class GetPaymentRecords(Resource):
    def get(self, loan_id):
        """Get payment record for a given loan."""


@loans_api.route("/loan/<int:loan_id>/get")
class GetLoan(Resource):
    def get(self, loan_id):
        """Get loan given the loan ID"""


@loans_api.route("/payment/<int:payment_id>/get")
class GetPayment(Resource):
    def get(self, payment_id):
        """Get payment given the payment ID"""

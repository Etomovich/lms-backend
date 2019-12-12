import os
from marshmallow import (
    Schema, fields, ValidationError, validates_schema
)
from instance.config import config_classes
from lms_app.v1.models.user_models import UserModel


class RegisterUserSchema(Schema):
    '''This schema validates user registration data '''
    username = fields.String(required=True)
    first_name = fields.String(required=True)
    last_name = fields.String(required=True)
    national_id = fields.Integer(required=True)
    role = fields.String(required=True)
    date_joined = fields.String(required=True)
    email = fields.Email(required=True)
    phone_number = fields.String(required=True)
    password = fields.String(required=True)
    retype_password = fields.String(required=True)
    officer_username = fields.String()
    location = fields.String()
    officer_info = fields.String()
    farmer_info = fields.String()

    @validates_schema
    def validate_registration_data(self, data, **kwargs):
        flask_environment = os.environ.get("BASE_ENVIRONMENT")
        db_url = config_classes[flask_environment].DATABASE_URL
        user_model = UserModel(db_url)
        user_model.verify_current_user(self.context["username"])

        # Check if <password> and <retype_password> are equal.
        if data['password'] != data['retype_password']:
            raise ValidationError(
                "[password] and [retype_password] should be equal."
            )
        if len(data['password'].strip()) == 0:
            raise ValidationError(
                "[password] cannot be null"
            )

        # Check if current user role is farmer hence cannot register user.
        if (self.context["role"] == "FARMER"):
            msg = (
                ("A farmer cannot register another farmer. Please ") +
                ("reach out to your agent and notify him/her of this.")
            )
            raise ValidationError(msg)

        # Check an officer cannot register manager or a loan officer.
        if (
            (self.context["role"] == "LOAN_OFFICER") and
            (
                (data['role'] == "LOAN_OFFICER") or
                (data['role'] == "CREDIT_MANAGER")
            )
        ):
            msg = (
                ("A loan officer cannot hire a credit manager ") +
                ("or another loan officer. You can only register farmers ") +
                ("you manage. Please reach out to your manager for more ") +
                ("information about this.")
            )
            raise ValidationError(msg)

        # Check if is farmer registration by manager. Check
        # officer_username present
        if(
            (self.context["role"] == "CREDIT_MANAGER") and
            (data['role'] == "FARMER") and
            (not ('officer_username' in data))
        ):
            msg = (
                ("Please add an [officer_username] who will be handling ") +
                ("the affairs of this farmer")
            )
            raise ValidationError(msg)

        # Role can either be [FARMER, LOAN_OFFICER, CREDIT_MANAGER]
        roles = ["FARMER", "LOAN_OFFICER", "CREDIT_MANAGER"]
        if not (data["role"] in roles):
            msg = (
                ("Please note that [role] can either be one of the following ")
                + ("values [FARMER, LOAN_OFFICER, CREDIT_MANAGER]")
            )
            raise ValidationError(msg)

        # Check if username, email, phone_no, national_id is unique
        # username
        if user_model.get_a_user(data["username"]):
            msg = ("This [username] is already in use")
            raise ValidationError(msg)

        # email
        if user_model.check_duplicate("email", data["email"]):
            msg = ("This [email] is already in use")
            raise ValidationError(msg)
        # phone_no
        if user_model.check_duplicate("phone_number", data["phone_number"]):
            msg = ("This [phone_number] is already in use")
            raise ValidationError(msg)
        # national_id
        if user_model.check_duplicate("national_id", data["national_id"]):
            msg = ("This [national_id] is already in use")
            raise ValidationError(msg)
    

class LoginSchema(Schema):
    '''This schema validates login information data '''
    username = fields.String(required=False)
    email = fields.Email(required=False)
    password = fields.String(required=True)

    @validates_schema
    def validate_login_data(self, data, **kwargs):
        # Check that username or email is provided
        if(
            (not ("username" in data.keys())) and
            (not ("email" in data.keys()))
        ):
            msg = ("Please add a [username] or [email] to login")
            raise ValidationError(msg)

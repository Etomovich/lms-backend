import os
from marshmallow import (
    Schema, fields, ValidationError, validates_schema
)
from instance.config import config_classes
from lms_app.v1.models.loan_models import LoanModel

class AskLoan(Schema):
    '''This schema validates login information data '''
    amount_requested = fields.Integer(required=True)

    @validates_schema
    def validate_login_data(self, data, **kwargs):
        # Check that username or email is provided
        if(
            (not ("username" in data.keys())) and
            (not ("email" in data.keys()))
        ):
            msg = ("Please add a [username] or [email] to login")
            raise ValidationError(msg)
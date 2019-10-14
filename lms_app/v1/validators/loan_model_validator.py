from marshmallow import (
    Schema, fields, validates, ValidationError
)


class AskLoan(Schema):
    '''This schema validates ask loan information data '''
    amount_requested = fields.String(required=True)


class ProcessLoan(Schema):
    '''This schema validates process loan information data '''
    amount_given = fields.String(required=False)
    date_loaned = fields.String(required=False)
    pay_date = fields.String(required=False)
    loan_info = fields.String(required=False)
    interest_rate = fields.String(required=False)
    loan_status = fields.String(required=False)

    @validates("loan_status")
    def validate_loan_status(self, loan_status):
        accepted = ["REJECTED", "PENDING", "APPROVED", "CLOSED"]
        if loan_status not in accepted:
            raise ValidationError(
                ("The [loan_status] variable can either be: ") +
                ("[REJECTED, PENDING, APPROVED, CLOSED]")
            )


class MakePayment(Schema):
    '''This schema validates make payment information data '''
    amount_paid = fields.String(required=True)
    payment_info = fields.String(required=True)
    pay_date = fields.String(required=True)


class EditPayment(Schema):
    '''This schema validates edit payment information data '''
    amount_paid = fields.Integer(required=False)
    payment_info = fields.DateTime(required=False)
    pay_date = fields.DateTime(required=False)


class VerifyPayment(Schema):
    '''This schema validates verify payment info data '''
    approved = fields.String(required=True)

    @validates("approved")
    def validate_approved(self, approved):
        accepted = ["NO", "PENDING", "YES"]
        if approved not in accepted:
            raise ValidationError(
                ("The approved variable can either be: ") +
                ("[NO, PENDING, YES]")
            )

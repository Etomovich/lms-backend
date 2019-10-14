from flask_restplus import Namespace, fields


class LoansDataModel(object):
    """Represents the loans data transfer object."""
    api = Namespace(
        'loans', description='management of loans and officers.'
    )
    ask_loan = api.model('Ask loan input data', {
        'amount_requested': fields.String(
            required=True,
            description="The amount of money a farmer wants to loan"
        )
    })
    edit_loan = api.model('Farmer loan edit input before being processed', {
        'amount_requested': fields.Integer(
            required=True,
            description="The amount of money a farmer wants to loan"
        )
    })
    process_farmer_loan = api.model('Process farmer loan', {
        'amount_given': fields.String(
            required=False,
            description="The amount of money given to the farmer"
        ),
        'date_loaned': fields.String(
            required=False,
            description="Date farmer was loaned"
        ),
        'pay_date': fields.String(
            required=False,
            description="Day on which the amount is to be paid."
        ),
        'loan_info': fields.String(
            required=False,
            description="Most recent critical information aout the loan."
        ),
        'interest_rate': fields.String(
            required=False,
            description="Day on which the amount is to be paid."
        ),
        'loan_status': fields.String(
            required=False,
            description="Day on which the amount is to be paid."
        ),
    })
    farmer_payment = api.model('Add farmer payment input', {
        'amount_paid': fields.String(
            required=True,
            description="The amount of money a farmer paid for the loan"
        ),
        'payment_info': fields.String(
            required=True,
            description="Any proof that can verify the payment"
        ),
        'pay_date': fields.String(
            required=True,
            description="Day on which the amount was paid."
        )
    })
    edit_farmer_payment = api.model('Edit farmer pay input', {
        'amount_paid': fields.Integer(
            required=False,
            description="The amount of money a farmer paid for the loan"
        ),
        'payment_info': fields.Integer(
            required=False,
            description="Any proof that can verify the payment"
        ),
        'pay_date': fields.DateTime(
            required=False,
            description="Day on which the amount was paid."
        )
    })
    verify_loan_payment = api.model('Verify Farmer payment', {
        'approved': fields.String(
            required=True,
            description="Approve this payment"
        ),
    })

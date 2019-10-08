from flask_restplus import Namespace, fields


class UserDataModel(object):
    """Represents the user data transfer object."""
    api = Namespace(
        'user', description='user authentication and signup resources'
    )
    this_user = api.model('Register input data', {
        'username': fields.String(
            required=True, description="username"
        ),
        'first_name': fields.String(
            required=True, description="user's first name"
        ),
        'last_name': fields.String(
            required=True, description="user's last name"
        ),
        'national_id': fields.Integer(
            required=True, description="user's national ID"
        ),
        'role': fields.String(
            required=True, description="user's role"
        ),
        'date_joined': fields.Date(
            required=True, description="Date joined"
        ),
        'email': fields.String(
            required=True, description="user's email"
        ),
        'phone_number': fields.String(
            required=True, description="user's last name"
        ),
        'password': fields.String(
            required=True, description="user's password"
        ),
        'retype_password': fields.String(
            required=True, description="Retype password"
        ),
        'officer_username': fields.String(
            required=False, description="Enter officer name"
        ),
        'location': fields.String(
            required=False, description="Enter location"
        ),
        'officer_info': fields.String(
            required=False, description="Add officer information"
        ),
        'farmer_info': fields.String(
            required=False, description="Add farmer information"
        ),
    })
    login_user = api.model('Login input data', {
        'password': fields.String(
            required=True, description="Add your password"
        ),
        'username': fields.String(
            required=False, description="Add your username"
        ),
        'email': fields.String(
            required=False, description="Add you email"
        )
    })

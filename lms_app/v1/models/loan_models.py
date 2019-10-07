from datetime import datetime
from lms_app.v1.models.user_models import UserModel
from instance.config import Config


class LoanModel(UserModel):
    """Creates essential methods that will be used to manage
    loan payment in the system."""
    def __init__(self, db_url):
        super().__init__(db_url)

    def ask_for_loan(self, amount, farmer_data):
        """This method allows farmers to apply for loans."""
        user_query = """
            INSERT INTO loans(
                amount_requested, farmer_id
            )
            VALUES(
                '{}', '{}',
            )
        """.format(
            amount,
            farmer_data["farmer_id"],
        )
        queries = []
        queries.append(user_query)
        create_user_check = self.save_data(queries)
        if isinstance(create_user_check, dict):
            return self.return_data(400, "BAD_REQUEST", create_user_check)
        return self.return_data(201, "CREATED", {})


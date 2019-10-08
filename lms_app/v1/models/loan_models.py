from lms_app.v1.models.user_models import UserModel


class LoanModel(UserModel):
    """Creates essential methods that will be used to manage
    loan payment in the system."""
    def __init__(self, db_url):
        super().__init__(db_url)

    def check_agent_by_role(self, username, role):
        """Check is user is a of the role provided"""
        current_user = self.this_user
        new_user = self.verify_current_user(username)
        self.this_user = current_user
        if new_user and new_user["role"] == role:
            return new_user
        return False

    def is_farmers_agent(self, agent_username, farmers_username):
        """Check if it is the Officer is incharge of the farmer
        and returns their data lest it returns false."""
        # Check if it is a real agent and a real farmer
        agent_check = self.check_agent_by_role(agent_username, "LOAN_OFFICER")
        farmer_check = self.check_agent_by_role(farmers_username, "FARMER")
        if not (agent_check and farmer_check):
            return False

        # Check if the agent is incharge of the farmer
        if farmer_check["officer_incharge"] == agent_check["officer_id"]:
            payload = {}
            payload["farmer_data"] = farmer_check
            payload["officer_data"] = agent_check
            return payload
        return False

    def loan_formatter(self, loan_item):
        """Formats the loan query result to an object"""
        return {
            "loan_id": loan_item[0],
            "amount_requested": loan_item[1],
            "amount_given": loan_item[2],
            "date_loaned": loan_item[3],
            "pay_date": loan_item[4],
            "loan_info": loan_item[5],
            "request_times": loan_item[6],
            "interest_rate": loan_item[7],
            "loan_status": loan_item[8],
            "farmer_id": loan_item[9]
        }

    def pay_formatter(self, pay_item):
        """Formats the payments query result to an object"""
        return {
            "payment_id": pay_item[0],
            "amount_paid": pay_item[1],
            "payment_info": pay_item[2],
            "approved": pay_item[3],
            "pay_date": pay_item[4],
            "loan_id": pay_item[5],
            "farmer_id": pay_item[6]
        }

    def ask_for_loan(self, amount):
        """This method allows farmers to apply for loans."""
        if not self.this_user:
            return self.return_data(401, "Current user not set", {})

        is_farmer = self.check_agent_by_role(
            self.this_user["username"], "FARMER"
        )
        msg = (
            ("Could not ask for loan. NB: only farmers are ") +
            ("eligible to get loans. Please reach out to the management.")
        )
        create_user_check = {}
        create_user_check["error"] = msg
        if is_farmer:
            user_query = """
                INSERT INTO loans(
                    amount_requested, farmer_id
                )
                VALUES(
                    '{}', '{}',
                )
            """.format(
                amount,
                self.this_user["farmer_id"],
            )
            queries = []
            queries.append(user_query)
            create_user_check = self.save_data(queries)
        if isinstance(create_user_check, dict):
            return self.return_data(400, "BAD_REQUEST", create_user_check)
        return self.return_data(201, "CREATED", {})

    def get_loan_query(self, search_field, search_field_data):
        """This method is used to search for a loan given
        the search criteria"""
        loan_query = """
            SELECT * FROM loans WHERE {}='{}'
        """.format(
           search_field, search_field_data
        )
        return loan_query

    def get_a_loan(self, search_field, search_field_data):
        """This method gets one loan given a search parameter"""
        query = self.get_loan_query(search_field, search_field_data)
        loan_item = self.fetch_single_data(query)
        if loan_item:
            return self.loan_formatter(loan_item)
        return False

    def get_all_loans(self, search_field, search_field_data):
        """This method gets all loans given a search parameter"""
        query = self.get_loan_query(search_field, search_field_data)
        loan_items = self.fetch_all_data(query)
        response_item = []
        if loan_items:
            for item in loan_items:
                response_item.append(self.loan_formatter(item))
            return response_item
        return False

    def update_loan_amount(self, loan_id, amount):
        """This method updates the loan amount before"""
        # Verify user. Must be the owner of the loan(farmer)
        if not self.this_user:
            return self.return_data(401, "Current user not set", {})
        loan_data = None
        if "farmer_id" in self.this_user.keys():
            query = """
                SELECT * FROM loans WHERE loan_id='{}' AND farmer_id='{}'
            """.format(
                loan_id, self.this_user["farmer_id"]
            )
            loan_data = self.fetch_single_data(query)

        if not loan_data:
            return self.return_data(401, "UNAUTHORIZED", {})

        loan_data = self.loan_formatter(loan_data)
        # Check if [loan_status] is rejected. If so update [amount_requested]
        # and increment [request_times] by one
        resp = "No loan status checked. Missed all available statuses"
        reply = self.return_data(400, "BAD REQUEST", {"error": resp})
        if loan_data["loan_status"] == "REJECTED":
            q_list = []
            query1 = self.update_query(
              "loans", "amount_requested", amount,
              "loan_id", loan_id
            )
            query2 = self.update_query(
              "loans", "request_times",
              (loan_data["request_times"] + 1),
              "loan_id", loan_id
            )
            q_list.append(query1)
            q_list.append(query2)
            execution_results = self.save_data(q_list)
            if isinstance(execution_results, dict):
                return self.return_data(400, "BAD REQUEST", execution_results)

            reply = self.return_data(
                200,
                "SUCCESS",
                self.get_a_loan("loan_id", loan_data["loan_id"])
            )

        # Check if loan status is pending. If so update [amount_requested]
        if loan_data["loan_status"] == "PENDING":
            q_list = []
            query1 = self.update_query(
              "loans", "amount_requested", amount,
              "loan_id", loan_id
            )
            q_list.append(query2)
            execution_results = self.save_data(q_list)
            if isinstance(execution_results, dict):
                return self.return_data(400, "BAD REQUEST", execution_results)

            reply = self.return_data(
                200,
                "SUCCESS",
                self.get_a_loan("loan_id", loan_data["loan_id"])
            )

        # Check if loan status is approved or closed. Reject request
        if (
            (loan_data["loan_status"] == "APPROVED") or
            (loan_data["loan_status"] == "CLOSED")
        ):
            msg = (
                ("You cannot edit the [amount_requested] after ") +
                ("a loan has been [accepted] or [closed].")
            )
            reply = self.return_data(400, "BAD REQUEST", msg)
        return reply

    def get_loan_owner(self, loan_id):
        """Get the person who owns this loan"""
        this_loan = self.get_a_loan("loan_id", loan_id)
        farmer_data = None
        owner_info = {}
        if this_loan:
            farmer_query = """
                SELECT * FROM farmers WHERE farmer_id='{}'
            """.format(this_loan["farmer_id"])
            farmer_data = self.fetch_single_data(farmer_query)
        if farmer_data:
            farmer_data = self.farmer_formatter(farmer_data)
            owner_info["profile_id"] = farmer_data["profile_id"]
            owner_info["farmer_id"] = this_loan["farmer_id"]
            owner_info["officer_incharge"] = this_loan["officer_incharge"]
        farmer_data = None
        if "profile_id" in owner_info.keys():
            farmer_query = """
                SELECT * FROM profiles WHERE profile_id='{}'
            """.format(owner_info["profile_id"])
            farmer_data = self.fetch_single_data(farmer_query)
        if farmer_data:
            owner_info["user_id"] = farmer_data[6]
        farmer_data = None
        if "user_id" in owner_info.keys():
            farmer_query = """
                SELECT * FROM users WHERE user_id='{}'
            """.format(owner_info["user_id"])
            farmer_data = self.fetch_single_data(farmer_query)
        if farmer_data:
            owner_info["username"] = farmer_data[1]
            owner_info["loan_id"] = loan_id
        return owner_info

    def process_loan(self, loan_id, update_input):
        if not self.this_user:
            return self.return_data(401, "Current user not set", {})

        loan_owner = self.get_loan_owner(loan_id)
        is_incharge = False
        is_manager = False
        if len(loan_owner) > 0:
            is_incharge = self.is_farmers_agent(
                self.this_user["username"], loan_owner["usename"]
            )
        if self.this_user["role"] == "CREDIT_MANAGER":
            is_manager = True
        q_list = []
        if (
            (is_incharge or is_manager) and
            ("amount_given" in update_input.keys())
        ):
            query = self.update_query(
                "loans", "amount_given", update_input["amount_given"],
                "loan_id", loan_id
            )
            q_list.append(query)
        if (
            (is_incharge or is_manager) and
            ("date_loaned" in update_input.keys())
        ):
            query = self.update_query(
                "loans", "date_loaned", update_input["date_loaned"],
                "loan_id", loan_id
            )
            q_list.append(query)
        if (
            (is_incharge or is_manager) and
            ("pay_date" in update_input.keys())
        ):
            query = self.update_query(
                "loans", "pay_date", update_input["pay_date"],
                "loan_id", loan_id
            )
            q_list.append(query)
        if (
            (is_incharge or is_manager) and
            ("loan_info" in update_input.keys())
        ):
            query = self.update_query(
                "loans", "loan_info", update_input["loan_info"],
                "loan_id", loan_id
            )
            q_list.append(query)
        if (
            (is_incharge or is_manager) and
            ("interest_rate" in update_input.keys())
        ):
            query = self.update_query(
                "loans", "interest_rate", update_input["interest_rate"],
                "loan_id", loan_id
            )
            q_list.append(query)
        if (
            (is_incharge or is_manager) and
            "loan_status" in update_input.keys()
        ):
            query = self.update_query(
                "loans", "loan_status", update_input["loan_status"],
                "loan_id", loan_id
            )
            q_list.append(query)

        reply = {
            "error": "No change data given"
        }
        if len(q_list) > 0:
            reply = self.save_data(q_list)
        if not is_manager and len(q_list) > 0:
            reply["error"] = "You have no authority to procces this data."
            return self.return_data(401, "UNAUTHORIZED", reply)
        if isinstance(reply, bool):
            reply = self.get_a_loan("loan_id", loan_id)
            return self.return_data(200, "SUCCESS", reply)
        return self.return_data(400, "BAD REQUEST", reply)

    def is_loan_owner(self, farmer_id, loan_id):
        """Returns true if the loan belongs to the
        farmer in question"""
        owner = self.get_loan_owner(loan_id)
        if ("farmer_id" in owner.keys()) and owner["farmer_id"] == farmer_id:
            return True
        return False

    def delete_a_loan(self, loan_id):
        """Delete this particular loan. A loan can only be deleted if it
        is [pending] or [rejected] by the owner_farmer, [agent_incharge]
        or a manager."""
        if not self.this_user:
            return self.return_data(401, "Current user not set", {})

        is_owner = False
        is_agent = False
        is_manager = False
        correct_status = False
        reply = {}
        if "farmer_id" in self.this_user.keys():
            is_owner = self.is_loan_owner(
                self.this_user["farmer_id"], loan_id
            )
        if "officer_id" in self.this_user.keys():
            owner = self.get_loan_owner(loan_id)
            is_agent = self.is_farmers_agent(
                self.this_user["username"], owner["username"]
            )
        if self.this_user["role"] == "CREDIT_MANAGER":
            is_manager = True
        this_loan = self.get_a_loan("loan_id", loan_id)
        if this_loan and (
            (this_loan["loan_status"] == "PENDING") or
            ((this_loan["loan_status"] == "REJECTED"))
        ):
            correct_status = True

        if correct_status and (is_owner or is_agent or is_manager):
            query = """
                DELETE FROM loans WHERE loan_id='{}'
            """.format(loan_id)
            q_list = []
            q_list.append(query)
            reply = self.save_data(q_list)
        if isinstance(reply, bool):
            return self.return_data(200, "SUCCESS", {})
        if not correct_status:
            msg = (
                ("Note this loan can only be deleted once its status ") +
                ("is either REJECTED or PENDING")
            )
            payload = {"error": msg}
            return self.return_data(400, "BAD REQUEST", payload)
        return self.return_data(401, "UNAUTHORIZED", reply)

    def make_loan_payment(self, loan_id, amount, pay_verification, pay_date):
        """Farmer makes payment he/she owns the company"""
        if not self.this_user:
            return self.return_data(401, "Current user not set", {})
        
        is_owner = False
        check_pay = {
          "error": "You are not the owner of this loan."
        }
        if "farmer_id" in self.this_user.keys():
            is_owner = self.is_loan_owner(
                self.this_user["farmer_id"], loan_id
            )
        if is_owner:
            query = """
                INSERT INTO payments(
                    amount_paid, payment_info, pay_date,
                    loan_id, farmer_id
                )
                VALUES(
                    '{}', '{}', '{}', '{}'
                )
            """.format(
                amount, pay_verification, pay_date,
                loan_id, self.this_user["farmer_id"],
            )
            queries = []
            queries.append(query)
            check_pay = self.save_data(queries)
            if isinstance(check_pay, bool):
                return self.return_data(200, "SUCCESS", {})
            return self.return_data(401, "UNAUTHORIZED", check_pay)

    def get_a_payment(self, payment_id):
        """Get the payment with the given ID"""
        query = """
            SELECT * FROM payments WHERE payment_id='{}'
        """.format(payment_id)
        pay_data = self.fetch_single_data(query)
        if pay_data:
            return self.pay_formatter(pay_data)
        return pay_data

    def get_payments_per_loan(self, loan_id):
        """Get all payments with the associated loan ID"""
        query = """
            SELECT * FROM payments WHERE loan_id='{}'
        """.format(loan_id)
        pay_data = self.fetch_all_data(query)
        reply = []
        if pay_data:
            for item in pay_data:
                reply.append(self.pay_formatter(item))
            return reply
        return pay_data

    def edit_loan_payment(self, payment_id, user_input):
        """Edit the payment by the user if it has not been approved."""
        if not self.this_user:
            return self.return_data(401, "Current user not set", {})

        is_owner = False
        payment_info = None
        q_list = []
        check_pay = {
          "error": "You are not the owner of this payment."
        }
        if "farmer_id" in self.this_user.keys():
            payment_info = self.get_a_payment(payment_id)
        if (
            payment_info and (payment_info["approved"] != "YES") and
            (payment_info["farmer_id"] == self.this_user["farmer_id"])
        ):
            is_owner = True
        if is_owner and "amount_paid" in user_input.keys():
            query = self.update_query(
                "payments", "date_loaned", user_input["amount_paid"],
                "payment_id", payment_id
            )
            q_list.append(query)
        if is_owner and "payment_info" in user_input.keys():
            query = self.update_query(
                "payments", "payment_info", user_input["payment_info"],
                "payment_id", payment_id
            )
            q_list.append(query)
        if is_owner and "pay_date" in user_input.keys():
            query = self.update_query(
                "payments", "pay_date", user_input["pay_date"],
                "payment_id", payment_id
            )
            q_list.append(query)

        if not is_owner:
            return self.return_data(401, "UNAUTHORIZED", check_pay)
        if len(q_list) == 0:
            check_pay["error"] = "There is no data to change from you input"
        else:
            query = self.update_query(
                "payments", "approved", "PENDING",
                "payment_id", payment_id
            )
            q_list.append(query)
            check_pay = self.save_data(q_list)

        if isinstance(check_pay, bool):
            check_pay = self.get_a_payment(payment_id)
            return self.return_data(200, "SUCCESS", check_pay)
        return self.return_data(400, "BAD REQUEST", check_pay)

    def verify_farmer_payment(self, payment_id, pay_status):
        """This method verifies if the is authentic. This can be done
        by the officer incharge or the credit officer."""
        if not self.this_user:
            return self.return_data(401, "Current user not set", {})

        payment_info = self.get_a_payment(payment_id)
        loan_owner = {}
        if payment_info:
            loan_owner = self.get_loan_owner(payment_info["loan_id"])
        is_incharge = False
        is_manager = False
        if len(loan_owner) > 0:
            is_incharge = self.is_farmers_agent(
                self.this_user["username"], loan_owner["usename"]
            )
        if self.this_user["role"] == "CREDIT_MANAGER":
            is_manager = True

        if (is_incharge or is_manager):
            q_list = []
            query = self.update_query(
                "payments", "approved", pay_status,
                "payment_id", payment_id
            )
            q_list.append(query)
            reply = self.save_data(q_list)
            if isinstance(reply, bool):
                reply = self.get_a_payment(payment_id)
                return self.return_data(200, "SUCCESS", reply)
            return self.return_data(400, "BAD REQUEST", reply)
        return self.return_data(401, "UNAUTHRIZED", {})

    def delete_payment(self, payment_id):
        """This method is used to delete the payment of
        a particular loan. It can be accessed with the owner,
        officer in-charge and the manager."""
        if not self.this_user:
            return self.return_data(401, "Current user not set", {})

        is_owner = False
        is_agent = False
        is_manager = False
        correct_status = False
        reply = {}

        loan_owner = None
        payment_info = self.get_a_payment(payment_id)
        if payment_info:
            loan_owner = self.get_loan_owner(payment_info["loan_id"])

        if (
            ("farmer_id" in self.this_user.keys()) and
            loan_owner and (len(loan_owner) > 0)
        ):
            is_owner = self.is_loan_owner(
                self.this_user["farmer_id"], loan_owner["farmer_id"]
            )
        if (
            ("officer_id" in self.this_user.keys()) and
            loan_owner and (len(loan_owner) > 0)
        ):
            is_agent = self.is_farmers_agent(
                self.this_user["username"], loan_owner["username"]
            )
        if self.this_user["role"] == "CREDIT_MANAGER":
            is_manager = True
        if payment_info and (
            (payment_info["approved"] != "YES")
        ):
            correct_status = True

        if correct_status and (is_owner or is_agent or is_manager):
            query = """
                DELETE FROM payments WHERE payment_id='{}'
            """.format(payment_id)
            q_list = []
            q_list.append(query)
            reply = self.save_data(q_list)
        if isinstance(reply, bool):
            return self.return_data(200, "SUCCESS", {})
        if not correct_status:
            msg = (
                ("Note that you cannot delete an approved payment")
            )
            payload = {"error": msg}
            return self.return_data(400, "BAD REQUEST", payload)
        return self.return_data(401, "UNAUTHORIZED", reply)

    def get_a_farmers_loan_records(self, farmer_id):
        """Get all the loan records of the farmer in question"""
        if not self.this_user:
            return self.return_data(401, "Current user not set", {})

        farmer_check = False
        in_charge = False
        is_manager = False
        is_owner = False
        in_charge_query = """
            SELECT * FROM farmers WHERE farmer_id='{}'
        """.format(farmer_id)
        farmer_check = self.fetch_single_data(in_charge_query)
        if farmer_check:
            farmer_check = self.farmer_formatter(farmer_check)

        is_officer = False
        if farmer_check and "officer_id" in self.this_user:
            is_officer = True
        if (
            is_officer and
            (
                (self.this_user["officer_id"]) ==
                (farmer_check["officer_incharge"]))
        ):
            in_charge = True

        is_farmer = False
        if "farmer_id" in self.this_user:
            is_farmer = True
        if is_farmer and self.this_user["farmer_id"] == farmer_id:
            is_owner = True
        if self.this_user["role"] == "CREDIT_MANAGER":
            is_manager = True
        if is_owner or in_charge or is_manager:
            query = """
                SELECT * FROM loans WHERE farmer_id='{}'
            """.format(farmer_id)
            loan_data = self.fetch_all_data(query)
            reply = []
            if loan_data:
                for item in loan_data:
                    reply.append(self.loan_formatter(item))
                return self.return_data(200, "SUCCESS", reply)
            return self.return_data(404, "NOT FOUND", reply)
        return self.return_data(401, "UNAUTHORIZED", {})

    def check_access(self, loan_id):
        """Returns if loan can be accessed with owner,
        in_charge and manager"""
        is_owner = False
        is_agent = False
        is_manager = False

        if not self.this_user:
            return False

        loan_owner = self.get_loan_owner(loan_id)

        if (
            ("farmer_id" in self.this_user.keys()) and
            loan_owner and (len(loan_owner) > 0)
        ):
            is_owner = self.is_loan_owner(
                self.this_user["farmer_id"], loan_owner["farmer_id"]
            )
        if (
            ("officer_id" in self.this_user.keys()) and
            loan_owner and (len(loan_owner) > 0)
        ):
            is_agent = self.is_farmers_agent(
                self.this_user["username"], loan_owner["username"]
            )
        if self.this_user["role"] == "CREDIT_MANAGER":
            is_manager = True
        if is_owner or is_agent or is_manager:
            return True
        return False

    def get_payment_given_pay_id(self, payment_id):
        """Gets a particular payment given the payment ID"""
        # Verify user
        this_pay = self.get_a_payment(payment_id)
        loan_id = None
        valid_user = None
        if this_pay:
            loan_id = this_pay["loan_id"]
        if not this_pay:
            return self.return_data(404, "NOT FOUND", {})
        if loan_id:
            valid_user = self.check_access(payment_id)
        if valid_user:
            return self.return_data(200, "SUCCESS", this_pay)    
        return self.return_data(401, "UNAUTHORIZED", {})

    def get_loan_given_load_id(self, loan_id):
        """Get a loan given the loan ID"""
        # Verify user
        valid_user = self.check_access(loan_id)
        the_loan = False
        if valid_user:
            the_loan = self.get_a_loan("loan_id", loan_id)    
        if not valid_user:
            return self.return_data(401, "UNAUTHORIZED", {})
        if the_loan:  
            return self.return_data(200, "SUCCESS", the_loan)
        return self.return_data(404, "NOT FOUND", {})

    def get_payment_records(self, loan_id):
        """Get a payment records given a loan_id"""
        # Verify user
        valid_user = self.check_access(loan_id)
        the_loan = False
        if valid_user:
            the_loan = self.get_payments_per_loan(loan_id)
        if not valid_user:
            return self.return_data(401, "UNAUTHORIZED", {})
        if the_loan:  
            return self.return_data(200, "SUCCESS", the_loan)
        return self.return_data(404, "NOT FOUND", {})

from datetime import datetime
from lms_app.db_config.database import DatabaseConnect
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer)
from instance.config import Config


class UserModel(DatabaseConnect):
    """Creates essential methods that will be used to access
    user model and manage relationships."""
    def __init__(self, db_url):
        super().__init__(db_url)
        self.this_user = None

    def create_user(self, registration_data):
        """This method is used to create a user. Users can be
        either in 3 categories/roles (FARMER, LOAN_OFFICER, CREDIT_MANAGER)
        """
        user_query = """
            INSERT INTO users(
                username, email, role, password
            )
            VALUES(
                '{}', '{}', '{}', '{}'
            )
        """.format(
            registration_data["username"],
            registration_data["email"],
            registration_data["role"],
            generate_password_hash(
                registration_data["password"],
                salt_length=90
            )
        )
        queries = []
        queries.append(user_query)
        create_user_check = self.save_data(queries)
        if isinstance(create_user_check, dict):
            return self.return_data(400, "BAD_REQUEST", create_user_check)
        return self.return_data(201, "CREATED", {})

    def create_profile(self, username, registration_data):
        """This method creates a user profile."""
        current_person = self.get_a_user(username)
        create_user_check = {}
        if current_person:
            user_query = """
                INSERT INTO profiles(
                    first_name, last_name, phone_number, national_id,
                    date_joined, profile_owner
                )
                VALUES(
                    '{}', '{}', '{}', '{}', '{}', '{}'
                )
            """.format(
                registration_data["first_name"],
                registration_data["last_name"],
                registration_data["phone_number"],
                registration_data["national_id"],
                datetime.strptime(
                    registration_data["date_joined"], "%d/%m/%y %H:%M"
                ),
                current_person["user_id"],
            )
            queries = []
            queries.append(user_query)
            create_user_check = self.save_data(queries)
        payload = {}
        if not isinstance(create_user_check, dict):
            current_profile = self.get_a_profile(current_person["user_id"])
            payload["user_id"] = current_person["user_id"]
            payload["profile_id"] = current_profile["profile_id"]
            return self.return_data(201, "CREATED", payload)
        return self.return_data(400, "BAD_REQUEST", payload)

    def create_officer(self, profile_info, registration_data):
        """This method is used for loan officer registration"""
        officer_query = """
            INSERT INTO loan_officers( profile_id ) VALUES ('{}')
        """.format(
            profile_info["profile_id"]
        )
        queries = []
        queries.append(officer_query)
        create_officer_check = self.save_data(queries)

        payload = {}
        current_officer = False
        if not isinstance(create_officer_check, dict):
            loan_fetch_query = """
                SELECT * FROM loan_officers WHERE profile_id='{}'
            """.format(profile_info["profile_id"])
            current_officer = self.fetch_single_data(loan_fetch_query)
            payload["profile_id"] = profile_info["profile_id"]
            payload["user_id"] = profile_info["user_id"]
            payload["officer_id"] = current_officer[0]

        save_info = {}
        if ((payload) and ("officer_info" in registration_data)):
            update_query = """
                UPDATE loan_officers SET officer_info='{}'
                WHERE officer_id='{}'""".format(
                    registration_data["officer_info"],
                    payload["officer_id"]
                )
            queries = []
            queries.append(update_query)
            save_info = self.save_data(queries)
            if isinstance(save_info, dict):
                return self.return_data(400, "BAD_REQUEST", save_info)
        return self.return_data(201, "CREATED", payload)

    def create_farmer(self, profile_info, registration_data):
        """This method creates a farmer for a particular agent."""
        farmer_created_check = {}
        queries = []
        if self.this_user["role"] == "LOAN_OFFICER":
            farmer_query = """
                INSERT INTO farmers(
                    profile_id, officer_incharge
                ) VALUES ('{}', {})
            """.format(
                profile_info["profile_id"], self.this_user["officer_id"]
            )
            queries.append(farmer_query)

        # Get profile_id of officer in payload
        officer_profile = self.get_a_user(
            registration_data["officer_username"]
        )
        if officer_profile and self.this_user["role"] == "CREDIT_MANAGER":
            officer_profile = self.get_a_profile(officer_profile["user_id"])
            farmer_query = """
                INSERT INTO farmers(
                    profile_id, officer_incharge
                ) VALUES ('{}', {})
            """.format(
                profile_info["profile_id"], officer_profile["profile_id"]
            )
            queries.append(farmer_query)
        farmer_created_check = self.save_data(queries)

        payload = {}
        current_farmer = False
        if not isinstance(farmer_created_check, dict):
            farmer_fetch_query = """
                SELECT * FROM farmers WHERE profile_id='{}'
            """.format(profile_info["profile_id"])
            current_farmer = self.fetch_single_data(farmer_fetch_query)
            payload["profile_id"] = profile_info["profile_id"]
            payload["user_id"] = profile_info["user_id"]
            payload["farmer_id"] = current_farmer[0]

        save_info = {}
        save_location = {}
        error_reply = {}
        if ((payload) and ("farmer_info" in registration_data)):
            update_query = """
                UPDATE farmers SET farmer_info='{}'
                WHERE farmer_id='{}'""".format(
                    registration_data["officer_info"],
                    payload["farmer_id"]
                )
            queries = []
            queries.append(update_query)
            save_info = self.save_data(queries)

        if ((payload) and ("location" in registration_data)):
            update_query = """
                UPDATE farmers SET location='{}'
                WHERE farmer_id='{}'""".format(
                    registration_data["location"],
                    payload["farmer_id"]
                )
            queries = []
            queries.append(update_query)
            save_location = self.save_data(queries)

        if isinstance(save_info, dict):
            error_reply["farmer_info_error"] = save_info
        if isinstance(save_location, dict):
            error_reply["farmer_location_error"] = save_location
        if not error_reply:
            return self.return_data(400, "BAD_REQUEST", error_reply)
        return self.return_data(201, "CREATED", payload)

    def register_user(self, registration_data):
        """This method is used to register any user in the application."""
        reg_data = {}
        payload = {}
        create_user_check = self.create_user(registration_data)
        if create_user_check["status"] != 201:
            return create_user_check

        create_profile_check = self.create_profile(
            registration_data["username"],
            registration_data
        )
        if create_profile_check["status"] != 201:
            return create_profile_check

        payload = create_profile_check
        reg_data["status"] = 201
        if registration_data["role"] == "FARMER":
            reg_data = self.create_farmer(
                create_profile_check["data"],
                registration_data
            )
            payload = reg_data
        if reg_data["status"] != 201:
            return reg_data
        if registration_data["role"] == "LOAN_OFFICER":
            reg_data = self.create_officer(
                create_profile_check["data"],
                registration_data
            )
            payload = reg_data
        if reg_data["status"] != 201:
            return reg_data
        return payload

    def login(self, login_data):
        """This method is used to login a user to the system."""
        user = None
        current_person = None
        username = ""
        if ("email" in login_data.keys()):
            user_fetch_query = """
                SELECT * FROM users WHERE email='{}'
            """.format(login_data["email"])
            current_person = self.fetch_single_data(user_fetch_query)
        if current_person:
            username = current_person[1]
        if ("username" in login_data.keys()):
            username = login_data["username"]
        if (len(username) > 0):
            user = self.verify_current_user(username)
        if user and check_password_hash(
            user["password"], login_data["password"]
        ):
            out_data = {}
            s = Serializer(Config.SECRET_KEY, expires_in=21600)
            token = (s.dumps(user)).decode("ascii")
            out_data["token"] = token
            out_data["user"] = user
            return self.return_data(200, "SUCCESS", out_data)
        error_m = {}
        error_m["error"] = "You have entered wrong login credentials"
        return self.return_data(401, "UNAUTHORIZED", error_m)

    def get_a_user(self, username):
        """"This method is used to get a user with the username given.
        Returns false if the user doesn't exist."""
        user_fetch_query = """SELECT * FROM users WHERE username='{}'
        """.format(username)
        current_person = self.fetch_single_data(user_fetch_query)
        if current_person:
            return {
                "user_id": current_person[0],
                "username": current_person[1],
                "email": current_person[2],
                "role": current_person[3],
                "account_status": current_person[4],
                "password": current_person[5]
            }
        return False
    
    def get_a_profile(self, user_id):
        """"This method is used to get a user's with the user_id given.
        Returns false if the profile doesn't exist."""
        user_fetch_query = """
            SELECT * FROM profiles WHERE profile_owner='{}'
        """.format(user_id)
        current_profile = self.fetch_single_data(user_fetch_query)
        if current_profile:
            return {
                "profile_id": current_profile[0],
                "first_name": current_profile[1],
                "last_name": current_profile[2],
                "phone_number": current_profile[3],
                "national_id": current_profile[4],
                "date_joined": current_profile[5],
                "profile_owner": current_profile[6]
            }
        return False

    def check_duplicate(self, key, value):
        """"This method is used to check duplicate values."""
        user_fetch_query = """
            SELECT * FROM users WHERE '{}'='{};'
        """.format(key, value)
        current_profile = self.fetch_single_data(user_fetch_query)
        if current_profile:
            return True
        return False

    def get_all_officers(self):
        """This method is used to get all agents"""
        user_fetch_query = """
            SELECT * FROM loan_officers;
        """
        current_profiles = self.fetch_all_data(user_fetch_query)
        profile_list = []
        for item in current_profiles:
            officer_object = {}
            officer_object["officer_id"] = item[0]
            officer_object["officer_info"] = item[1]
            officer_object["profile_id"] = item[2]
            profile_list.append(officer_object)
        if len(profile_list) > 0:
            return profile_list
        return False

    def get_all_farmers_for_officer(self, username):
        """This method is used to get all farmers per officer"""
        user = self.verify_current_user(username)
        if not (user):
            return self.return_data(
                400, "Invalid Username", {}
            ) 
        if (
            (user["role"] == "FARMER")
            and (user["role"] == "CREDIT_MANAGER")
        ):
            return self.return_data(
                400, "Please enter a [loan officer] to view farmers", {}
            )
        
        if(
            (self.this_user["role"] == "CREDIT_MANAGER") or
            (
                (self.this_user["role"] == "LOAN_OFFICER") and
                (self.this_user["user_id"] == user["userid"])
            )
        ):
            farmers_fetch_query = """
                SELECT * FROM farmers WHERE officer_incharge='{}'
            """.format(user["officer_id"])

            current_profiles = self.fetch_all_data(farmers_fetch_query)
            profile_list = []
            for item in current_profiles:
                farmer_object = {}
                farmer_object["farmer_id"] = item[0]
                farmer_object["farmer_info"] = item[1]
                farmer_object["location"] = item[2]
                farmer_object["officer_incharge"] = item[3]
                farmer_object["profile_id"] = item[4]
                profile_list.append(farmer_object)
            if len(profile_list) > 0:
                return self.return_data(
                    200, "SUCCESS", profile_list
                )
            else:
                return self.return_data(
                    404, "NOT FOUND", profile_list
                )
        return self.return_data(
            401, "UNAUTHORIZED", {}
        )
        
    def get_a_farmer(self, profile_id):
        """"This method is used to get a farmer with the profile_id given.
        Returns false if the farmer doesn't exist."""
        user_fetch_query = """
            SELECT * FROM farmers WHERE profile_id ='{}'
        """.format(profile_id)
        current_farmer = self.fetch_single_data(user_fetch_query)
        if current_farmer:
            return {
                "farmer_id": current_farmer[0],
                "farmer_info": current_farmer[1],
                "location": current_farmer[2],
                "officer_incharge": current_farmer[3],
                "profile_id": current_farmer[4]
            }
        return False
    
    def get_an_officer(self, profile_id):
        """"This method is used to get a farmer with the profile_id given.
        Returns false if the farmer doesn't exist."""
        user_fetch_query = """
            SELECT * FROM loan_officers WHERE profile_id='{}'
        """.format(profile_id)
        current_officer = self.fetch_single_data(user_fetch_query)
        if current_officer:
            return {
                "officer_id": current_officer[0],
                "officer_info": current_officer[1],
                "profile_id": current_officer[2]
            }
        return False

    def edit_a_user(self, user_id, edit_data):
        """"This method is used to edit a user information. Specific roles
        can edit specific information."""

    def delete_a_user(self, user_id):
        """"This method is used to delete a specific user from the database"""

    def verify_current_user(self, username):
        """Check is the user login credentials are true."""
        profile = False
        officer = False
        farmer = False
        return_data = {}
        user_info = self.get_a_user(username)

        if user_info:
            return_data = user_info
            profile = self.get_a_profile(user_info["user_id"])
        if profile:
            return_data["profile_id"] = profile["profile_id"]

        if (
            ("profile_id" in return_data.keys()) and
            (return_data["role"] == "FARMER")
        ):
            farmer = self.get_a_farmer(return_data["profile_id"])
        if farmer:
            return_data["farmer_id"] = farmer["farmer_id"]

        if (
            ("profile_id" in return_data.keys()) and
            (return_data["role"] == "LOAN_OFFICER")
        ):
            officer = self.get_an_officer(return_data["profile_id"])
        if officer:
            return_data["officer_id"] = officer["officer_id"]
          
        if len(return_data) == 0:
            return False

        self.this_user = return_data
        return return_data

    def decode_token(self, token):
        """This method is used to decode the given token"""
        s = Serializer(Config.SECRET_KEY, expires_in=21600)
        try:
            return s.loads(str(token))
        except Exception:
            return False

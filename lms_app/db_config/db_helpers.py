import os
import psycopg2
from datetime import datetime
from werkzeug.security import generate_password_hash


def create_lms_tables():
    """Creates all the tables in the database."""
    users_table = '''
        CREATE TABLE IF NOT EXISTS users(
            user_id               SERIAL PRIMARY KEY,
            username              VARCHAR(50)  UNIQUE NOT NULL,
            email                 VARCHAR(50)  UNIQUE NOT NULL,
            role                  VARCHAR(20)  NOT NULL,
            account_status        VARCHAR(50)  DEFAULT 'ACTIVE',
            password              VARCHAR(200) NOT NULL
        );
    '''

    profile_table = '''
        CREATE TABLE IF NOT EXISTS profiles(
            profile_id      SERIAL PRIMARY KEY,
            first_name      VARCHAR(50)  NOT NULL,
            last_name       VARCHAR(50)  NOT NULL,
            phone_number    VARCHAR(30)  UNIQUE NOT NULL,
            national_id     VARCHAR(30)  UNIQUE NOT NULL,
            date_joined     TIMESTAMP WITH TIME ZONE NOT NULL,
            profile_owner   INTEGER REFERENCES users(user_id)
                            ON DELETE CASCADE
        );
    '''

    loan_officers_table = '''
        CREATE TABLE IF NOT EXISTS loan_officers(
            officer_id      SERIAL PRIMARY KEY,
            officer_info    VARCHAR(300)  NULL,
            profile_id      INTEGER REFERENCES profiles(profile_id)
                            ON DELETE CASCADE
        );
    '''

    farmers_table = '''
        CREATE TABLE IF NOT EXISTS farmers(
            farmer_id           SERIAL PRIMARY KEY,
            farmer_info         VARCHAR(300)  NULL,
            location            VARCHAR(50)  NULL,
            officer_incharge    INTEGER REFERENCES loan_officers(officer_id)
                                ON DELETE CASCADE,
            profile_id          INTEGER REFERENCES profiles(profile_id)
                                ON DELETE CASCADE
        );
    '''

    loans_table = '''
        CREATE TABLE IF NOT EXISTS loans(
            loan_id             SERIAL PRIMARY KEY,
            amount_requested    NUMERIC(20, 2) NULL DEFAULT 0.0,
            amount_given        NUMERIC(20, 2) NULL DEFAULT 0.0,
            date_loaned         TIMESTAMP WITH TIME ZONE NULL,
            pay_date            TIMESTAMP WITH TIME ZONE NULL,
            loan_info           VARCHAR(300) NULL,
            request_times       INTEGER NULL DEFAULT 0,
            interest_rate       INTEGER NULL DEFAULT 0,
            loan_status         VARCHAR(20) NULL DEFAULT 'PENDING',
            farmer_id           INTEGER REFERENCES farmers(farmer_id)
                                ON DELETE CASCADE
        );
    '''

    payment_table = '''
        CREATE TABLE IF NOT EXISTS payments(
            payment_id          SERIAL PRIMARY KEY,
            amount_paid         NUMERIC(20, 2) NULL DEFAULT 0.0,
            payment_info        VARCHAR(300) NOT NULL,
            approved            VARCHAR(10) DEFAULT 'PENDING',
            pay_date            TIMESTAMP WITH TIME ZONE NOT NULL,
            loan_id             INTEGER REFERENCES loans(loan_id)
                                ON DELETE CASCADE,
            farmer_id           INTEGER REFERENCES farmers(farmer_id)
                                ON DELETE CASCADE
        );
    '''

    return [
        users_table, profile_table, loan_officers_table,
        farmers_table, loans_table, payment_table
    ]


def remove_lms_tables():
    """Remove all existing tables form the database."""
    remove_users_table = '''
        DROP TABLE IF EXISTS users CASCADE
    '''
    remove_profile_table = '''
        DROP TABLE IF EXISTS profiles CASCADE
    '''
    remove_loan_officers_table = '''
        DROP TABLE IF EXISTS loan_officers CASCADE
    '''
    remove_farmers_table = '''
        DROP TABLE IF EXISTS farmers CASCADE
    '''
    remove_loans_table = '''
        DROP TABLE IF EXISTS loans CASCADE
    '''
    remove_payments_table = '''
        DROP TABLE IF EXISTS payments CASCADE
    '''
    return [
        remove_users_table, remove_profile_table,
        remove_loan_officers_table, remove_farmers_table,
        remove_loans_table, remove_payments_table
    ]


def create_default_admin(connection):
    """Create a default user for the database if none exists."""
    query = """
        INSERT INTO users(
            username, email, role, password
        )
        VALUES(
            'lms_admin', 'etolejames@gmail.com', 'CREDIT_MANAGER', '{}'
        );
    """.format(
        generate_password_hash(
            os.environ.get("ADMIN_PASSWORD"),
            salt_length=90
        )
    )

    check_query = """SELECT * from users WHERE username='lms_admin'"""
    try:
        cur = connection.cursor()
        cur.execute(check_query)
        check_admin = cur.fetchone()
        if not check_admin:
            cur.execute(query)
            cur.execute(check_query)
            user_data = cur.fetchone()

            user_query = """
                INSERT INTO profiles(
                    first_name, last_name, phone_number, national_id,
                    date_joined, profile_owner
                )
                VALUES(
                    '{}', '{}', '{}', '{}', '{}', '{}'
                )
            """.format(
                "James", "Etole", "+254717823158", 42934923492,
                datetime.utcnow(), user_data[0],
            )
            cur.execute(user_query)
            connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()


def execute_transactions(conn_obj, query_list):
    """Executes multiple queries in a list"""
    try:
        for query in query_list:
            conn_obj.cursor.execute(query)
        conn_obj.connect.commit()
        return True
    except Exception as error:
        print(error)
        return {
            "error": error
        }

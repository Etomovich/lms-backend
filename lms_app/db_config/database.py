import psycopg2
from lms_app.db_config.db_helpers import create_lms_tables
from lms_app.db_config.db_helpers import remove_lms_tables
from lms_app.db_config.db_helpers import create_default_admin
from lms_app.db_config.db_helpers import execute_transactions


class DatabaseConnect(object):
    """Creates the database connection. Manages all the connections
    to the PosgreSQL database using python extension psycopg2-binary."""
    connect = None
    cursor = None

    def __init__(self, db_url):
        """Creates a DatabaseConnect instance with a db_url argument"""
        try:
            print('Connecting to the PostgreSQL database...')
            DatabaseConnect.connect = psycopg2.connect(db_url)
            DatabaseConnect.cursor = DatabaseConnect.connect.cursor()
        except Exception as error:
            print(error)

    def create_schemas(self):
        """Create database tables and add default admin"""
        lms_tables = create_lms_tables()
        created = execute_transactions(DatabaseConnect, lms_tables)
        if not isinstance(created, dict):
            create_default_admin(DatabaseConnect.connect)
        return created

    def destroy_schemas(self):
        """Delete all database tables."""
        lms_tables = remove_lms_tables()
        return execute_transactions(DatabaseConnect, lms_tables)

    def fetch_single_data(self, query):
        """Fetch single data from the database."""
        try:
            DatabaseConnect.cursor.execute(query)
            response = DatabaseConnect.cursor.fetchone()
            return response
        except Exception as error:
            print(error)
            return False

    def fetch_all_data(self, query):
        """Fetch all rows of the query"""
        try:
            DatabaseConnect.cursor.execute(query)
            response = DatabaseConnect.cursor.fetchall()
            return response
        except Exception as error:
            print(error)
            return False

    def save_data(self, query_list):
        """Save any data passed as a query"""
        return execute_transactions(DatabaseConnect, query_list)

    def return_data(self, status_code, message, data):
        """Response to be used by the views"""
        return {
            "status": status_code,
            "message": message,
            "data": data
        }

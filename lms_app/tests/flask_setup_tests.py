import unittest
from lms_app import create_app
from flask import Flask


class FlaskSetupCase(unittest.TestCase):
    """Implement test to check the database configuration works."""

    def test_create_app_serves_flask_app(self):
        self.assertTrue(isinstance(
            create_app('testing'), Flask),
            msg="create app does not serve a flask instance"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)

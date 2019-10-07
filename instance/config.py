import os


class Config(object):
    '''This class carries the shared configurations across the app.'''
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DEBUG = False


class ProductionConfig(Config):
    '''This class carries configurations to be used in production.'''
    DATABASE_URL = os.environ.get("DATABASE_URL")


class DevelopmentConfig(Config):
    '''This class carries configurations to be used while developing.'''
    DATABASE_URL = os.environ.get("DEV_DB_URL")
    DEBUG = True


class TestingConfig(Config):
    '''This class carries configurations to be used while testing.'''
    DATABASE_URL = os.environ.get("TEST_DB_URL")
    DEBUG = True


config_classes = {
    "production": ProductionConfig,
    "development": DevelopmentConfig,
    "testing": TestingConfig
}

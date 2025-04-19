import os

class Config:
    SONIC_PI_HOST = os.environ.get('SONIC_PI_HOST') or 'localhost'
    SONIC_PI_PORT = int(os.environ.get('SONIC_PI_PORT') or 4557)

class DevelopmentConfig(Config):
    DEBUG = True

class TestConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

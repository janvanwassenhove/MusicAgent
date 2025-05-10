import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class Config:

    PROJECT_ROOT = PROJECT_ROOT

    model_config_file = os.path.join(PROJECT_ROOT, 'App', 'static', 'config', 'model_config.json')
    with open(model_config_file, 'r') as f:
        MODEL_CONFIG = json.load(f)

    settings_file = os.path.join(PROJECT_ROOT, 'App', 'static', 'config', 'settings.json')
    try:
        with open(settings_file) as f:
            SETTINGS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        SETTINGS = {}

    SONIC_PI_HOST = os.environ.get('SONIC_PI_HOST') or SETTINGS.get('sonic_pi_IP', 'localhost')
    SONIC_PI_PORT = int(os.environ.get('SONIC_PI_PORT') or SETTINGS.get('sonic_pi_port', 4557))

    API_KEYS = {
        'openai': os.environ.get('OPENAI_API_KEY') or SETTINGS.get('OPENAI_API_KEY'),
        'anthropic': os.environ.get('ANTHROPIC_API_KEY') or SETTINGS.get('ANTHROPIC_API_KEY'),
        'azure': os.environ.get('AZURE_OPENAI_API_KEY') or SETTINGS.get('AZURE_OPENAI_API_KEY')
    }

    @classmethod
    def get_azure_endpoint(cls):
        return os.environ.get('AZURE_OPENAI_ENDPOINT') or cls.SETTINGS.get('AZURE_OPENAI_ENDPOINT')

    @classmethod
    def get_azure_api_version(cls):
        return os.environ.get('AZURE_OPENAI_API_VERSION') or cls.SETTINGS.get('AZURE_OPENAI_API_VERSION')
    
    @classmethod
    def get_api_key(cls, provider):
        return cls.API_KEYS.get(provider)

    @classmethod
    def update_sonic_pi_settings(cls, new_ip, new_port):
        try:
            settings = {}
            try:
                with open(cls.settings_file) as f:
                    settings = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pass

            settings['sonic_pi_IP'] = new_ip
            settings['sonic_pi_port'] = new_port

            with open(cls.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            # Update class attributes
            cls.SONIC_PI_HOST = new_ip
            cls.SONIC_PI_PORT = int(new_port)
            return True
        except Exception as e:
            raise Exception(f"Failed to update Sonic Pi settings: {str(e)}")

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

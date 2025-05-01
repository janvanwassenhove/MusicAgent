# In App/routes/config_routes.py

from flask import Blueprint, jsonify
from App.config import Config

config_bp = Blueprint('config', __name__)

@config_bp.route('/model_config', methods=['GET'])
def get_model_config():
    """Return the model configuration data."""
    return jsonify(Config.MODEL_CONFIG)

@config_bp.route('/model_config/<provider>', methods=['GET'])
def get_provider_config(provider):
    """Return the model configuration for a specific provider."""
    if provider in Config.MODEL_CONFIG:
        return jsonify(Config.MODEL_CONFIG[provider])
    return jsonify({"error": f"Provider {provider} not found"}), 404

@config_bp.route('/model_config/<provider>/<model>', methods=['GET'])
def get_model_details(provider, model):
    """Return the configuration for a specific model from a provider."""
    if provider in Config.MODEL_CONFIG:
        if model in Config.MODEL_CONFIG[provider]:
            return jsonify(Config.MODEL_CONFIG[provider][model])
        return jsonify({"error": f"Model {model} not found for provider {provider}"}), 404
    return jsonify({"error": f"Provider {provider} not found"}), 404
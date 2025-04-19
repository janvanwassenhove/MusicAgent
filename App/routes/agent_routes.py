from flask import Blueprint, request, jsonify
import os
import json
import logging

agent_bp = Blueprint('agent', __name__)
logger = logging.getLogger()

# Helper functions
def find_agent_config_dir():
    """Find the AgentConfig directory by traversing up the directory tree."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # We've reached the root directory
            raise FileNotFoundError("AgentConfig directory not found in any parent directory")
        agent_config_path = os.path.join(parent_dir, 'AgentConfig')
        if os.path.exists(agent_config_path) and os.path.isdir(agent_config_path):
            return agent_config_path
        current_dir = parent_dir

def get_agent_types():
    """Get the list of available agent types based on the folders in AgentConfig."""
    try:
        agent_config_path = find_agent_config_dir()
        agent_types = [folder for folder in os.listdir(agent_config_path)
                       if os.path.isdir(os.path.join(agent_config_path, folder))]
        return agent_types
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        return []

def load_config(agent_type):
    """Load the configuration for the specified agent type."""
    agent_config_path = find_agent_config_dir()
    config_path = os.path.join(agent_config_path, agent_type, 'ArtistConfig.json')

    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        raise ValueError(f"Configuration file for {agent_type} // {config_path} not found.")
    except Exception as e:
        raise ValueError(f"Error loading configuration for {agent_type}: {str(e)}")

# Routes
@agent_bp.route('/agent_types')
def agent_types():
    try:
        types = get_agent_types()
        return jsonify({"agent_types": types})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

@agent_bp.route('/init', methods=['POST'])
def init_agent():
    agent_type = request.json.get('agent_type')
    try:
        config = load_config(agent_type)
        return jsonify({
            "genres": config['genres']
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@agent_bp.route('/agent_config/<agent_type>', methods=['GET'])
def get_agent_config(agent_type):
    print(f"Getting config for {agent_type}")
    config = load_config(agent_type)
    return jsonify(config)

@agent_bp.route('/agent_config/<agent_type>', methods=['POST'])
def save_agent_config(agent_type):
    new_config = request.json
    save_config(agent_type, new_config)
    return jsonify({"message": "Configuration saved successfully"})

def save_config(agent_type, new_config):
    agent_config_path = find_agent_config_dir()
    config_path = os.path.join(agent_config_path, agent_type, 'ArtistConfig.json')
    with open(config_path, 'w') as config_file:
        json.dump(new_config, config_file, indent=2)

@agent_bp.route('/artists/config', methods=['GET'])
def get_artists_config():
    agent_config_path = find_agent_config_dir()
    sonic_pi_configs = []

    for agent_type in os.listdir(agent_config_path):
        config_path = os.path.join(agent_config_path, agent_type, 'ArtistConfig.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                sonic_pi_configs.append({
                    "agent_type": agent_type,
                    "agent_name": config.get("agent_name"),
                    "artist_style": config.get("artist_style")
                })

    return jsonify(sonic_pi_configs)

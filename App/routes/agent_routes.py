from flask import Blueprint, request, jsonify, current_app, render_template
import os
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from App.services.agent import GPTAgent
from App.services.song import Song

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

def save_config(agent_type, new_config):
    agent_config_path = find_agent_config_dir()
    config_path = os.path.join(agent_config_path, agent_type, 'ArtistConfig.json')
    with open(config_path, 'w') as config_file:
        json.dump(new_config, config_file, indent=2)

# Import agent/song classes and helpers from parent
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(parent_dir)


# Load song config for genres
with open(os.path.join(parent_dir, 'AgentConfig', 'mITyJohn', 'SongConfig.json')) as f:
    song_config = json.load(f)

input_queue = Queue()
def create_input_callback():
    def callback(prompt):
        logger.info(f"Requesting input: {prompt}")
        # In blueprint, you may want to emit via socketio if available
        # For now, just log and wait
        return wait_for_input()
    return callback

def wait_for_input():
    logger.info("Waiting for user input...")
    user_input = input_queue.get()
    logger.info(f"Received user input: {user_input}")
    return user_input

def initialize_agent(song_name, agent_type, input_callback, selected_model, api_provider):
    logger.info(f"Initializing agent {agent_type} for song: {song_name}")
    song = Song(name=song_name, logger=logger)
    agent = GPTAgent(
        selected_model=selected_model,
        logger=logger,
        song=song,
        agentType=agent_type,
        api_provider=api_provider
    )
    logger.info(f"Initialized agent with [PROVIDER]:[{api_provider}] & [MODEL]:[{selected_model}]")
    agent.input_callback = input_callback
    return agent

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

@agent_bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        genre = data.get('genre')
        duration = data.get('duration')
        additional_information = data.get('additional_information')
        song_name = data.get('song_name', 'Untitled')
        agent_type = data.get('agentType', 'mITyJohn')
        selected_model = data['selected_model']
        api_provider = data['api_provider']

        if duration is None:
            return jsonify({"error": "Duration is required"}), 400

        try:
            duration = int(duration)
        except ValueError:
            return jsonify({"error": "Invalid duration value"}), 400

        def run_agent():
            input_callback = create_input_callback()
            logger.info("Starting agent execution")
            agent = initialize_agent(song_name, agent_type, input_callback, selected_model, api_provider)
            agent.input_callback = input_callback
            logger.info("Starting agent execution with callback: " )
            result = agent.execute_composition_chain(genre, duration, additional_information)
            logger.info("Agent execution completed")
            logger.info("DONE")
            # Optionally emit socketio event if available

        run_agent()
        return jsonify({"message": "Agent started"})

    return render_template('index.html')

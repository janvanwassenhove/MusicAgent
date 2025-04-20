from flask import Blueprint, request, jsonify, send_file
import os
import json
import logging
import sys
from App.services.sonicPi import SonicPi
from App.services.song import Song

sonicpi_bp = Blueprint('sonicpi', __name__)
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

def find_agent_config_dir():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            raise FileNotFoundError("AgentConfig directory not found in any parent directory")
        agent_config_path = os.path.join(parent_dir, 'AgentConfig')
        if os.path.exists(agent_config_path) and os.path.isdir(agent_config_path):
            return agent_config_path
        current_dir = parent_dir

def load_config(agent_type):
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

@sonicpi_bp.route('/sonicpi/config', methods=['GET'])
def get_sonicpi_config():
    agent_config_path = find_agent_config_dir()
    sonic_pi_configs = []

    for agent_type in os.listdir(agent_config_path):
        config_path = os.path.join(agent_config_path, agent_type, 'ArtistConfig.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                sonic_pi_configs.append({
                    "agent_type": agent_type,
                    "sonic_pi_IP": config.get("sonic_pi_IP"),
                    "sonic_pi_port": config.get("sonic_pi_port")
                })

    return jsonify(sonic_pi_configs)

@sonicpi_bp.route('/sonicpi/config', methods=['POST'])
def update_sonicpi_config():
    data = request.json
    agent_type = data.get('agent_type')
    new_ip = data.get('sonic_pi_IP')
    new_port = data.get('sonic_pi_port')

    config_path = os.path.join(find_agent_config_dir(), agent_type, 'ArtistConfig.json')
    if not os.path.exists(config_path):
        return jsonify({"error": "Configuration file not found"}), 404

    with open(config_path, 'r') as f:
        config = json.load(f)

    config['sonic_pi_IP'] = new_ip
    config['sonic_pi_port'] = new_port

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    return jsonify({"message": "Configuration updated successfully"})

@sonicpi_bp.route('/send_to_sonicpi', methods=['POST'])
def send_to_sonicpi():
    data = request.json
    if not data or 'code' not in data:
        return jsonify({"error": "No code provided"}), 400

    code = data['code']
    song_name = data.get('song_name', 'Untitled')
    agent_type = data.get('agent_type', 'mITyJohn')
    try:
        artist_config = load_config(agent_type)
        ip_address = artist_config["sonic_pi_IP"]
        port = int(artist_config["sonic_pi_port"])

        # Create a Song instance
        song = Song(name=song_name, logger=logger)

        # Read the script file
        script_file_path = os.path.join(os.path.dirname(parent_dir), 'Songs', song_name, f'{song_name}.rb')
        with open(script_file_path, 'r') as file:
            full_script = file.read()

        # Initialize SonicPi instance
        sonic_pi = SonicPi(logger)

        # Call Sonic Pi with the song, IP address, port, and script content
        sonic_pi.call_sonicpi(song, ip_address, port, full_script)

        return jsonify({"message": "Code sent to Sonic Pi"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Routes
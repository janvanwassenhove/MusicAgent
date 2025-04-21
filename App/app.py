from flask import Flask, render_template, request, jsonify, Response, send_file
import sys
import os
import logging
import queue
from flask_socketio import SocketIO
from concurrent.futures import ThreadPoolExecutor
from flask_cors import CORS

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from App.services.agent import GPTAgent
from App.services.song import Song
import json
from queue import Queue
from routes import register_routes

app = Flask(__name__, static_url_path='/static', static_folder=os.path.join(parent_dir, 'Songs'))
CORS(app)

socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
app.logger.setLevel(logging.DEBUG)  # Set Flask logger to DEBUG level
input_callback = None
input_queue = Queue()

# Global variable to track progress
progress = 0
progress_file = os.path.join(os.path.dirname(__file__), 'progress.json')

def create_input_callback():
    def callback(prompt):
        logger.info(f"Requesting input: {prompt}")
        socketio.emit('input_required', {'prompt': prompt})
        logger.info("Emitted 'input_required' event")
        return wait_for_input()
    return callback

def wait_for_input():
    logger.info("Waiting for user input...")
    user_input = input_queue.get()
    logger.info(f"Received user input: {user_input}")
    return user_input

@socketio.on('submit_input')
def handle_submit_input(data):
    user_input = data['input']
    input_queue.put(user_input)

# Create a queue to store log messages
log_queue = queue.Queue()
class QueueHandler(logging.Handler):
    def emit(self, record):
        log_queue.put(self.format(record))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
queue_handler = QueueHandler()
queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(queue_handler)

register_routes(app)

# Global variable to store the current configuration
current_config = None

# Load configurations
with open(os.path.join(parent_dir, 'AgentConfig', 'mITyJohn', 'SongConfig.json')) as f:
    song_config = json.load(f)

def initialize_agent(song_name, agent_type, input_callback, selected_model, api_provider):
    # Set up logging
    logger.info(f"Initializing agent {agent_type} for song: {song_name}")

    # Create a Song instance
    song = Song(name=song_name, logger=logger)

    # Initialize the agent with default settings
    agent = GPTAgent(
        selected_model=selected_model,  # or whichever model you prefer
        logger=logger,
        song=song,
        agentType=agent_type,  # or whichever agent type you're using
        api_provider=api_provider  # or "anthropic" if you're using that
    )
    logger.info(f"Initialized agent with [PROVIDER]:[{api_provider}] & [MODEL]:[{selected_model}]")
    logger.info(f"Initializing agent input_callback {input_callback} ")
    agent.input_callback = input_callback
    logger.info(f"input_callback set {agent.input_callback} ")
    return agent

def save_config(agent_type, new_config):
    agent_config_path = find_agent_config_dir()
    config_path = os.path.join(agent_config_path, agent_type, 'ArtistConfig.json')
    with open(config_path, 'w') as config_file:
        json.dump(new_config, config_file, indent=2)

@socketio.on('/api/connect')
def handle_connect():
    global input_callback
    input_callback = create_input_callback()
    logger.info(f"Client connected ({request.sid}) and input_callback created ")

@socketio.on('/api/disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@app.route('/api/stream')
def stream():
    def generate():
        while True:
            try:
                message = log_queue.get(timeout=5)  # Wait for 5 seconds
                if message == "DONE":
                    yield "data: DONE\n\n"
                    break
                yield f"data: {message}\n\n"
            except queue.Empty:
                yield "data: Waiting for more data...\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/genres')
def get_genres():
    return jsonify({"genres": song_config['genres']})

@app.route('/api/get_sonicpi_code/<songname>', methods=['GET'])
def get_sonicpi_code(songname):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filepath = os.path.join(project_root, 'Songs', songname, f'{songname}.rb')
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            code = file.read()
        return jsonify({'sonicpi_code': code})
    else:
        return jsonify({'error': 'File not found'}), 404



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

import shutil

def read_progress():
    global progress
    try:
        with open(progress_file, 'r') as f:
            data = json.load(f)
            progress = data.get("progress", 0)
    except Exception as e:
        progress = 0

executor = ThreadPoolExecutor(max_workers=1)

# Remove sample-related endpoints (now in sample_routes.py)

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

@app.route('/api/artists/config', methods=['GET'])
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

if __name__ == '__main__':
    socketio.run(app, debug=True)

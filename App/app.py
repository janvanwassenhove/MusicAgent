from flask import Flask, render_template, request, jsonify, Response
import sys
import os
import logging
import queue
import threading
import traceback
import time
import asyncio
from flask_socketio import SocketIO, emit
from pythonosc import udp_client

from flask_cors import CORS


# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from agent import GPTAgent
from song import Song
import json
from queue import Queue

app = Flask(__name__)

CORS(app)

socketio = SocketIO(app, async_mode='threading',  cors_allowed_origins="*")
app.logger.setLevel(logging.DEBUG)  # Set Flask logger to DEBUG level
input_callback = None
input_queue = Queue()

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

# Global variable to store the current configuration
current_config = None

# Load configurations
with open(os.path.join(parent_dir, 'AgentConfig', 'mITyJohn', 'SongConfig.json')) as f:
    song_config = json.load(f)

def find_agent_config_dir():
    """     Find the AgentConfig directory by traversing up the directory tree.     """
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
    """     Get the list of available agent types based on the folders in AgentConfig.     """
    try:
        agent_config_path = find_agent_config_dir()
        agent_types = [folder for folder in os.listdir(agent_config_path)
                       if os.path.isdir(os.path.join(agent_config_path, folder))]
        return agent_types
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        return []

def load_config(agent_type):
    """
    Load the configuration for the specified agent type.
    """
    agent_config_path = find_agent_config_dir()
    config_path = os.path.join(agent_config_path, agent_type, 'ArtistConfig.json')

    try:
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        raise ValueError(f"Configuration file for {agent_type} // {config_path}  not found.")
    except Exception as e:
        raise ValueError(f"Error loading configuration for {agent_type}: {str(e)}")

def initialize_agent(song_name, agent_type, input_callback, selected_model,api_provider ):
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

@app.route('/api/agent_types')
def agent_types():
    try:
        types = get_agent_types()
        return jsonify({"agent_types": types})
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/init', methods=['POST'])
def init_agent():
    global current_config
    agent_type = request.json.get('agent_type')
    try:
        current_config = load_config(agent_type)
        return jsonify({
            "genres": current_config['genres']
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/create', methods=['GET', 'POST'])
def index():
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
            global input_callback
            input_callback = create_input_callback()

            logger.info("Starting agent execution")
            agent = initialize_agent(song_name, agent_type, input_callback, selected_model, api_provider)
            agent.input_callback = input_callback
            logger.info("Starting agent execution with callback: " )
            result = agent.execute_composition_chain(genre, duration, additional_information)
            logger.info("Agent execution completed")
            logger.info("DONE")
            socketio.emit('process_complete', {'message': 'DONE'})

        run_agent()
        return jsonify({"message": "Agent started"})

    return render_template('index.html')

@app.route('/api/timeline')
def get_timeline():
    agent_type = request.args.get('agent_type', 'mITyJohn')  # Default to mITyJohn if not specified
    config_path = f'AgentConfig/{agent_type}/MusicCreationChainConfig.json'
    with open(config_path, 'r') as f:
        config = json.load(f)
    return jsonify(config)

@app.route('/api/agent_config/<agent_type>', methods=['GET'])
def get_agent_config(agent_type):
    print(f"Getting config for {agent_type}")
    config = load_config(agent_type)
    return jsonify(config)

@app.route('/api/agent_config/<agent_type>', methods=['POST'])
def save_agent_config(agent_type):
    new_config = request.json
    save_config(agent_type, new_config)
    return jsonify({"message": "Configuration saved successfully"})

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
    filepath = os.path.join('songs', songname, f'{songname}.rb')
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            code = file.read()
        return jsonify({'sonicpi_code': code})
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/send_to_sonicpi', methods=['POST'])
def send_to_sonicpi():
    data = request.json
    if not data or 'code' not in data:
        return jsonify({"error": "No code provided"}), 400

    code = data['code']
    song_name = data.get('song_name', 'Untitled')
    agent_type = data.get('agent_type', 'mITyJohn')
    try:
        artist_config = load_config(agent_type)
        client = udp_client.SimpleUDPClient(artist_config["sonic_pi_IP"], int(artist_config["sonic_pi_port"]))

        script_file_path = f"{os.path.dirname(current_dir)}\\songs\\{song_name}\\{song_name}.rb"
        with open(script_file_path, 'r') as file:
            full_script = file.read()

        client.send_message('/run-code', full_script)
        return jsonify({"message": "Code sent to Sonic Pi"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True)

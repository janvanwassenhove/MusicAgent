from flask import Flask, render_template, request, jsonify, Response, send_file
import sys
import os
import logging
import queue
from flask_socketio import SocketIO
from SampleMedataListing import process_directory
from concurrent.futures import ThreadPoolExecutor
from flask_cors import CORS

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from App.agent import GPTAgent
from App.song import Song
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

register_routes(app)

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

@app.route('/api/run_sample_metadata_listing', methods=['POST'])
def run_sample_metadata_listing_endpoint():
    #print("Starting sample metadata listing")
    #threading.Thread(target=run_sample_metadata_listing).start()
    logging.info("run_sample_metadata_listing API called")
    try:
        input_directory = os.path.join(os.path.dirname(__file__), "..", "Samples")
        executor.submit(process_directory, input_directory)
        return jsonify({"status": "accepted"}), 202
    except Exception as e:
        logging.error(f"Error running sample metadata listing: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/sample_metadata_progress', methods=['GET'])
def sample_metadata_progress():
    try:
        with open(progress_file, 'r') as f:
            data = json.load(f)
            progress = data.get("progress", 0)
        return jsonify({"progress": progress})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sample_metadata', methods=['GET'])
def get_sample_metadata():
    try:
        sample_metadata_path = os.path.join(parent_dir, 'Samples', 'sample_metadata.json')
        with open(sample_metadata_path, 'r', encoding='utf-8') as f:
            sample_metadata = json.load(f)
        return jsonify(sample_metadata)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sample/<path:filename>', methods=['GET'])
def get_sample(filename):
    try:
        sample_path = os.path.join(parent_dir, 'Samples', filename)
        if os.path.exists(sample_path):
            return send_file(sample_path, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sample/search', methods=['GET'])
def search_samples():
    query = request.args.get('query', '').lower()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    samples_dir = os.path.join(project_root, 'Samples')
    filepath = os.path.join(samples_dir, f'sample_metadata.json')
    with open(filepath, 'r') as f:
        data = json.load(f)
    results = [item for item in data if query.lower() in json.dumps(item).lower()]
    return jsonify(results)


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
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'AgentConfig', agent_type, 'MusicCreationChainConfig.json')
    logger.info("config_path " + config_path)
    if not os.path.exists(config_path):
        return jsonify({"error": f"Configuration file not found: {config_path}"}), 404

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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

from App.sonicPi import SonicPi

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
        ip_address = artist_config["sonic_pi_IP"]
        port = int(artist_config["sonic_pi_port"])

        # Create a Song instance
        song = Song(name=song_name, logger=logger)

        # Read the script file
        script_file_path = f"{os.path.dirname(current_dir)}\\Songs\\{song_name}\\{song_name}.rb"
        with open(script_file_path, 'r') as file:
            full_script = file.read()

        # Initialize SonicPi instance
        sonic_pi = SonicPi(logger)

        # Call Sonic Pi with the song, IP address, port, and script content
        sonic_pi.call_sonicpi(song, ip_address, port, full_script)

        return jsonify({"message": "Code sent to Sonic Pi"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/songs', methods=['GET'])
def list_songs():
    songs_dir = os.path.join(parent_dir, 'Songs')
    try:
        songs = [f for f in os.listdir(songs_dir) if os.path.isdir(os.path.join(songs_dir, f))]
        return jsonify({"songs": songs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import shutil

@app.route('/api/songs/<song>', methods=['DELETE'])
def delete_song(song):
    song_path = os.path.join(parent_dir, 'Songs', song)
    try:
        if os.path.exists(song_path) and os.path.isdir(song_path):
            shutil.rmtree(song_path)
            return jsonify({"message": "Song deleted successfully"})
        else:
            return jsonify({"error": "Song not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/songs/<song>/image', methods=['GET'])
def get_song_image(song):
    song_path = os.path.join(parent_dir, 'Songs', song, f'{song}.png')
    if os.path.exists(song_path):
        return send_file(song_path, mimetype='image/png')
    else:
        return jsonify({'error': 'Image not found'}), 404

def read_progress():
    global progress
    try:
        with open(progress_file, 'r') as f:
            data = json.load(f)
            progress = data.get("progress", 0)
    except Exception as e:
        progress = 0

executor = ThreadPoolExecutor(max_workers=1)


UPLOAD_DIRECTORY = os.path.join(os.path.dirname(__file__), '..', 'Samples', 'Uploaded')

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

@app.route('/api/upload_samples', methods=['POST'])
def upload_samples():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    for file in files:
        file.save(os.path.join(UPLOAD_DIRECTORY, file.filename))

    return jsonify({"status": "success"}), 200

@app.route('/api/sonicpi/config', methods=['GET'])
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

@app.route('/api/sonicpi/config', methods=['POST'])
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

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.json
    sonic_pi_code = ''
    songName = data.get('song_name')

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    songs_dir = os.path.join(project_root, 'songs')
    if not os.path.exists(songs_dir):
        os.makedirs(songs_dir)
    song_log_directory = os.path.join(songs_dir, songName)
    if not os.path.exists(song_log_directory):
        os.makedirs(song_log_directory)

    song_log_directory = os.path.join(songs_dir, songName)
    filepath = os.path.join(song_log_directory, f'{songName}.rb')
    app.logger.debug(f"Looking for file in: {filepath}")
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            sonic_pi_code = file.read()

    selected_files = data.get('selectedFiles', [])
    samples_str = ', '.join(item.get('Filename', '') for item in selected_files if isinstance(item, dict))

    phrase = f'Following samples (external to Sonic Pi) can be used: {samples_str}.'

    user_comment = data.get('message')
    if samples_str:
        user_comment += ' ' + phrase

    selected_model = data.get('selected_model', 'gpt-4o-mini')
    api_provider = data.get('api_provider', 'openai')

    app.logger.debug(f"sonic_pi_code retrieved: {sonic_pi_code}")
    app.logger.debug(f"Received chat request: {data}")

    song = Song(name=songName, logger=logger)

    agent = GPTAgent(
        selected_model=selected_model,
        logger=logger,
        song=song,
        agentType='default',  # Not used in this context
        api_provider=api_provider
    )

    chatResponse = agent.handle_chat_input(sonic_pi_code, user_comment)
    app.logger.debug(f"Chat response: {chatResponse}")

    song_log_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'songs', songName)
    chat_history_file = os.path.join(song_log_directory, 'chat_history.json')

    # Load existing chat history
    if os.path.exists(chat_history_file):
        with open(chat_history_file, 'r') as file:
            chat_history = json.load(file)
    else:
        chat_history = []

    # Append new chat entry
    chat_history.append({
        "role": "user",
        "content": user_comment
    })
    chat_history.append({
        "role": "assistant",
        "content": chatResponse
    })

    # Save updated chat history
    with open(chat_history_file, 'w') as file:
        json.dump(chat_history, file, indent=2)

    if chatResponse is not None:
        return jsonify({"comment": chatResponse})
    else:
        return jsonify({"error": "No response from agent"})

@app.route('/api/conversation_history', methods=['GET'])
def get_conversation_history():
    song_name = request.args.get('song_name', 'default_song')
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conversation_history_path = os.path.join(project_root, 'songs', song_name, 'chat_history.json')
    if os.path.exists(conversation_history_path):
        with open(conversation_history_path, 'r') as file:
            conversation_history = json.load(file)
        return jsonify(conversation_history)
    else:
        return jsonify([])

if __name__ == '__main__':
    socketio.run(app, debug=True)

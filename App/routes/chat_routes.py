from flask import Blueprint, request, jsonify
import os
import json
import logging
import sys

chat_bp = Blueprint('chat', __name__)
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(root_dir)

from App.services.agent import GPTAgent
from App.services.song import Song

@chat_bp.route('/chat', methods=['POST'])
def handle_chat():
    data = request.json
    sonic_pi_code = ''
    songName = data.get('song_name')

    songs_dir = os.path.join(root_dir, 'songs')
    if not os.path.exists(songs_dir):
        os.makedirs(songs_dir)
    song_log_directory = os.path.join(songs_dir, songName)
    if not os.path.exists(song_log_directory):
        os.makedirs(song_log_directory)

    song_log_directory = os.path.join(songs_dir, songName)
    filepath = os.path.join(song_log_directory, f'{songName}.rb')
    logger.debug(f"Looking for file in: {filepath}")
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            sonic_pi_code = file.read()

    selected_files = data.get('selectedFiles', [])

    samples_metadata_path = os.path.join(root_dir, 'Samples', 'sample_metadata.json')
    with open(samples_metadata_path, 'r') as f:
        sample_metadata = json.load(f)

    # Create a lookup dictionary for fast access by filename
    metadata_lookup = {item['Filename']: item for item in sample_metadata}

    # For each selected file, get its full metadata
    selected_metadata = []
    for item in selected_files:
        filename = item.get('Filename', '')
        if filename in metadata_lookup:
            selected_metadata.append(metadata_lookup[filename])
        else:
            # Optionally, handle missing metadata
            selected_metadata.append({'Filename': filename, 'Error': 'Metadata not found'})

    # Now, selected_metadata is a list of dicts with all metadata for each selected file
    # You can convert it to a JSON string for display or further processing
    samples_str = json.dumps(selected_metadata, indent=2)

    phrase = f'Following samples (external to Sonic Pi) can be used: {samples_str}.'

    user_comment = data.get('message')
    if samples_str:
        user_comment += ' ' + phrase

    selected_model = data.get('selected_model', 'gpt-4o-mini')
    api_provider = data.get('api_provider', 'openai')

    logger.debug(f"sonic_pi_code retrieved: {sonic_pi_code}")
    logger.debug(f"Received chat request: {data}")

    song = Song(name=songName, logger=logger)

    agent = GPTAgent(
        selected_model=selected_model,
        logger=logger,
        song=song,
        agentType='default',  # Not used in this context
        api_provider=api_provider
    )

    chatResponse = agent.handle_chat_input(sonic_pi_code, user_comment)
    logger.debug(f"Chat response: {chatResponse}")

    song_log_directory = os.path.join(root_dir, 'songs', songName)

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

@chat_bp.route('/conversation_history', methods=['GET'])
def get_conversation_history():
    song_name = request.args.get('song_name', 'default_song')
    conversation_history_path = os.path.join(root_dir, 'songs', song_name, 'chat_history.json')
    if os.path.exists(conversation_history_path):
        with open(conversation_history_path, 'r') as file:
            conversation_history = json.load(file)
        return jsonify(conversation_history)
    else:
        return jsonify([])
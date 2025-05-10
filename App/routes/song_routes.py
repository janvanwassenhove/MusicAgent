from flask import Blueprint, request, jsonify, send_file
import os
import json
import logging
import sys
import shutil

song_bp = Blueprint('song', __name__)
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(root_dir)

@song_bp.route('/timeline')
def get_timeline():
    agent_type = request.args.get('agent_type', 'mITyJohn')  # Default to mITyJohn if not specified
    config_path = os.path.join(root_dir, 'AgentConfig', agent_type, 'MusicCreationChainConfig.json')
    logger.info("config_path " + config_path)
    if not os.path.exists(config_path):
        return jsonify({"error": f"Configuration file not found: {config_path}"}), 404

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@song_bp.route('/songs', methods=['GET'])
def list_songs():
    songs_dir = os.path.join(root_dir, 'Songs')
    try:
        songs = [f for f in os.listdir(songs_dir) if os.path.isdir(os.path.join(songs_dir, f))]
        return jsonify({"songs": songs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@song_bp.route('/songs/<song>', methods=['DELETE'])
def delete_song(song):
    song_path = os.path.join(root_dir, 'Songs', song)
    try:
        if os.path.exists(song_path) and os.path.isdir(song_path):
            shutil.rmtree(song_path)
            return jsonify({"message": "Song deleted successfully"})
        else:
            return jsonify({"error": "Song not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@song_bp.route('/songs/<song>/image', methods=['GET'])
def get_song_image(song):
    song_path = os.path.join(root_dir, 'Songs', song, f'{song}.png')
    if os.path.exists(song_path):
        return send_file(song_path, mimetype='image/png')
    else:
        return jsonify({'error': 'Image not found'}), 404

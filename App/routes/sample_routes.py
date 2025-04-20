from flask import Blueprint, request, jsonify, send_file
import os
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from App.services.SampleMedataListing import process_directory

sample_bp = Blueprint('sample', __name__)
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(root_dir)

progress_file = os.path.join(root_dir, 'progress.json')
executor = ThreadPoolExecutor(max_workers=1)
UPLOAD_DIRECTORY = os.path.join(root_dir, 'Samples', 'Uploaded')
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Run sample metadata listing
default_samples_dir = os.path.join(root_dir, 'Samples')

@sample_bp.route('/run_sample_metadata_listing', methods=['POST'])
def run_sample_metadata_listing_endpoint():
    logger.info("run_sample_metadata_listing API called")
    try:
        input_directory = default_samples_dir
        executor.submit(process_directory, input_directory)
        return jsonify({"status": "accepted"}), 202
    except Exception as e:
        logger.error(f"Error running sample metadata listing: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@sample_bp.route('/sample_metadata_progress', methods=['GET'])
def sample_metadata_progress():
    try:
        with open(progress_file, 'r') as f:
            data = json.load(f)
            progress = data.get("progress", 0)
        return jsonify({"progress": progress})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sample_bp.route('/sample_metadata', methods=['GET'])
def get_sample_metadata():
    try:
        sample_metadata_path = os.path.join(root_dir, 'Samples', 'sample_metadata.json')
        with open(sample_metadata_path, 'r', encoding='utf-8') as f:
            sample_metadata = json.load(f)
        return jsonify(sample_metadata)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sample_bp.route('/sample/<path:filename>', methods=['GET'])
def get_sample(filename):
    try:
        sample_path = os.path.join(root_dir, 'Samples', filename)
        if os.path.exists(sample_path):
            return send_file(sample_path, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sample_bp.route('/sample/search', methods=['GET'])
def search_samples():
    query = request.args.get('query', '').lower()
    samples_dir = os.path.join(root_dir, 'Samples')
    filepath = os.path.join(samples_dir, f'sample_metadata.json')
    with open(filepath, 'r') as f:
        data = json.load(f)
    results = [item for item in data if query.lower() in json.dumps(item).lower()]
    return jsonify(results)

@sample_bp.route('/upload_samples', methods=['POST'])
def upload_samples():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    for file in files:
        file.save(os.path.join(UPLOAD_DIRECTORY, file.filename))

    return jsonify({"status": "success"}), 200

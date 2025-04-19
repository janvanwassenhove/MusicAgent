from flask import Blueprint, request, jsonify
import os
import json
import logging
import sys

sonicpi_bp = Blueprint('sonicpi', __name__)
logger = logging.getLogger()

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Helper functions

# Routes
from flask import Blueprint

# Import all route blueprints
from .agent_routes import agent_bp
from .song_routes import song_bp
from .sample_routes import sample_bp
from .sonicpi_routes import sonicpi_bp
from .chat_routes import chat_bp

def register_routes(app):
    """Register all blueprints with the app"""
    app.register_blueprint(agent_bp, url_prefix='/api')
    app.register_blueprint(song_bp, url_prefix='/api')
    app.register_blueprint(sample_bp, url_prefix='/api')
    app.register_blueprint(sonicpi_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')

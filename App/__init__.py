from flask import Flask
from flask_socketio import SocketIO
from App.config import config
from flask_cors import CORS

socketio = SocketIO()

def create_app(config_name='default'):
    app = Flask(__name__,
                static_folder='../static',
                template_folder='../templates')
    app.config.from_object(config[config_name])

    CORS(app)

    socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error"}, 500

    return app

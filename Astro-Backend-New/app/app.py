
import os
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO
from dotenv import load_dotenv
from routes.auth import auth_bp
from routes.survey import survey_bp
from routes.pujari import pujari_bp
from routes.pooja import pooja_bp
from routes.astrology import astro_bp
from routes.chat import chat_bp, init_socket_events

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(survey_bp)
    app.register_blueprint(pujari_bp)
    app.register_blueprint(pooja_bp)
    app.register_blueprint(astro_bp)
    app.register_blueprint(chat_bp, url_prefix='/chat')
    
    # Add a route to serve the chat interface
    @app.route('/chat')
    def chat():
        return "Chat Service Active"  # Or render your chat template if you have one
    
    # Initialize Socket.IO
    socketio = SocketIO(app, cors_allowed_origins="*")
    init_socket_events(socketio)
    
    return app, socketio

if __name__ == "__main__":
    app, socketio = create_app()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
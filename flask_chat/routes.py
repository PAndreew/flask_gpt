from flask import Blueprint, render_template
from flask_socketio import emit
from .app import db, socketio, chatgpt_chain
from .models import Message
from flask import current_app as app

chat_blueprint = Blueprint('chat', __name__)

@chat_blueprint.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handle_message(msg):
    # Store the message in the database
    message = Message(text=msg)
    db.session.add(message)
    db.session.commit()

    # Generate a response using the AI model
    output = chatgpt_chain.predict(human_input=msg)
    
    # Store the AI's response in the database
    response = Message(text=output)
    db.session.add(response)
    db.session.commit()

    # Broadcast the response to all connected clients
    emit('message', output, broadcast=True)

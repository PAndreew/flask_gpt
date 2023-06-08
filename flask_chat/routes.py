from flask import Blueprint, render_template
from flask_socketio import emit
from .app import db, socketio, chatgpt_chain
from .models import Message

chat_blueprint = Blueprint('chat', __name__)

@chat_blueprint.route('/')
def index():
    return render_template('index.html')

@socketio.on('message')
def handleMessage(msg):
    message = Message(text=msg)
    db.session.add(message)
    db.session.commit()

    # Broadcast the message to all clients
    emit('message', {'msg': msg, 'sender': 'user'}, broadcast=True)

    output = chatgpt_chain.predict(human_input=msg)
    
    response = Message(text=output)
    db.session.add(response)
    db.session.commit()

    emit('message', {'msg': 'Assistant: ' + output, 'sender': 'ai'}, broadcast=True)


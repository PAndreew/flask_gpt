from flask import Blueprint, request, session, redirect, url_for, render_template
from flask_socketio import emit, join_room
from ..app import db, socketio, chatgpt_chain
from ..models import Message, User, Room, UserRoom
from ..utils import generate_light_color

chat_blueprint = Blueprint('chat', __name__)

@chat_blueprint.route('/chat')
def chat():
    if 'username' not in session:
        # The user is not logged in, so redirect them to the login page
        return redirect(url_for('chat.index'))
    else:
        # The user is logged in, so show the chat page
        return render_template('chat.html')
    
@socketio.on('message')
def handleMessage(msg):
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    color = user.color if user else '#000000'
    message = Message(text=msg)
    db.session.add(message)
    db.session.commit()

    # Broadcast the message to all clients
    emit('message', {'msg': msg, 'sender': user.username, 'color': color}, broadcast=True)

    output = chatgpt_chain.predict(human_input=msg)
    
    response = Message(text=output)
    db.session.add(response)
    db.session.commit()

    emit('message', {'msg': 'Assistant: ' + output, 'sender': 'ai'}, broadcast=True)
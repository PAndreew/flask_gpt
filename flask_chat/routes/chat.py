from flask import Blueprint, request, session, render_template, jsonify
from flask_socketio import emit
from flask_login import login_required
from ..app import db, socketio
from ..models import Message, User, Room, UserRoom

chat_blueprint = Blueprint('chat', __name__)

@chat_blueprint.route('/chat')
@login_required
def chat():
    # The user is logged in, so show the chat page
    return render_template('chat.html')
    
@socketio.on('message')
def handleMessage(data):
    raw_msg = data.get('message')
    room_id = data.get('room_id')

    # Parse the AI model name and the message from the raw message
    if raw_msg.startswith('#'):
        aimodel_name, msg = raw_msg.split(' ', 1)
        aimodel_name = aimodel_name[1:]  # Remove the '#' prefix
    else:
        aimodel_name = None
        msg = raw_msg

    # Get the user information
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    color = user.color if user else '#000000'

    # Check if the user is in the room
    user_room = UserRoom.query.filter_by(user_id=user.id, room_id=room_id).first()
    if not user_room:
        return  # The user is not in the room, so don't process the message

    # Save the message
    message = Message(text=msg, user_id=user.id, room_id=room_id)
    db.session.add(message)
    db.session.commit()

    # Broadcast the message to all clients in the room
    emit('message', {'msg': msg, 'sender': user.username, 'color': color}, room=room_id)

    # Get the AI response
    room = Room.query.get(room_id)
    if room:
        # Look for the AI model with the specified name
        aimodel = next((m for m in room.ai_models if m.name == aimodel_name), None)
        if aimodel:
            ai_output = aimodel.predict(human_input=msg)

            # Save the response
            response = Message(text=ai_output, user_id=None, room_id=room_id)  # No user_id for AI responses
            db.session.add(response)
            db.session.commit()

            # Broadcast the AI response to all clients in the room
            emit('message', {'msg': 'Assistant: ' + ai_output, 'sender': 'ai'}, room=room_id)

@chat_blueprint.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')  # Get the query parameter from the URL
    results = User.query.filter(User.username.like('%' + query + '%')).all()
    users = [{"id": user.id, "username": user.username} for user in results]  # Convert User objects to a list of dictionaries with id and username
    return jsonify(users)  # Return the results as JSON


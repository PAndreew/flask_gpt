from flask import Blueprint, request, render_template, jsonify
from flask_socketio import emit
from flask_login import login_required, current_user
from ..app import db, socketio
from ..models import Message, User, Room, UserRoom
from ..aimodels import AIModelManager, ai_model_colors
from sqlalchemy.orm import joinedload

chat_blueprint = Blueprint('chat', __name__)

# Initialize the AI model manager
aimodel_manager = AIModelManager()

@chat_blueprint.route('/chat')
@login_required
def chat():
    # The user is logged in, so show the chat page

    # Fetch the first room of the current user
    first_room = (
        Room.query
        .options(joinedload(Room.users))
        .filter(UserRoom.user_id == current_user.id)
        .first()
    )

    room_id = first_room.id if first_room else None

    return render_template('chat.html', room_id=room_id, username=current_user.username)
    

# @socketio.on('connect')
# def test_connect():
#     emit('message', {'msg': 'Connected', 'sender': 'Server', 'color': '#000000'})


# @socketio.on('message')
# def handle_message(data):
#     print('Received message: ' + str(data))


@socketio.on('message')
def handleMessage(data):
    print("Calling handlemessage")
    raw_msg = data.get('message')
    room_id = data.get('room_id')
    username = current_user.username

    user = User.query.filter_by(username=username).first()
    color = user.color if user else '#000000'

    # Parse the AI model name and the message from the raw message
    ai_output = None
    if raw_msg.startswith('#'):
        aimodel_name, msg = raw_msg.split(' ', 1)
        aimodel_name = aimodel_name[1:]  # Remove the '#' prefix

        # If an AI model name was specified, switch to that model
        aimodel_manager.switch_model(aimodel_name)

        # Generate the AI response
        ai_output = aimodel_manager.generate_response(msg)

        ai_color = ai_model_colors.get(aimodel_name, '#111111')

    else:
        msg = raw_msg

    # Save the user's message
    user_message = Message(text=msg, user_id=user.id, room_id=room_id)
    db.session.add(user_message)
    db.session.commit()

    # Broadcast the user's message to all clients in the room
    emit('message', {'msg': msg, 'sender': user.username, 'color': color}, room=room_id)
    print('Message sent to room', room_id)

    if ai_output:
        # Save the AI's response
        ai_response = Message(text=ai_output, aimodel_name=aimodel_manager.current_model_name, user_id=None, room_id=room_id, message_color=ai_color)  # No user_id for AI responses
        db.session.add(ai_response)
        db.session.commit()

        # Broadcast the AI's response to all clients in the room
        emit('message', {'msg': 'Assistant: ' + ai_output, 'sender': 'ai', 'color': ai_color}, room=room_id)


@chat_blueprint.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')  # Get the query parameter from the URL
    results = User.query.filter(User.username.like('%' + query + '%')).all()
    users = [{"id": user.id, "username": user.username} for user in results]  # Convert User objects to a list of dictionaries with id and username
    return jsonify(users)  # Return the results as JSON


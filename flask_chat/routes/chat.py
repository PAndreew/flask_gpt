from flask import Blueprint, request, render_template, jsonify
from flask_socketio import emit
from flask_login import login_required, current_user
from ..app import db, socketio
from ..models import Message, User, Room, UserRoom
from ..aimodels import AIModelManager
from ..tasks import generate_ai_response
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
    
@socketio.on('message')
def handleMessage(data):
    print("Calling handlemessage")
    raw_msg = data.get('message')
    room_id = data.get('room_id')
    username = current_user.username

    user = User.query.filter_by(username=username).first()
    color = user.color if user else '#000000'

    # Parse the AI model name and the message from the raw message
    if raw_msg.startswith('#'):
        aimodel_name, msg = raw_msg.split(' ', 1)
        aimodel_name = aimodel_name[1:]  # Remove the '#' prefix

        # Save the user's message
        user_message = Message(text=msg, user_id=user.id, room_id=room_id)
        db.session.add(user_message)
        db.session.commit()

        # Broadcast the user's message to all clients in the room
        emit('message', {'msg': msg, 'sender': user.username, 'color': color}, room=room_id)
        print('Message sent to room', room_id)

        # If an AI model name was specified, switch to that model and generate the AI response
        # generate_ai_response.delay(aimodel_name, msg, room_id)

        task = generate_ai_response.delay(aimodel_name, msg, room_id)  # However you're calling the task

        # Print the task id
        print(f"Task ID: {task.id}")

        # Print the task status
        print(f"Task Status: {task.state}")

        # Try to get the result of the task
        result = task.result

        # Print the result if it exists
        if result is not None:
            print(f"Task Result: {result}")
        else:
            print("Task has not finished yet.")

    else:
        msg = raw_msg

        # Save the user's message
        user_message = Message(text=msg, user_id=user.id, room_id=room_id)
        db.session.add(user_message)
        db.session.commit()

        # Broadcast the user's message to all clients in the room
        emit('message', {'msg': msg, 'sender': user.username, 'color': color}, room=room_id)
        print('Message sent to room', room_id)

@chat_blueprint.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')  # Get the query parameter from the URL
    results = User.query.filter(User.username.like('%' + query + '%')).all()
    users = [{"id": user.id, "username": user.username} for user in results]  # Convert User objects to a list of dictionaries with id and username
    return jsonify(users)  # Return the results as JSON


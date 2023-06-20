from flask import Blueprint, request, render_template, jsonify, send_from_directory
from flask_socketio import emit
from flask_login import login_required, current_user
from ..app import db, socketio
from ..models import Message, User, Room, UserRoom
from ..aimodels import AIModelManager
from ..tasks import generate_ai_response, on_task_done
from ..utils import upload_to_server, UPLOAD_FOLDER
from sqlalchemy.orm import joinedload

chat_blueprint = Blueprint('chat', __name__)

# Initialize the AI model manager
aimodel_manager = AIModelManager()

@chat_blueprint.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


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

    aimodel_name, msg, media_type, media_url, message_color = None, raw_msg, None, None, color

    # Check if message is from an AI model
    if raw_msg.startswith('#'):
        aimodel_name, msg = raw_msg.split(' ', 1)
        aimodel_name = aimodel_name[1:]  # Remove the '#' prefix
        message_color = color  # AI messages use color from User

        task = generate_ai_response.apply_async(args=[aimodel_name, msg, room_id], link=on_task_done)

        # Print the task id
        print(f"Task ID: {task.id}")

        # Print the task status
        print(f"Task Status: {task.state}")

        # Try to get the result of the task
        result = task.result

        # If the result exists
        if result is not None:
            print(f"Task Result: {result}")
            if result["type"] == "text":
                msg = result["content"]
            else:
                media_type = result["type"]
                media_url = upload_to_server(result["content"], media_type)  # upload the content to your storage service

            # Broadcast the AI's message to all clients in the room
            emit('message', {
                'msg': msg,
                'media_type': media_type,
                'sender': 'ai',
                'color': color,
                'media_url': media_url,
                'message_color': message_color
            }, room=room_id)

            print('AI Message sent to room', room_id)
        else:
            print("Task has not finished yet.")

    # Save the user's or AI's message
    user_message = Message(
        text=msg, 
        media_url=media_url, 
        media_type=media_type, 
        user_id=user.id, 
        room_id=room_id, 
        aimodel_name=aimodel_name, 
        message_color=message_color
    )
    db.session.add(user_message)
    db.session.commit()

    # Broadcast the user's message to all clients in the room
    emit('message', {
        'msg': msg,
        'media_type': media_type,
        'sender': user.username, 
        'color': color,
        'media_url': media_url,
        'message_color': message_color
    }, room=room_id)

    print('Message sent to room', room_id)



@chat_blueprint.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')  # Get the query parameter from the URL
    results = User.query.filter(User.username.like('%' + query + '%')).all()
    users = [{"id": user.id, "username": user.username} for user in results]  # Convert User objects to a list of dictionaries with id and username
    return jsonify(users)  # Return the results as JSON


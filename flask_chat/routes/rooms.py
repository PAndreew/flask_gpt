from flask import Blueprint, session, jsonify, request, current_app
from flask_login import current_user, login_required
from flask_socketio import join_room, emit
from ..app import db, socketio
from ..models import Message, User, Room, UserRoom
from ..utils import notify_user
from ..aimodels import ai_model_colors

rooms_blueprint = Blueprint('room', __name__)

@socketio.on('join')
def on_join(data):
    room_id = data['room_id']
    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    if not user:
        emit('join_response', {'error': 'User not found.'}, room=request.sid)
        return

    # Check if the user is a member of the room
    user_room = UserRoom.query.filter_by(user_id=user.id, room_id=room_id).first()

    if not user_room:
        # Add the user to the room if they are not already a member
        user_room = UserRoom(user_id=user.id, room_id=room_id)
        db.session.add(user_room)
        db.session.commit()

    join_room(room_id)
    emit('join_response', {'message': 'Successfully joined the room.', 'room_id': room_id}, room=request.sid)


@rooms_blueprint.route('/room/<int:room_id>', methods=['GET'])
def room(room_id):
    room = Room.query.get(room_id)

    if not room or not any(user_room.user_id == current_user.id for user_room in room.users):
        current_app.logger.info(f"current_user: {current_user}, room.users: {[str(user_room) for user_room in room.users]}")
        return jsonify({"error": "Room not found or you are not a part of this room."}), 404

    messages = Message.query.filter_by(room_id=room.id).all()  # Get the room's messages.

    # Modify each message's dictionary to include the sender's username and color.
    message_dicts = []
    for message in messages:
        msg_dict = message.to_dict()

        if message.aimodel_name:
            # AI message
            msg_dict['sender'] = 'ai'
            msg_dict['color'] = ai_model_colors.get(message.aimodel_name, '#111111')  # Get the color for this AI model, or default to '#111111'
        else:
            # User message
            user = User.query.get(message.user_id)
            msg_dict['sender'] = user.username
            msg_dict['color'] = user.color

        message_dicts.append(msg_dict)

    return jsonify(room=room.to_dict(), messages=message_dicts), 200



@rooms_blueprint.route('/create_room/<int:user_id>', methods=['POST'])
@login_required
def create_room(user_id):
    if user_id == current_user.id:
        return jsonify({"error": "Cannot create a room with yourself."}), 400

    other_user = User.query.get(user_id)
    if not other_user:
        return jsonify({"error": "Invalid user."}), 400

    # Check if a room already exists between the two users.
    existing_room = Room.query.join(UserRoom).filter(
        UserRoom.user_id.in_([current_user.id, other_user.id])
    ).group_by(Room.id).having(db.func.count() == 2).first()

    if existing_room:
        return jsonify({"error": "Room already exists.", "room_id": existing_room.id}), 409

    # Create the room if it doesn't exist.
    new_room = Room()
    db.session.add(new_room)
    db.session.flush()  # This is needed to generate room.id

    # Link the current user and the selected user to the new room.
    for user in [current_user, other_user]:
        user_room = UserRoom(user_id=user.id, room_id=new_room.id)
        db.session.add(user_room)
    
    db.session.commit()

    # Notify the other user about the new room.
    notify_user(other_user, f"You have been invited to a new chat room by {current_user.username}")

    # Emit the new_room event
    emit('new_room', {'room_id': new_room.id}, namespace='/chat', room=other_user.username)

    return jsonify({"message": "Room created successfully.", "room_id": new_room.id}), 200


@rooms_blueprint.route('/accept_invitation/<int:room_id>', methods=['POST'])
@login_required
def accept_invitation(room_id):
    user_room = UserRoom.query.filter_by(user_id=current_user.id, room_id=room_id).first()

    if not user_room:
        return jsonify({"error": "Invalid room."}), 400

    user_room.status = 'accepted'  # Assume you added a status field to UserRoom.
    db.session.commit()

    return jsonify({"message": "You have joined the room."}), 200

@rooms_blueprint.route('/get_rooms', methods=['GET'])
@login_required
def get_rooms():
    # Get the rooms for the current user
    rooms = Room.query.join(UserRoom).filter_by(user_id=current_user.id).all()
    # Convert the rooms to dictionaries and return them
    return jsonify(rooms=[room.to_dict() for room in rooms])

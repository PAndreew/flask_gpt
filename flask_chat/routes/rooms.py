from flask import Blueprint, session, redirect, url_for, render_template, jsonify, flash, make_response
from flask_login import current_user, login_required
from flask_socketio import join_room
from ..app import db, socketio
from ..models import Message, User, Room, UserRoom
from ..utils import notify_user

rooms_blueprint = Blueprint('room', __name__)


@socketio.on('join')
def on_join(data):
    room_id = data['room_id']
    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    user = User.query.filter_by(username=username).first()
    if not user:
        response = jsonify({"error": "User not found."})
        return make_response(response, 404)
    
    # Check if the user is a member of the room
    user_room = UserRoom.query.filter_by(user_id=user.id, room_id=room_id).first()

    if not user_room:
        # Add the user to the room if they are not already a member
        user_room = UserRoom(user_id=user.id, room_id=room_id)
        db.session.add(user_room)
        db.session.commit()

    join_room(room_id)


@rooms_blueprint.route('/room/<int:room_id>', methods=['GET'])
def room(room_id):
    room = Room.query.get(room_id)
    if not room or current_user not in room.users:
        flash('Room not found or you are not a part of this room.')
        return redirect(url_for('chat_blueprint.chat'))

    messages = Message.query.filter_by(room_id=room.id).all()  # Get the room's messages.
    return render_template('chat.html', room=room, messages=messages)

@rooms_blueprint.route('/create_room/<int:user_id>', methods=['POST'])
@login_required
def create_room(user_id):
    user = User.query.get(user_id)
    if not user or user == current_user:
        return jsonify({"error": "Invalid user."}), 400

    room = Room()
    db.session.add(room)
    db.session.flush()  # This is needed to generate room.id

    # Link the current user and the selected user to the new room.
    for user in [current_user, user]:
        user_room = UserRoom(user_id=user.id, room_id=room.id)
        db.session.add(user_room)
    
    db.session.commit()

    # Notify the selected user about the new room.
    # This is just a placeholder, the actual implementation will depend on how you're handling notifications.
    notify_user(user, f"You have been invited to a new chat room by {current_user.username}")

    return jsonify({"message": "Room created successfully.", "room_id": room.id}), 200

@rooms_blueprint.route('/accept_invitation/<int:room_id>', methods=['POST'])
@login_required
def accept_invitation(room_id):
    user_room = UserRoom.query.filter_by(user_id=current_user.id, room_id=room_id).first()

    if not user_room:
        return jsonify({"error": "Invalid room."}), 400

    user_room.status = 'accepted'  # Assume you added a status field to UserRoom.
    db.session.commit()

    return jsonify({"message": "You have joined the room."}), 200

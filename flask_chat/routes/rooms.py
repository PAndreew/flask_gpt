from flask import Blueprint, request, session, redirect, url_for, render_template
from flask_socketio import join_room
from ..app import db, socketio
from ..models import Message, User, Room, UserRoom

rooms_blueprint = Blueprint('room', __name__)


@socketio.on('join')
def on_join(data):
    room_id = data['room_id']
    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    # Check if the user is a member of the room
    user_room = UserRoom.query.filter_by(user_id=user.id, room_id=room_id).first()

    if not user_room:
        # Add the user to the room if they are not already a member
        user_room = UserRoom(user_id=user.id, room_id=room_id)
        db.session.add(user_room)
        db.session.commit()

    join_room(room_id)


@rooms_blueprint.route('/rooms', methods=['GET', 'POST'])
def rooms():
    if 'username' not in session:
        # The user is not logged in, so redirect them to the login page
        return redirect(url_for('room.index'))

    if request.method == 'POST':
        # Create a new room
        room = Room()
        db.session.add(room)
        db.session.commit()

        # Add the user to the room
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        user_room = UserRoom(user_id=user.id, room_id=room.id)
        db.session.add(user_room)
        db.session.commit()

        return redirect(url_for('chat.room', room_id=room.id))

    else:
        # Show the rooms page
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
        rooms = Room.query.join(UserRoom).filter(UserRoom.user_id == user.id).all()
        return render_template('rooms.html', rooms=rooms)
    
@rooms_blueprint.route('/room/<int:room_id>')
def room(room_id):
    if 'username' not in session:
        # The user is not logged in, so redirect them to the login page
        return redirect(url_for('auth.login'))

    # Show the chat page for the room
    return render_template('chat.html', room_id=room_id)
from datetime import datetime
from flask_chat.app import db

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))  # A message is associated with a room

    def __repr__(self):
        return '<Message %r>' % self.text


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    color = db.Column(db.String(7)) # for storing color in HEX format
    rooms = db.relationship('UserRoom', back_populates='user')
    sent_invitations = db.relationship('Invitation', foreign_keys='Invitation.sender_id', backref='sender', lazy='dynamic')
    received_invitations = db.relationship('Invitation', foreign_keys='Invitation.receiver_id', backref='receiver', lazy='dynamic')

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    aimodels = db.relationship('AIModel', backref='associated_room', lazy='dynamic')
    users = db.relationship('UserRoom', back_populates='room')  # Added this relationship
    messages = db.relationship('Message', lazy='dynamic')  # Messages in this room

class UserRoom(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), primary_key=True)
    user = db.relationship("User", back_populates="rooms")
    room = db.relationship("Room", back_populates="users")

class AIModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(50), nullable=False)  # e.g., "LLM", "Generative", etc.
    state = db.Column(db.PickleType)  # Serialized state for LLM
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)  # The room the AI model is in

    # Define relationship with Room
    room = db.relationship('Room', back_populates='aimodels')  # corrected 'ai_models' to 'aimodels'

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50), nullable=False, default="pending")

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

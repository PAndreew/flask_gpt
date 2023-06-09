from datetime import datetime
from flask_chat.app import db

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return '<Message %r>' % self.text

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    color = db.Column(db.String(7)) # for storing color in HEX format
    rooms = db.relationship('UserRoom', back_populates='user')

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    autoincrement=True
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    llmchain_state = db.relationship('LLMChainState', uselist=False, back_populates='room')

class UserRoom(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), primary_key=True)
    user = db.relationship("User", back_populates="rooms")
    room = db.relationship("Room", back_populates="users")
    users = db.relationship('UserRoom', back_populates='room')

class AIModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(50), nullable=False)  # e.g., "LLM", "Generative", etc.
    state = db.Column(db.PickleType)  # Serialized state for LLM
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))  # The room the AI model is in

    # Define relationship with Room
    room = db.relationship('Room', back_populates='ai_models')

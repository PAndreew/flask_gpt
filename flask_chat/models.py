from datetime import datetime
from flask_chat.app import db
from flask_login import UserMixin


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # New field
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    user = db.relationship('User', backref='messages') # Establish relationship

    def __repr__(self):
        return '<Message %r>' % self.text

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'user_id': self.user_id, # Include in to_dict
            'room_id': self.room_id
        }

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    color = db.Column(db.String(7)) # for storing color in HEX format
    rooms = db.relationship('UserRoom', back_populates='user')
    sent_invitations = db.relationship('Invitation', foreign_keys='Invitation.sender_id', backref='sender', lazy='dynamic')
    received_invitations = db.relationship('Invitation', foreign_keys='Invitation.receiver_id', backref='receiver', lazy='dynamic')
    is_anonymous = db.Column(db.Boolean, default=False)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    def get_id(self):
        return str(self.id)  # Assuming id is the user's unique identifier

    def __repr__(self):
        return '<User %r>' % self.username

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "color": self.color,
            "is_active": self.is_active,
            "is_anonymous": self.is_anonymous
        }

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    aimodels = db.relationship('AIModel', lazy='dynamic')
    users = db.relationship('UserRoom', back_populates='room')
    messages = db.relationship('Message', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime as string
            'users': [user_room.user.to_dict() for user_room in self.users],  # Assuming User model has a to_dict method
            'messages': [message.to_dict() for message in self.messages.all()],  # Assuming Message model has a to_dict method
            'aimodels': [aimodel.to_dict() for aimodel in self.aimodels.all()]  # Assuming AIModel has a to_dict method
        }

class UserRoom(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), primary_key=True)
    user = db.relationship("User", back_populates="rooms")
    room = db.relationship("Room", back_populates="users")

class AIModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_type = db.Column(db.String(50), nullable=False)  # e.g., "LLM", "Generative", etc.
    state = db.Column(db.PickleType)  # Serialized state for LLM
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    room = db.relationship('Room', back_populates='aimodels')


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

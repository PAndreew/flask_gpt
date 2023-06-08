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
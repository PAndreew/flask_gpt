from flask import Blueprint, request, session, redirect, url_for, render_template
from flask_socketio import emit
from .app import db, socketio, chatgpt_chain
from .models import Message, User
from .utils import generate_light_color

chat_blueprint = Blueprint('chat', __name__)

@chat_blueprint.route('/')
def index():
    if 'username' in session:
        # The user is logged in, so redirect them to the chat page
        return render_template('chat.html')
    else:
        # The user is not logged in, so show the login page
        return render_template('index.html')

@chat_blueprint.route('/chat')
def chat():
    if 'username' not in session:
        # The user is not logged in, so redirect them to the login page
        return redirect(url_for('chat.index'))
    else:
        # The user is logged in, so show the chat page
        return render_template('chat.html')


@socketio.on('message')
def handleMessage(msg):
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    color = user.color if user else '#000000'
    message = Message(text=msg)
    db.session.add(message)
    db.session.commit()

    # Broadcast the message to all clients
    emit('message', {'msg': msg, 'sender': user.username, 'color': color}, broadcast=True)

    output = chatgpt_chain.predict(human_input=msg)
    
    response = Message(text=output)
    db.session.add(response)
    db.session.commit()

    emit('message', {'msg': 'Assistant: ' + output, 'sender': 'ai'}, broadcast=True)


@chat_blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        color = generate_light_color()
        if username:  # Check if username is not empty
            user = User(username=username, color=color)
            db.session.add(user)
            try:
                db.session.commit()
                session['username'] = user.username
                return redirect(url_for('chat.login'))
            except Exception as e:
                print("Failed to add user. Error: ", str(e))
                db.session.rollback()
        else:
            print("Username is empty")
        return redirect(url_for('chat.signup'))
    return render_template('signup.html')



@chat_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            session['username'] = user.username
            return redirect(url_for('chat.chat'))
        else:
            return redirect(url_for('chat.signup'))
    return render_template('login.html')

@chat_blueprint.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('chat.index'))  # Redirect to the login page

from flask import Blueprint, render_template, request, redirect, url_for, session
from ..utils import generate_light_color
from ..models import User
from ..app import db

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/signup', methods=['GET', 'POST'])
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
                return redirect(url_for('auth.login'))
            except Exception as e:
                print("Failed to add user. Error: ", str(e))
                db.session.rollback()
        else:
            print("Username is empty")
        return redirect(url_for('auth.signup'))
    return render_template('signup.html')


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            session['username'] = user.username
            return redirect(url_for('chat.chat'))
        else:
            return redirect(url_for('auth.signup'))
    return render_template('login.html')

@auth_blueprint.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('auth.login'))  # Redirect to the login page
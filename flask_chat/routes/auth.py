from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from ..utils import generate_light_color
from ..models import User
from ..app import db

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('chat.chat'))  # If user is already logged in, redirect to chat

    if request.method == 'POST':
        username = request.form.get('username')
        color = generate_light_color()
        if username:  # Check if username is not empty
            user = User(username=username, color=color)
            db.session.add(user)
            try:
                db.session.commit()
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('auth.login'))
            except Exception as e:
                print("Failed to add user. Error: ", str(e))
                db.session.rollback()
        else:
            flash('Username is empty', 'error')
        return redirect(url_for('auth.signup'))
    return render_template('signup.html')


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat.chat'))  # If user is already logged in, redirect to chat

    if request.method == 'POST':
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            login_user(user)  # Here we use Flask-Login to manage the session
            return redirect(url_for('chat.chat'))
        else:
            flash('Invalid username', 'error')
            return redirect(url_for('auth.login'))  # Redirect back to login if invalid username
    return render_template('login.html')


@auth_blueprint.route('/logout')
@login_required  # Ensure the user is logged in before allowing them to log out
def logout():
    logout_user()  # Use Flask-Login's logout_user function to log out the user
    return redirect(url_for('auth.login'))  # Redirect to the login page

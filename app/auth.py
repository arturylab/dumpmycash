import functools
import re
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

def login_required(view):
    """
    View decorator that redirects anonymous users to the login page.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("You need to be logged in to view this page.", "warning")
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def api_login_required(view):
    """
    API view decorator that returns JSON error for anonymous users.
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        return view(**kwargs)
    return wrapped_view

def is_password_complex(password):
    """
    Checks if the password meets complexity requirements.
    - At least 8 characters
    - At least one uppercase or lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]", password):
        return False, "Password must contain at least one special character."
    return True, ""

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login."""
    if g.user:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('auth/login.html', input_email=email, open_register_modal=False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.home'))

        flash('Invalid email or password.', 'danger')
        return render_template('auth/login.html', input_email=email, open_register_modal=False)

    return render_template('auth/login.html', open_register_modal=False)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logs the current user out."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handles new user registration."""
    if g.user:
        return redirect(url_for('dashboard.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        error_occurred = False
        error_messages = []

        if not email or not username or not password:
            error_messages.append('Email, username, and password are required.')
            error_occurred = True
        
        is_complex, complexity_message = is_password_complex(password)
        if not is_complex and password:
            error_messages.append(complexity_message)
            error_occurred = True


        if not error_occurred:
            if User.query.filter_by(email=email).first():
                error_messages.append('Email already registered.')
                error_occurred = True

            if User.query.filter_by(username=username).first():
                error_messages.append('Username already taken.')
                error_occurred = True
        
        if error_occurred:
            for msg in error_messages:
                flash(msg, 'danger')
            return render_template('auth/login.html', 
                                   open_register_modal=True, 
                                   input_email=email, 
                                   input_username=username)

        new_user = User(email=email, username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))


    open_modal_flag = request.args.get('open_register_modal', 'false').lower() == 'true'
    return render_template('auth/login.html', open_register_modal=open_modal_flag)


@auth_bp.route('/check_username', methods=['POST'])
def check_username_availability():
    """Checks if a username is available for registration via AJAX."""
    data = request.get_json()
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'available': False, 'message': 'Username cannot be empty.'}), 400
    if len(username) < 3:
        return jsonify({'available': False, 'message': 'Username must be at least 3 characters.'}), 400
    if not re.match(r"^[a-zA-Z0-9]+$", username):
        return jsonify({'available': False, 'message': 'Username can only contain letters and numbers.'}), 400
    
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'available': False, 'message': 'Username already taken.'})
    return jsonify({'available': True, 'message': 'Username is available!'})

@auth_bp.route('/check_email', methods=['POST'])
def check_email_availability():
    """Checks if an email is available for registration via AJAX."""
    data = request.get_json()
    email = data.get('email', '').strip()

    if not email:
        return jsonify({'available': False, 'message': 'Email cannot be empty.'}), 400
    

    if "@" not in email or "." not in email.split('@')[-1] or len(email.split('@')[-1].split('.')[0]) == 0 or len(email.split('.')[-1]) < 2 :
        return jsonify({'available': False, 'message': 'Invalid email format.'})

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'available': False, 'message': 'Email already registered.'})
    return jsonify({'available': True, 'message': 'Email is available!'})
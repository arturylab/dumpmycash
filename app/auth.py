import functools
import re
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify
)
from app.models import db, User

auth_bp = Blueprint('auth', __name__)

# Password complexity patterns
PASSWORD_PATTERNS = {
    'letter': re.compile(r'[a-zA-Z]'),
    'digit': re.compile(r'\d'),
    'special': re.compile(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?~`]')
}

# Email validation pattern
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Username validation pattern
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9]+$')

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

def validate_password_complexity(password):
    """
    Validates password complexity requirements.
    
    Args:
        password (str): The password to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    
    if not PASSWORD_PATTERNS['letter'].search(password):
        return False, "Password must contain at least one letter."
    
    if not PASSWORD_PATTERNS['digit'].search(password):
        return False, "Password must contain at least one digit."
    
    if not PASSWORD_PATTERNS['special'].search(password):
        return False, "Password must contain at least one special character."
    
    return True, ""

def validate_email_format(email):
    """
    Validates email format using regex pattern.
    
    Args:
        email (str): The email to validate
        
    Returns:
        bool: True if email format is valid, False otherwise
    """
    return bool(EMAIL_PATTERN.match(email))

def validate_username_format(username):
    """
    Validates username format (alphanumeric only).
    
    Args:
        username (str): The username to validate
        
    Returns:
        bool: True if username format is valid, False otherwise
    """
    return bool(USERNAME_PATTERN.match(username)) and len(username) >= 3

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
        
        # Validate required fields
        if not all([email, username, password]):
            flash('Email, username, and password are required.', 'danger')
            return render_template('auth/login.html', 
                                   open_register_modal=True, 
                                   input_email=email, 
                                   input_username=username)
        
        # Validate password complexity
        is_complex, complexity_message = validate_password_complexity(password)
        if not is_complex:
            flash(complexity_message, 'danger')
            return render_template('auth/login.html', 
                                   open_register_modal=True, 
                                   input_email=email, 
                                   input_username=username)

        # Check for existing users
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/login.html', 
                                   open_register_modal=True, 
                                   input_email=email, 
                                   input_username=username)

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/login.html', 
                                   open_register_modal=True, 
                                   input_email=email, 
                                   input_username=username)

        # Create new user
        new_user = User(email=email, username=username)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    # Handle GET request
    open_modal_flag = request.args.get('open_register_modal', 'false').lower() == 'true'
    return render_template('auth/login.html', open_register_modal=open_modal_flag)


@auth_bp.route('/check_username', methods=['POST'])
def check_username_availability():
    """Checks if a username is available for registration via AJAX."""
    data = request.get_json()
    if not data:
        return jsonify({'available': False, 'message': 'Invalid request data.'}), 400
        
    username = data.get('username', '').strip()
    
    # Validate username format
    if not username:
        return jsonify({'available': False, 'message': 'Username cannot be empty.'}), 400
    
    if not validate_username_format(username):
        if len(username) < 3:
            return jsonify({'available': False, 'message': 'Username must be at least 3 characters.'}), 400
        else:
            return jsonify({'available': False, 'message': 'Username can only contain letters and numbers.'}), 400
    
    # Check availability
    if User.query.filter_by(username=username).first():
        return jsonify({'available': False, 'message': 'Username already taken.'})
    
    return jsonify({'available': True, 'message': 'Username is available!'})

@auth_bp.route('/check_email', methods=['POST'])
def check_email_availability():
    """Checks if an email is available for registration via AJAX."""
    data = request.get_json()
    if not data:
        return jsonify({'available': False, 'message': 'Invalid request data.'}), 400
        
    email = data.get('email', '').strip()

    # Validate email format
    if not email:
        return jsonify({'available': False, 'message': 'Email cannot be empty.'}), 400
    
    if not validate_email_format(email):
        return jsonify({'available': False, 'message': 'Invalid email format.'})

    # Check availability
    if User.query.filter_by(email=email).first():
        return jsonify({'available': False, 'message': 'Email already registered.'})
    
    return jsonify({'available': True, 'message': 'Email is available!'})
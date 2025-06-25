# app/__init__.py
from flask import Flask, g, redirect, url_for, session, render_template, Blueprint, request
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from datetime import datetime
from app.config import Config
from app.models import db, User
from app.auth import auth_bp, login_required
from app.account import account_bp
from app.categories import category_bp
from app.transactions import transaction_bp
from app.home import home as home_bp
from app.profile import profile_bp
from app.utils import format_currency

# Create the blueprint first
dashboard = Blueprint('dashboard', __name__)

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    csrf = CSRFProtect(app)
    
    # Register Jinja2 global functions
    @app.template_global()
    def now():
        """Return current datetime for use in templates."""
        return datetime.now()
    
    # Register Jinja2 filters
    @app.template_filter('currency')
    def format_currency_filter(amount):
        """Format currency with commas and two decimal places."""
        return format_currency(amount)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard)
    app.register_blueprint(home_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(profile_bp, url_prefix='/profile')
    
    @app.before_request
    def load_logged_in_user():
        """Load the logged-in user from the session before each request."""
        user_id = session.get('user_id')
        if user_id is None:
            g.user = None
        else:
            g.user = db.session.get(User, user_id)
    
    return app

# Define dashboard routes
@dashboard.route('/')
def index():
    """Redirects to the home page if logged in, otherwise to the login page."""
    if g.user:
        return redirect(url_for('home.dashboard'))
    return redirect(url_for('auth.login'))

@dashboard.route('/home')
@login_required
def home():
    """Redirect to the home blueprint."""
    return redirect(url_for('home.dashboard'))

@dashboard.route('/account')
@login_required
def account():
    """Redirect to the account blueprint."""
    return redirect(url_for('account.index'))

@dashboard.route('/transactions')
@login_required
def transactions():
    """Redirect to the transactions blueprint."""
    return redirect(url_for('transactions.list_transactions'))

@dashboard.route('/categories')
@login_required
def categories():
    """Redirect to the categories blueprint."""
    return redirect(url_for('categories.list_categories'))

@dashboard.route('/profile')
@login_required
def profile():
    """Redirect to the profile blueprint."""
    return redirect(url_for('profile.index'))

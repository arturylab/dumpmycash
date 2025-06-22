from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        """Verify the user's password."""
        return check_password_hash(self.password_hash, password)

class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    color = db.Column(db.String(7), default='#FF6384')  # Hex color for account identification
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref=db.backref('accounts', lazy=True))

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    unicode_emoji = db.Column(db.String(10), nullable=True)  # Optional emoji for the category
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('categories', lazy=True))

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.String(255), nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    account = db.relationship('Account', backref=db.backref('transactions', lazy=True))
    category = db.relationship('Category', backref=db.backref('transactions', lazy=True))
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))

class Transfer(db.Model):
    __tablename__ = 'transfers'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.String(255), nullable=True)
    from_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    to_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    to_transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)

    from_account = db.relationship('Account', foreign_keys=[from_account_id], backref=db.backref('transfers_from', lazy=True))
    to_account = db.relationship('Account', foreign_keys=[to_account_id], backref=db.backref('transfers_to', lazy=True))
    user = db.relationship('User', backref=db.backref('transfers', lazy=True))
    from_transaction = db.relationship('Transaction', foreign_keys=[from_transaction_id], backref=db.backref('transfer_from', uselist=False))
    to_transaction = db.relationship('Transaction', foreign_keys=[to_transaction_id], backref=db.backref('transfer_to', uselist=False))
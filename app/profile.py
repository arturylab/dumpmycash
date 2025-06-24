from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g, send_file
from sqlalchemy import func
from datetime import datetime, timedelta
import json
import tempfile
import os
from app.models import db, User, Account, Category, Transaction
from app.auth import login_required, api_login_required

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def index():
    """Display the user's profile page with statistics."""
    # Calculate user statistics
    stats = get_user_statistics(g.user.id)
    
    return render_template('dashboard/profile.html', **stats)

def get_user_statistics(user_id):
    """Calculate and return user statistics."""
    # Total transactions
    total_transactions = Transaction.query.filter_by(user_id=user_id).count()
    
    # Categories created
    categories_created = Category.query.filter_by(user_id=user_id).count()
    
    # Accounts managed
    accounts_managed = Account.query.filter_by(user_id=user_id).count()
    
    # Days active (days since registration)
    user = User.query.get(user_id)
    if user and user.created_at:
        days_active = (datetime.now() - user.created_at).days
    else:
        days_active = 0
    
    return {
        'total_transactions': total_transactions,
        'categories_created': categories_created,
        'accounts_managed': accounts_managed,
        'days_active': days_active
    }

@profile_bp.route('/api/stats')
@api_login_required
def api_stats():
    """API endpoint to get user statistics."""
    stats = get_user_statistics(g.user.id)
    return jsonify(stats)

@profile_bp.route('/update', methods=['POST'])
@api_login_required
def update_profile():
    """Update user profile information."""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        user = User.query.get(g.user.id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Update first name, last name, and email
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        email = data.get('email', '').strip()
        
        updated = False
        
        # Update name if provided
        if first_name or last_name:
            full_name = f"{first_name} {last_name}".strip()
            user.name = full_name if full_name else None
            updated = True
        
        # Update email if provided and different
        if email and email != user.email:
            # Check if email is already taken by another user
            existing_user = User.query.filter(User.email == email, User.id != user.id).first()
            if existing_user:
                return jsonify({'success': False, 'message': 'Email is already in use by another account'}), 400
            user.email = email
            updated = True
        
        if updated:
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Profile updated successfully!',
                'name': user.name,
                'email': user.email
            })
        else:
            return jsonify({'success': False, 'message': 'No changes were made'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating profile'}), 500

@profile_bp.route('/change-password', methods=['POST'])
@api_login_required
def change_password():
    """Change user password."""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        confirm_password = data.get('confirmPassword')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'success': False, 'message': 'All password fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
        
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters long'}), 400
        
        user = User.query.get(g.user.id)
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        if not user.check_password(current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Password changed successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error changing password'}), 500

@profile_bp.route('/export-data')
@login_required
def export_data():
    """Export user data in JSON format."""
    try:
        user_data = get_user_backup_data(g.user.id)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(user_data, temp_file, indent=2, default=str)
        temp_file.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'dumpmycash_backup_{g.user.username}_{timestamp}.json'
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/json'
        )
        
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
        return redirect(url_for('profile.index'))

@profile_bp.route('/restore-data', methods=['POST'])
@login_required 
def restore_data():
    """Restore user data from JSON file."""
    try:
        if 'backup_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('profile.index'))
        
        file = request.files['backup_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('profile.index'))
        
        if not file.filename.endswith('.json'):
            flash('Please upload a JSON file', 'error')
            return redirect(url_for('profile.index'))
        
        # Read and parse JSON
        try:
            backup_data = json.load(file)
        except json.JSONDecodeError:
            flash('Invalid JSON file format', 'error')
            return redirect(url_for('profile.index'))
        
        # Validate backup data structure
        if not validate_backup_data(backup_data):
            flash('Invalid backup file structure', 'error')
            return redirect(url_for('profile.index'))
        
        # Restore data
        result = restore_user_data(g.user.id, backup_data)
        
        if result['success']:
            flash(f"Data restored successfully! {result['message']}", 'success')
        else:
            flash(f"Error restoring data: {result['message']}", 'error')
            
        return redirect(url_for('profile.index'))
        
    except Exception as e:
        flash(f'Error restoring data: {str(e)}', 'error')
        return redirect(url_for('profile.index'))

def get_user_backup_data(user_id):
    """Get all user data for backup."""
    user = User.query.get(user_id)
    
    # Get user accounts
    accounts = Account.query.filter_by(user_id=user_id).all()
    accounts_data = []
    for account in accounts:
        accounts_data.append({
            'name': account.name,
            'balance': float(account.balance),
            'color': account.color if hasattr(account, 'color') else None,
            'created_at': account.created_at.isoformat() if account.created_at else None
        })
    
    # Get user categories
    categories = Category.query.filter_by(user_id=user_id).all()
    categories_data = []
    for category in categories:
        categories_data.append({
            'name': category.name,
            'type': category.type,
            'unicode_emoji': category.unicode_emoji if hasattr(category, 'unicode_emoji') else None
        })
    
    # Get user transactions
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    transactions_data = []
    for transaction in transactions:
        # Get account and category names for reference
        account = Account.query.get(transaction.account_id)
        category = Category.query.get(transaction.category_id)
        
        transactions_data.append({
            'amount': float(transaction.amount),
            'description': transaction.description,
            'account_name': account.name if account else None,
            'category_name': category.name if category else None,
            'date': transaction.date.isoformat() if transaction.date else None
        })
    
    backup_data = {
        'export_info': {
            'username': user.username,
            'email': user.email,
            'export_date': datetime.now().isoformat(),
            'version': '1.0'
        },
        'user_profile': {
            'name': user.name,
            'created_at': user.created_at.isoformat() if user.created_at else None
        },
        'accounts': accounts_data,
        'categories': categories_data,
        'transactions': transactions_data,
        'statistics': {
            'total_accounts': len(accounts_data),
            'total_categories': len(categories_data),
            'total_transactions': len(transactions_data)
        }
    }
    
    return backup_data

def validate_backup_data(data):
    """Validate backup data structure."""
    required_keys = ['export_info', 'accounts', 'categories', 'transactions']
    return all(key in data for key in required_keys)

def restore_user_data(user_id, backup_data):
    """Restore user data from backup."""
    try:
        restored_counts = {
            'accounts': 0,
            'categories': 0,
            'transactions': 0
        }
        
        # Create mapping for old to new IDs
        account_mapping = {}
        category_mapping = {}
        
        # Restore accounts
        for account_data in backup_data.get('accounts', []):
            # Check if account already exists
            existing_account = Account.query.filter_by(
                user_id=user_id, 
                name=account_data['name']
            ).first()
            
            if not existing_account:
                new_account = Account(
                    name=account_data['name'],
                    balance=account_data.get('balance', 0.0),
                    user_id=user_id
                )
                if 'color' in account_data and hasattr(new_account, 'color'):
                    new_account.color = account_data['color']
                
                db.session.add(new_account)
                db.session.flush()  # Get the ID
                account_mapping[account_data['name']] = new_account.id
                restored_counts['accounts'] += 1
            else:
                account_mapping[account_data['name']] = existing_account.id
        
        # Restore categories
        for category_data in backup_data.get('categories', []):
            # Check if category already exists
            existing_category = Category.query.filter_by(
                user_id=user_id,
                name=category_data['name'],
                type=category_data['type']
            ).first()
            
            if not existing_category:
                new_category = Category(
                    name=category_data['name'],
                    type=category_data['type'],
                    user_id=user_id
                )
                if 'unicode_emoji' in category_data and category_data['unicode_emoji']:
                    new_category.unicode_emoji = category_data['unicode_emoji']
                
                db.session.add(new_category)
                db.session.flush()  # Get the ID
                category_mapping[category_data['name']] = new_category.id
                restored_counts['categories'] += 1
            else:
                category_mapping[category_data['name']] = existing_category.id
        
        # Restore transactions
        for transaction_data in backup_data.get('transactions', []):
            account_id = account_mapping.get(transaction_data.get('account_name'))
            category_id = category_mapping.get(transaction_data.get('category_name'))
            
            if account_id and category_id:
                new_transaction = Transaction(
                    amount=transaction_data['amount'],
                    description=transaction_data['description'],
                    account_id=account_id,
                    category_id=category_id,
                    user_id=user_id
                )
                
                # Parse date if provided
                if transaction_data.get('date'):
                    try:
                        new_transaction.date = datetime.fromisoformat(transaction_data['date'].replace('Z', '+00:00'))
                    except:
                        pass  # Use default date
                
                db.session.add(new_transaction)
                restored_counts['transactions'] += 1
        
        # Update account balances based on transactions
        for account_name, account_id in account_mapping.items():
            account = Account.query.get(account_id)
            if account:
                # Calculate balance from transactions
                total_income = db.session.query(func.sum(Transaction.amount)).filter(
                    Transaction.account_id == account_id,
                    Transaction.amount > 0
                ).scalar() or 0
                
                total_expense = db.session.query(func.sum(Transaction.amount)).filter(
                    Transaction.account_id == account_id,
                    Transaction.amount < 0
                ).scalar() or 0
                
                account.balance = float(total_income + total_expense)
        
        db.session.commit()
        
        message = f"Restored {restored_counts['accounts']} accounts, {restored_counts['categories']} categories, {restored_counts['transactions']} transactions"
        return {'success': True, 'message': message}
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}

@profile_bp.route('/delete-all-data', methods=['POST'])
@api_login_required
def delete_all_data():
    """Delete all user data except user account."""
    try:
        data = request.get_json(force=True, silent=True)
        confirmation1 = data.get('confirmation1') if data else None
        confirmation2 = data.get('confirmation2') if data else None
        
        if confirmation1 != 'DELETE ALL DATA':
            return jsonify({'success': False, 'message': 'Invalid first confirmation'}), 400
            
        if confirmation2 != 'CONFIRM DELETE':
            return jsonify({'success': False, 'message': 'Invalid second confirmation'}), 400
        
        user_id = g.user.id
        
        # Delete all user data in the correct order (to respect foreign keys)
        # 1. Delete transactions first
        Transaction.query.filter_by(user_id=user_id).delete()
        
        # 2. Delete accounts (this will also delete any remaining account references)
        Account.query.filter_by(user_id=user_id).delete()
        
        # 3. Delete categories
        Category.query.filter_by(user_id=user_id).delete()
        
        # 4. Delete transfers if they exist
        try:
            from app.models import Transfer
            Transfer.query.filter_by(user_id=user_id).delete()
        except ImportError:
            pass  # Transfer model might not exist in all configurations
        
        # Commit the transaction
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'All your data has been permanently deleted. Your account remains active.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting data: {str(e)}'}), 500

@profile_bp.route('/delete-account', methods=['POST'])
@api_login_required
def delete_account():
    """Delete user account and all associated data."""
    try:
        data = request.get_json(force=True, silent=True)
        confirmation1 = data.get('confirmation1') if data else None
        confirmation2 = data.get('confirmation2') if data else None
        
        if confirmation1 != 'DELETE ACCOUNT':
            return jsonify({'success': False, 'message': 'Invalid first confirmation'}), 400
            
        if confirmation2 != 'PERMANENTLY DELETE':
            return jsonify({'success': False, 'message': 'Invalid second confirmation'}), 400
        
        user_id = g.user.id
        
        # Delete all user data in the correct order (to respect foreign keys)
        # 1. Delete transactions first
        Transaction.query.filter_by(user_id=user_id).delete()
        
        # 2. Delete accounts
        Account.query.filter_by(user_id=user_id).delete()
        
        # 3. Delete categories
        Category.query.filter_by(user_id=user_id).delete()
        
        # 4. Delete transfers if they exist
        try:
            from app.models import Transfer
            Transfer.query.filter_by(user_id=user_id).delete()
        except ImportError:
            pass  # Transfer model might not exist in all configurations
        
        # 5. Finally, delete the user account
        User.query.filter_by(id=user_id).delete()
        
        # Commit the transaction
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Your account has been permanently deleted. You will be logged out.',
            'logout': True
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting account: {str(e)}'}), 500

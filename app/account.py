"""
Account blueprint for managing user accounts and transfers.
Provides account CRUD operations, balance tracking, and transfer functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app.models import db, Account, Transaction, Category, Transfer
from app.auth import login_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
from flask_wtf.csrf import validate_csrf
from werkzeug.exceptions import BadRequest

# Configuration constants
TRANSFER_CATEGORY_NAME = 'Transfer'
DEFAULT_ACCOUNT_COLOR = '#FF6384'
MAX_TRANSFERS_PER_PAGE = 100

account_bp = Blueprint('account', __name__, url_prefix='/account')


@account_bp.route('/')
@login_required
def index():
    """Display all accounts for the current user."""
    accounts = Account.query.filter_by(user_id=g.user.id).order_by(Account.name.asc()).all()
    
    return render_template('dashboard/account.html', accounts=accounts)


def _create_initial_deposit_if_needed(account, balance):
    """
    Create an initial deposit transaction if account has positive balance.
    
    Args:
        account (Account): The account object
        balance (float): Initial balance amount
    """
    if balance <= 0:
        return
    
    # Create or find the "Initial Deposit" category
    initial_deposit_category = Category.query.filter_by(
        name='Initial Deposit',
        type='income',
        user_id=account.user_id
    ).first()
    
    if not initial_deposit_category:
        initial_deposit_category = Category(
            name='Initial Deposit',
            type='income',
            unicode_emoji='💰',
            user_id=account.user_id
        )
        db.session.add(initial_deposit_category)
        db.session.flush()
    
    # Create the initial deposit transaction
    initial_transaction = Transaction(
        amount=balance,
        description=f'Initial deposit for {account.name}',
        account_id=account.id,
        category_id=initial_deposit_category.id,
        user_id=account.user_id,
        date=datetime.now()
    )
    
    db.session.add(initial_transaction)


@account_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new account with optional initial balance."""
    if request.method == 'POST':
        name = request.form.get('name')
        balance = request.form.get('balance', 0.0)
        color = request.form.get('color', DEFAULT_ACCOUNT_COLOR)
        
        # Validation
        if not name:
            flash('Account name is required.', 'error')
            return redirect(url_for('account.index'))
        
        try:
            balance = float(balance) if balance else 0.0
        except ValueError:
            flash('Invalid balance amount.', 'error')
            return redirect(url_for('account.index'))
        
        try:
            # Create new account
            account = Account(
                name=name,
                balance=balance,
                color=color,
                user_id=g.user.id
            )
            
            db.session.add(account)
            db.session.flush()  # Get the account ID
            
            # Create initial deposit transaction if needed
            _create_initial_deposit_if_needed(account, balance)
            
            db.session.commit()
            flash(f'Account "{name}" created successfully!', 'success')
            
        except IntegrityError:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
        
        return redirect(url_for('account.index'))
    
    # For GET requests, redirect to main account page
    return redirect(url_for('account.index'))


def _create_balance_adjustment_transaction(account, original_balance, new_balance):
    """
    Create a balance adjustment transaction when account balance is manually changed.
    
    Args:
        account (Account): The account object
        original_balance (float): Original balance amount
        new_balance (float): New balance amount
    """
    balance_difference = new_balance - original_balance
    
    # Determine category name and type based on adjustment direction
    if balance_difference > 0:
        category_name = 'Balance Adjustment (Increase)'
        category_type = 'income'
        emoji = '📈'
    else:
        category_name = 'Balance Adjustment (Decrease)'
        category_type = 'expense'
        emoji = '📉'
    
    # Create or find the appropriate balance adjustment category
    adjustment_category = Category.query.filter_by(
        name=category_name,
        type=category_type,
        user_id=account.user_id
    ).first()
    
    if not adjustment_category:
        adjustment_category = Category(
            name=category_name,
            type=category_type,
            unicode_emoji=emoji,
            user_id=account.user_id
        )
        db.session.add(adjustment_category)
        db.session.flush()
    
    # Create the balance adjustment transaction
    adjustment_description = f'Manual balance adjustment: ${original_balance:.2f} → ${new_balance:.2f}'
    adjustment_transaction = Transaction(
        amount=abs(balance_difference),
        description=adjustment_description,
        account_id=account.id,
        category_id=adjustment_category.id,
        user_id=account.user_id,
        date=datetime.now()
    )
    
    db.session.add(adjustment_transaction)


@account_bp.route('/edit/<int:account_id>', methods=['GET', 'POST'])
@login_required
def edit(account_id):
    """Edit an existing account with balance adjustment tracking."""
    account = Account.query.filter_by(id=account_id, user_id=g.user.id).first()
    
    if not account:
        flash('Account not found.', 'error')
        return redirect(url_for('account.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        balance = request.form.get('balance')
        color = request.form.get('color', account.color or DEFAULT_ACCOUNT_COLOR)
        
        # Validation
        if not name:
            flash('Account name is required.', 'error')
            return redirect(url_for('account.index'))
        
        try:
            new_balance = float(balance) if balance else account.balance
        except ValueError:
            flash('Invalid balance amount.', 'error')
            return redirect(url_for('account.index'))
        
        # Store original balance for comparison
        original_balance = account.balance
        
        # Update account properties
        account.name = name
        account.color = color
        
        try:
            # Create balance adjustment transaction if balance changed
            if new_balance != original_balance:
                _create_balance_adjustment_transaction(account, original_balance, new_balance)
                flash('Balance adjustment transaction created.', 'info')
            
            # Update the account balance
            account.balance = new_balance
            
            db.session.commit()
            flash(f'Account "{name}" updated successfully!', 'success')
            
        except IntegrityError:
            db.session.rollback()
            flash('Error updating account. Please try again.', 'error')
        except Exception as e:
            db.session.rollback()
            flash('Error updating account. Please try again.', 'error')
        
        return redirect(url_for('account.index'))
    
    # For GET requests, return account data as JSON (for AJAX requests)
    if request.headers.get('Content-Type') == 'application/json':
        return jsonify({
            'id': account.id,
            'name': account.name,
            'balance': account.balance
        })
    
    # For regular GET requests, redirect to main page
    return redirect(url_for('account.index'))


@account_bp.route('/delete/<int:account_id>', methods=['POST'])
@login_required
def delete(account_id):
    """Delete an account."""
    account = Account.query.filter_by(id=account_id, user_id=g.user.id).first()
    
    if not account:
        flash('Account not found.', 'error')
        return redirect(url_for('account.index'))
    
    account_name = account.name
    
    try:
        db.session.delete(account)
        db.session.commit()
        flash(f'Account "{account_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cannot delete account "{account_name}". Accounts with existing transactions or transfers cannot be deleted.', 'error')
    
    return redirect(url_for('account.index'))


@account_bp.route('/api/accounts')
@login_required
def api_accounts():
    """API endpoint to get all accounts as JSON."""
    accounts = Account.query.filter_by(user_id=g.user.id).order_by(Account.name.asc()).all()
    
    accounts_data = []
    for account in accounts:
        accounts_data.append({
            'id': account.id,
            'name': account.name,
            'balance': account.balance,
            'created_at': account.created_at.isoformat()
        })
    
    return jsonify(accounts_data)


def _handle_request_response(is_ajax, message, status='success'):
    """
    Handle response for both AJAX and regular requests.
    
    Args:
        is_ajax (bool): Whether this is an AJAX request
        message (str): Message to display/return
        status (str): Response status ('success' or 'error')
        
    Returns:
        Response object
    """
    if is_ajax:
        status_code = 200 if status == 'success' else 400
        return jsonify({'status': status, 'message': message}), status_code
    else:
        flash(message, status)
        return redirect(url_for('account.index'))


def _validate_transfer_data(from_account_id, to_account_id, amount):
    """
    Validate transfer request data.
    
    Args:
        from_account_id (str): Source account ID
        to_account_id (str): Destination account ID
        amount (str): Transfer amount
        
    Returns:
        tuple: (is_valid, error_message, amount_float)
    """
    if not from_account_id or not to_account_id:
        return False, 'Source and destination accounts are required.', None
    
    if from_account_id == to_account_id:
        return False, 'Source and destination accounts must be different.', None
    
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return False, 'Transfer amount must be positive.', None
        return True, None, amount_float
    except (ValueError, TypeError):
        return False, 'Invalid transfer amount.', None


@account_bp.route('/transfer', methods=['POST'])
@login_required
def transfer():
    """Transfer money between accounts with comprehensive validation."""
    from_account_id = request.form.get('from_account')
    to_account_id = request.form.get('to_account')
    amount = request.form.get('amount')
    description = request.form.get('description', 'Transfer between accounts')
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    # Validate transfer data
    is_valid, error_message, amount_float = _validate_transfer_data(from_account_id, to_account_id, amount)
    if not is_valid:
        return _handle_request_response(is_ajax, error_message, 'error')
    
    # Get accounts and verify ownership
    from_account = Account.query.filter_by(id=from_account_id, user_id=g.user.id).first()
    to_account = Account.query.filter_by(id=to_account_id, user_id=g.user.id).first()
    
    if not from_account or not to_account:
        return _handle_request_response(is_ajax, 'Invalid accounts selected.', 'error')
    
    # Check sufficient balance
    if from_account.balance < amount_float:
        return _handle_request_response(is_ajax, 'Insufficient balance in source account.', 'error')
    
    try:
        # Create the Transfer record
        transfer_record = Transfer(
            amount=amount_float,
            description=description,
            from_account_id=from_account.id,
            to_account_id=to_account.id,
            user_id=g.user.id,
            date=datetime.now()
        )
        
        db.session.add(transfer_record)
        
        # Update account balances directly
        from_account.balance -= amount_float
        to_account.balance += amount_float
        
        db.session.commit()
        
        success_message = f'Successfully transferred {format_currency(amount_float)} from {from_account.name} to {to_account.name}!'
        return _handle_request_response(is_ajax, success_message, 'success')
        
    except Exception as e:
        db.session.rollback()
        return _handle_request_response(is_ajax, 'Error processing transfer. Please try again.', 'error')


@account_bp.route('/api/chart-data')
@login_required
def api_chart_data():
    """API endpoint to get account balance data for pie chart."""
    accounts = Account.query.filter_by(user_id=g.user.id).order_by(Account.name.asc()).all()
    
    chart_data = {
        'labels': [],
        'data': [],
        'backgroundColor': []
    }
    
    for account in accounts:
        if account.balance > 0:  # Only show accounts with positive balance
            chart_data['labels'].append(account.name)
            chart_data['data'].append(float(account.balance))
            chart_data['backgroundColor'].append(account.color or DEFAULT_ACCOUNT_COLOR)
    
    return jsonify(chart_data)


def _format_transfer_data(transfer):
    """
    Format transfer data for API response.
    
    Args:
        transfer (Transfer): Transfer object
        
    Returns:
        dict: Formatted transfer data or None if invalid
    """
    try:
        # Ensure accounts exist and belong to current user
        if (not transfer.from_account or not transfer.to_account or
            transfer.from_account.user_id != g.user.id or 
            transfer.to_account.user_id != g.user.id):
            return None
            
        return {
            'id': transfer.id,
            'description': transfer.description or f"From {transfer.from_account.name} to {transfer.to_account.name}",
            'amount': float(transfer.amount),
            'formatted_amount': format_currency(transfer.amount),
            'date': transfer.date.strftime('%Y-%m-%d'),
            'formatted_date': transfer.date.strftime('%b %d, %Y'),
            'from_account': transfer.from_account.name,
            'to_account': transfer.to_account.name,
            'type': 'transfer'
        }
    except (AttributeError, Exception) as e:
        # Log error but don't expose details to client
        print(f"Error formatting transfer {transfer.id}: {str(e)}")
        return None


@account_bp.route('/api/recent-transfers')
@login_required
def recent_transfers():
    """Get recent quick transfers between accounts."""
    try:
        # Get recent transfers with explicit joins
        transfers = db.session.query(Transfer)\
            .options(joinedload(Transfer.from_account))\
            .options(joinedload(Transfer.to_account))\
            .filter(Transfer.user_id == g.user.id)\
            .order_by(Transfer.date.desc(), Transfer.id.desc())\
            .limit(5).all()
        
        # Format transfers data, filtering out invalid ones
        transfers_data = [
            _format_transfer_data(transfer) 
            for transfer in transfers
        ]
        transfers_data = [t for t in transfers_data if t is not None]
        
        return jsonify({
            'status': 'success',
            'data': {
                'transfers': transfers_data,
                'count': len(transfers_data)
            }
        })
        
    except Exception as e:
        print(f"Error in recent_transfers endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error loading recent transfers'}), 500


@account_bp.route('/api/transfers')
@login_required
def api_transfers():
    """API endpoint to get all transfers with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), MAX_TRANSFERS_PER_PAGE)
    
    transfers_query = Transfer.query.filter_by(user_id=g.user.id)\
        .order_by(Transfer.date.desc(), Transfer.id.desc())
    
    transfers_paginated = transfers_query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Format transfers data using helper function
    transfers_data = []
    for transfer in transfers_paginated.items:
        formatted_data = _format_transfer_data(transfer)
        if formatted_data:
            # Add detailed account information for this endpoint
            formatted_data.update({
                'formatted_date': transfer.date.strftime('%b %d, %Y at %I:%M %p'),
                'from_account': {
                    'id': transfer.from_account.id,
                    'name': transfer.from_account.name
                },
                'to_account': {
                    'id': transfer.to_account.id,
                    'name': transfer.to_account.name
                }
            })
            transfers_data.append(formatted_data)
    
    return jsonify({
        'transfers': transfers_data,
        'pagination': {
            'page': transfers_paginated.page,
            'pages': transfers_paginated.pages,
            'per_page': transfers_paginated.per_page,
            'total': transfers_paginated.total,
            'has_next': transfers_paginated.has_next,
            'has_prev': transfers_paginated.has_prev
        }
    })


@account_bp.route('/api/transfer/<int:transfer_id>')
@login_required
def api_transfer_detail(transfer_id):
    """API endpoint to get detailed transfer information."""
    transfer = Transfer.query.filter_by(id=transfer_id, user_id=g.user.id).first()
    
    if not transfer:
        return jsonify({'error': 'Transfer not found'}), 404
    
    transfer_data = {
        'id': transfer.id,
        'amount': float(transfer.amount),
        'formatted_amount': format_currency(transfer.amount),
        'date': transfer.date.isoformat(),
        'formatted_date': transfer.date.strftime('%b %d, %Y at %I:%M %p'),
        'description': transfer.description,
        'from_account': {
            'id': transfer.from_account.id,
            'name': transfer.from_account.name,
            'balance': float(transfer.from_account.balance)
        },
        'to_account': {
            'id': transfer.to_account.id,
            'name': transfer.to_account.name,
            'balance': float(transfer.to_account.balance)
        },
        'transactions': {
            'from_transaction_id': transfer.from_transaction_id,
            'to_transaction_id': transfer.to_transaction_id
        }
    }
    
    return jsonify(transfer_data)


@account_bp.route('/transfer/<int:transfer_id>/reverse', methods=['POST'])
@login_required
def delete_transfer(transfer_id):
    """Reverse a transfer by restoring original account balances."""
    # Ensure this is an AJAX request
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return jsonify({'status': 'error', 'message': 'Invalid request method'}), 400
    
    # Validate CSRF token (skip in testing environment)
    from flask import current_app
    if current_app.config.get('WTF_CSRF_ENABLED', True):
        try:
            validate_csrf(request.form.get('csrf_token'))
        except BadRequest:
            return jsonify({'status': 'error', 'message': 'The CSRF token is missing.'}), 400
    
    transfer = Transfer.query.filter_by(id=transfer_id, user_id=g.user.id).first()
    
    if not transfer:
        return jsonify({'status': 'error', 'message': 'Transfer not found'}), 404
    
    try:
        # Get the accounts and transfer amount
        from_account = transfer.from_account
        to_account = transfer.to_account
        amount = transfer.amount
        
        # Validate that accounts still exist and belong to user
        if not from_account or not to_account:
            return jsonify({'status': 'error', 'message': 'Associated accounts not found'}), 400
        
        if from_account.user_id != g.user.id or to_account.user_id != g.user.id:
            return jsonify({'status': 'error', 'message': 'Unauthorized access to accounts'}), 403
        
        # Reverse the transfer by updating account balances
        from_account.balance += amount  # Restore to source
        to_account.balance -= amount    # Remove from destination
        
        # Delete associated transactions if they exist
        for transaction_id in [transfer.from_transaction_id, transfer.to_transaction_id]:
            if transaction_id:
                transaction = Transaction.query.get(transaction_id)
                if transaction:
                    db.session.delete(transaction)
        
        # Delete the transfer record
        db.session.delete(transfer)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': f'Transfer of {format_currency(amount)} has been reversed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error reversing transfer {transfer_id}: {str(e)}")  # Log for debugging
        return jsonify({
            'status': 'error', 
            'message': 'Error reversing transfer. Please try again.'
        }), 500


def _get_month_boundaries():
    """Get current month start and end dates."""
    current_month = datetime.now().replace(day=1)
    next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    return current_month, next_month


@account_bp.route('/api/transfer-summary')
@login_required
def api_transfer_summary():
    """API endpoint to get transfer summary statistics."""
    # Get transfer statistics
    total_transfers = Transfer.query.filter_by(user_id=g.user.id).count()
    
    # Get total amount transferred
    total_amount = db.session.query(func.sum(Transfer.amount))\
        .filter(Transfer.user_id == g.user.id).scalar() or 0.0
    
    # Get monthly statistics
    current_month, next_month = _get_month_boundaries()
    
    monthly_transfers = Transfer.query.filter(
        Transfer.user_id == g.user.id,
        Transfer.date >= current_month,
        Transfer.date < next_month
    ).count()
    
    monthly_amount = db.session.query(func.sum(Transfer.amount))\
        .filter(
            Transfer.user_id == g.user.id,
            Transfer.date >= current_month,
            Transfer.date < next_month
        ).scalar() or 0.0
    
    # Get most used account pairs
    account_pairs = db.session.query(
        Transfer.from_account_id,
        Transfer.to_account_id,
        func.count(Transfer.id).label('count'),
        func.sum(Transfer.amount).label('total_amount')
    ).filter(Transfer.user_id == g.user.id)\
     .group_by(Transfer.from_account_id, Transfer.to_account_id)\
     .order_by(func.count(Transfer.id).desc())\
     .limit(5).all()
    
    popular_pairs = []
    for pair in account_pairs:
        from_account = Account.query.get(pair.from_account_id)
        to_account = Account.query.get(pair.to_account_id)
        if from_account and to_account:  # Ensure accounts exist
            popular_pairs.append({
                'from_account': from_account.name,
                'to_account': to_account.name,
                'count': pair.count,
                'total_amount': float(pair.total_amount),
                'formatted_amount': format_currency(pair.total_amount)
            })
    
    return jsonify({
        'total_transfers': total_transfers,
        'total_amount': float(total_amount),
        'formatted_total_amount': format_currency(total_amount),
        'monthly_transfers': monthly_transfers,
        'monthly_amount': float(monthly_amount),
        'formatted_monthly_amount': format_currency(monthly_amount),
        'popular_pairs': popular_pairs
    })
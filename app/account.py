from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app.models import db, Account, Transaction, Category, Transfer
from app.auth import login_required
from app.utils import format_currency
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

account_bp = Blueprint('account', __name__, url_prefix='/account')


@account_bp.route('/')
@login_required
def index():
    """Display all accounts for the current user."""
    accounts = Account.query.filter_by(user_id=g.user.id).order_by(Account.name.asc()).all()
    
    # Calculate summary statistics
    total_balance = sum(account.balance for account in accounts)
    
    # Calculate this month's income and expenses from transactions
    current_month = datetime.now().replace(day=1)
    next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    
    # Get transactions for current month with proper joins
    monthly_transactions = db.session.query(Transaction).join(Account).join(Category).filter(
        Account.user_id == g.user.id,
        Transaction.date >= current_month,
        Transaction.date < next_month
    ).all()
    
    monthly_income = 0.0
    monthly_expenses = 0.0
    
    for transaction in monthly_transactions:
        if transaction.category and transaction.category.type == 'income':
            monthly_income += transaction.amount
        elif transaction.category and transaction.category.type == 'expense':
            monthly_expenses += transaction.amount
    
    net_worth = total_balance
    
    return render_template('dashboard/account.html', 
                         accounts=accounts,
                         total_balance=total_balance,
                         monthly_income=monthly_income,
                         monthly_expenses=monthly_expenses,
                         net_worth=net_worth)


@account_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new account."""
    if request.method == 'POST':
        name = request.form.get('name')
        balance = request.form.get('balance', 0.0)
        color = request.form.get('color', '#FF6384')
        
        # Validation
        if not name:
            flash('Account name is required.', 'error')
            return redirect(url_for('account.index'))
        
        try:
            balance = float(balance) if balance else 0.0
        except ValueError:
            flash('Invalid balance amount.', 'error')
            return redirect(url_for('account.index'))
        
        # Create new account
        account = Account(
            name=name,
            balance=balance,
            color=color,
            user_id=g.user.id
        )
        
        try:
            db.session.add(account)
            db.session.commit()
            flash(f'Account "{name}" created successfully!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
        
        return redirect(url_for('account.index'))
    
    # For GET requests, redirect to main account page
    return redirect(url_for('account.index'))


@account_bp.route('/edit/<int:account_id>', methods=['GET', 'POST'])
@login_required
def edit(account_id):
    """Edit an existing account."""
    account = Account.query.filter_by(id=account_id, user_id=g.user.id).first()
    
    if not account:
        flash('Account not found.', 'error')
        return redirect(url_for('account.index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        balance = request.form.get('balance')
        color = request.form.get('color', account.color or '#FF6384')
        
        # Validation
        if not name:
            flash('Account name is required.', 'error')
            return redirect(url_for('account.index'))
        
        try:
            balance = float(balance) if balance else account.balance
        except ValueError:
            flash('Invalid balance amount.', 'error')
            return redirect(url_for('account.index'))
        
        # Update account
        account.name = name
        account.balance = balance
        account.color = color
        
        try:
            db.session.commit()
            flash(f'Account "{name}" updated successfully!', 'success')
        except IntegrityError:
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
        flash('Error deleting account. Please try again.', 'error')
    
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


@account_bp.route('/transfer', methods=['POST'])
@login_required
def transfer():
    """Transfer money between accounts."""
    from_account_id = request.form.get('from_account')
    to_account_id = request.form.get('to_account')
    amount = request.form.get('amount')
    description = request.form.get('description', 'Transfer between accounts')
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    def handle_error(message):
        if is_ajax:
            return jsonify({'status': 'error', 'message': message}), 400
        else:
            flash(message, 'error')
            return redirect(url_for('account.index'))
    
    def handle_success(message):
        if is_ajax:
            return jsonify({'status': 'success', 'message': message})
        else:
            flash(message, 'success')
            return redirect(url_for('account.index'))
    
    # Validation
    if not from_account_id or not to_account_id:
        return handle_error('Source and destination accounts are required.')
    
    if from_account_id == to_account_id:
        return handle_error('Source and destination accounts must be different.')
    
    try:
        amount = float(amount)
        if amount <= 0:
            return handle_error('Transfer amount must be positive.')
    except (ValueError, TypeError):
        return handle_error('Invalid transfer amount.')
    
    # Get accounts and verify ownership
    from_account = Account.query.filter_by(id=from_account_id, user_id=g.user.id).first()
    to_account = Account.query.filter_by(id=to_account_id, user_id=g.user.id).first()
    
    if not from_account or not to_account:
        return handle_error('Invalid accounts selected.')
    
    # Check sufficient balance
    if from_account.balance < amount:
        return handle_error('Insufficient balance in source account.')
    
    try:
        # Create transfer categories if they don't exist
        transfer_expense_category = Category.query.filter_by(
            name='Transfer', 
            type='expense', 
            user_id=g.user.id
        ).first()
        
        if not transfer_expense_category:
            transfer_expense_category = Category(
                name='Transfer',
                type='expense',
                unicode_emoji='🔄',
                user_id=g.user.id
            )
            db.session.add(transfer_expense_category)
            db.session.flush()  # Get the ID
        
        transfer_income_category = Category.query.filter_by(
            name='Transfer', 
            type='income', 
            user_id=g.user.id
        ).first()
        
        if not transfer_income_category:
            transfer_income_category = Category(
                name='Transfer',
                type='income',
                unicode_emoji='🔄',
                user_id=g.user.id
            )
            db.session.add(transfer_income_category)
            db.session.flush()  # Get the ID
        
        # Create transaction records for tracking
        # Outgoing transaction (expense from source account)
        out_transaction = Transaction(
            amount=amount,
            description=f"Transfer - from {from_account.name} to {to_account.name}",
            account_id=from_account.id,
            category_id=transfer_expense_category.id,
            user_id=g.user.id,
            date=datetime.now()
        )
        
        # Incoming transaction (income to destination account)
        in_transaction = Transaction(
            amount=amount,
            description=f"Transfer - from {from_account.name} to {to_account.name}",
            account_id=to_account.id,
            category_id=transfer_income_category.id,
            user_id=g.user.id,
            date=datetime.now()
        )
        
        db.session.add(out_transaction)
        db.session.add(in_transaction)
        db.session.flush()  # Get transaction IDs
        
        # Create the Transfer record
        transfer_record = Transfer(
            amount=amount,
            description=description,
            from_account_id=from_account.id,
            to_account_id=to_account.id,
            user_id=g.user.id,
            from_transaction_id=out_transaction.id,
            to_transaction_id=in_transaction.id
        )
        
        db.session.add(transfer_record)
        
        # Update account balances
        from_account.balance -= amount
        to_account.balance += amount
        
        db.session.commit()
        
        success_message = f'Successfully transferred {format_currency(amount)} from {from_account.name} to {to_account.name}!'
        return handle_success(success_message)
        
    except Exception as e:
        db.session.rollback()
        return handle_error('Error processing transfer. Please try again.')


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
            chart_data['backgroundColor'].append(account.color or '#FF6384')
    
    return jsonify(chart_data)


@account_bp.route('/api/summary')
@login_required
def api_summary():
    """API endpoint to get account summary as JSON."""
    accounts = Account.query.filter_by(user_id=g.user.id).all()
    
    total_balance = sum(account.balance for account in accounts)
    
    # Calculate this month's income and expenses from transactions
    current_month = datetime.now().replace(day=1)
    next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    
    # Get transactions for current month with proper joins
    monthly_transactions = db.session.query(Transaction).join(Account).join(Category).filter(
        Account.user_id == g.user.id,
        Transaction.date >= current_month,
        Transaction.date < next_month
    ).all()
    
    monthly_income = 0.0
    monthly_expenses = 0.0
    
    for transaction in monthly_transactions:
        if transaction.category and transaction.category.type == 'income':
            monthly_income += transaction.amount
        elif transaction.category and transaction.category.type == 'expense':
            monthly_expenses += transaction.amount
    
    net_worth = total_balance
    
    return jsonify({
        'total_balance': total_balance,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'net_worth': net_worth,
        'account_count': len(accounts)
    })


@account_bp.route('/api/recent-transfers')
@login_required
def recent_transfers():
    """Get recent quick transfers between accounts."""
    try:
        # Check if user is properly authenticated
        if not g.user or not g.user.id:
            return jsonify({'status': 'error', 'message': 'User not authenticated'}), 401
        
        # Get recent transfers with explicit joins to avoid lazy loading issues
        transfers = db.session.query(Transfer)\
            .options(joinedload(Transfer.from_account))\
            .options(joinedload(Transfer.to_account))\
            .filter(Transfer.user_id == g.user.id)\
            .order_by(Transfer.date.desc(), Transfer.id.desc())\
            .limit(5).all()
        
        if not transfers:
            return jsonify({
                'status': 'success',
                'data': {
                    'transfers': [],
                    'count': 0
                }
            })
        
        # Format transfers data
        transfers_data = []
        
        for transfer in transfers:
            try:
                # Ensure accounts exist and are accessible
                if not transfer.from_account or not transfer.to_account:
                    print(f"Transfer {transfer.id} missing account relationships")
                    continue
                
                # Check that accounts belong to the current user
                if (transfer.from_account.user_id != g.user.id or 
                    transfer.to_account.user_id != g.user.id):
                    print(f"Transfer {transfer.id} has accounts belonging to different user")
                    continue
                    
                transfers_data.append({
                    'id': transfer.id,
                    'description': transfer.description or f"From {transfer.from_account.name} to {transfer.to_account.name}",
                    'amount': float(transfer.amount),
                    'formatted_amount': format_currency(transfer.amount),
                    'date': transfer.date.strftime('%Y-%m-%d'),
                    'formatted_date': transfer.date.strftime('%b %d, %Y'),
                    'from_account': transfer.from_account.name,
                    'to_account': transfer.to_account.name,
                    'type': 'transfer'
                })
            except AttributeError as attr_error:
                # Skip transfers with missing account relationships
                print(f"Skipping transfer {transfer.id} due to missing account: {str(attr_error)}")
                continue
            except Exception as transfer_error:
                print(f"Error processing transfer {transfer.id}: {str(transfer_error)}")
                continue
        
        return jsonify({
            'status': 'success',
            'data': {
                'transfers': transfers_data,
                'count': len(transfers_data)
            }
        })
        
    except Exception as e:
        print(f"Error in recent_transfers endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': 'Error loading recent transfers'}), 500


@account_bp.route('/api/transfers')
@login_required
def api_transfers():
    """API endpoint to get all transfers with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)
    
    transfers_query = Transfer.query.filter_by(user_id=g.user.id)\
        .order_by(Transfer.date.desc(), Transfer.id.desc())
    
    transfers_paginated = transfers_query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    transfers_data = []
    for transfer in transfers_paginated.items:
        transfers_data.append({
            'id': transfer.id,
            'amount': float(transfer.amount),
            'formatted_amount': format_currency(transfer.amount),
            'date': transfer.date.isoformat(),
            'formatted_date': transfer.date.strftime('%b %d, %Y at %I:%M %p'),
            'description': transfer.description or f"Transfer from {transfer.from_account.name} to {transfer.to_account.name}",
            'from_account': {
                'id': transfer.from_account.id,
                'name': transfer.from_account.name
            },
            'to_account': {
                'id': transfer.to_account.id,
                'name': transfer.to_account.name
            }
        })
    
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
    """API endpoint to get transfer details."""
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
    """Delete a transfer and reverse the transaction."""
    transfer = Transfer.query.filter_by(id=transfer_id, user_id=g.user.id).first()
    
    if not transfer:
        return jsonify({'status': 'error', 'message': 'Transfer not found'}), 404
    
    try:
        # Get the accounts
        from_account = transfer.from_account
        to_account = transfer.to_account
        amount = transfer.amount
        
        # Reverse the transfer by updating account balances
        from_account.balance += amount  # Add back to source
        to_account.balance -= amount    # Remove from destination
        
        # Delete associated transactions if they exist
        if transfer.from_transaction_id:
            from_transaction = Transaction.query.get(transfer.from_transaction_id)
            if from_transaction:
                db.session.delete(from_transaction)
        
        if transfer.to_transaction_id:
            to_transaction = Transaction.query.get(transfer.to_transaction_id)
            if to_transaction:
                db.session.delete(to_transaction)
        
        # Delete the transfer record
        db.session.delete(transfer)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': f'Transfer of {format_currency(amount)} has been reversed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error', 
            'message': f'Error reversing transfer: {str(e)}'
        }), 500


@account_bp.route('/api/transfer-summary')
@login_required
def api_transfer_summary():
    """API endpoint to get transfer summary statistics."""
    from sqlalchemy import func
    
    # Get transfer statistics
    total_transfers = Transfer.query.filter_by(user_id=g.user.id).count()
    
    # Get total amount transferred
    total_amount = db.session.query(func.sum(Transfer.amount))\
        .filter(Transfer.user_id == g.user.id).scalar() or 0.0
    
    # Get transfers this month
    current_month = datetime.now().replace(day=1)
    next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    
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
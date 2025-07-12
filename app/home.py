"""
Home blueprint for the dashboard functionality.
Provides overview statistics, recent transactions, and quick actions.
"""

import calendar
from datetime import datetime, timedelta

from flask import Blueprint, render_template, jsonify, request, current_app, g
from sqlalchemy import func, and_

from app.models import Transaction, Category, db
from app.auth import login_required

home = Blueprint('home', __name__, url_prefix='/home')

# Constants for better maintainability
TRANSFER_CATEGORY_NAME = 'Transfer'
DEFAULT_STATS_DAYS = 30
MAX_TRANSACTION_LIMIT = 50

def format_currency(amount):
    """Format a currency amount with proper formatting."""
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"

def _get_transaction_filter(user_id, transaction_type, start_date=None, exclude_transfers=True):
    """
    Build common transaction filter for database queries.
    
    Args:
        user_id (int): User ID
        transaction_type (str): 'income' or 'expense'
        start_date (datetime, optional): Filter by date from this start date
        exclude_transfers (bool): Whether to exclude transfer transactions
        
    Returns:
        SQLAlchemy filter conditions
    """
    conditions = [
        Transaction.user_id == user_id,
        Transaction.category.has(Category.type == transaction_type)
    ]
    
    if exclude_transfers:
        conditions.append(Transaction.category.has(Category.name != TRANSFER_CATEGORY_NAME))
    
    if start_date:
        conditions.append(Transaction.date >= start_date)
    
    return and_(*conditions)

def _calculate_totals(user_id, start_date=None):
    """
    Calculate total income, expenses, and balance for a user.
    
    Args:
        user_id (int): User ID
        start_date (datetime, optional): Filter by date from this start date
        
    Returns:
        tuple: (total_income, total_expenses, total_balance)
    """
    # Calculate total income
    total_income = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        _get_transaction_filter(user_id, 'income', start_date)
    ).scalar()
    
    # Calculate total expenses
    total_expenses = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        _get_transaction_filter(user_id, 'expense', start_date)
    ).scalar()
    
    return float(total_income), float(total_expenses), float(total_income - total_expenses)

def _get_month_boundaries(year, month):
    """
    Get start and end datetime for a given month.
    
    Args:
        year (int): Year
        month (int): Month (1-12)
        
    Returns:
        tuple: (month_start, month_end)
    """
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(year, month + 1, 1) - timedelta(days=1)
    
    return month_start, month_end


@home.route('/')
@login_required
def dashboard():
    """Main dashboard view with overview statistics."""
    now = datetime.now()
    current_month_start = datetime(now.year, now.month, 1)
    
    # Calculate total balance (all time)
    total_income, total_expenses, total_balance = _calculate_totals(g.user.id)
    
    # Calculate current month statistics
    month_income, month_expenses, month_net = _calculate_totals(g.user.id, current_month_start)
    
    return render_template('dashboard/home.html', 
                         title='Dashboard',
                         total_balance=total_balance,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         month_income=month_income,
                         month_expenses=month_expenses,
                         month_net=month_net,
                         current_month=calendar.month_name[now.month])


@home.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics."""
    try:
        # Get date range from query parameters
        days = request.args.get('days', DEFAULT_STATS_DAYS, type=int)
        start_date = datetime.now() - timedelta(days=days) if days > 0 else None
        
        # Calculate total statistics (all time)
        total_income, total_expenses, total_balance = _calculate_totals(g.user.id)
        
        # Calculate period statistics
        period_income, period_expenses, period_net = _calculate_totals(g.user.id, start_date)
        
        # Get transaction count for the period
        count_query = db.session.query(func.count(Transaction.id)).filter(
            Transaction.user_id == g.user.id
        )
        if start_date:
            count_query = count_query.filter(Transaction.date >= start_date)
        transaction_count = count_query.scalar()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_balance': total_balance,
                'period_income': period_income,
                'period_expenses': period_expenses,
                'period_net': period_net,
                'transaction_count': transaction_count,
                'period_days': days
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching dashboard stats: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch dashboard statistics'
        }), 500


@home.route('/api/recent-transactions')
@login_required
def api_recent_transactions():
    """API endpoint for recent transactions. Used for transaction history displays."""
    try:
        limit = min(request.args.get('limit', 10, type=int), MAX_TRANSACTION_LIMIT)
        
        transactions = Transaction.query.filter(
            Transaction.user_id == g.user.id
        ).order_by(
            Transaction.date.desc(), 
            Transaction.id.desc()
        ).limit(limit).all()
        
        return jsonify({
            'status': 'success',
            'data': [{
                'id': t.id,
                'amount': float(t.amount),
                'description': t.description,
                'category': t.category.name if t.category else 'Uncategorized',
                'transaction_type': t.category.type if t.category else 'expense',
                'date': t.date.isoformat(),
                'formatted_date': t.date.strftime('%Y-%m-%d'),
                'formatted_amount': format_currency(t.amount)
            } for t in transactions]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching recent transactions: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch recent transactions'
        }), 500


@home.route('/api/category-breakdown')
@login_required
def api_category_breakdown():
    """API endpoint for category spending breakdown."""
    try:
        # Get query parameters
        days = request.args.get('days', DEFAULT_STATS_DAYS, type=int)
        transaction_type = request.args.get('type', 'expense')
        start_date = datetime.now() - timedelta(days=days) if days > 0 else None
        
        # Validate transaction type
        if transaction_type not in ['income', 'expense']:
            transaction_type = 'expense'
        
        # Build query for category breakdown
        query = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            _get_transaction_filter(g.user.id, transaction_type, start_date)
        ).group_by(Category.id, Category.name).order_by(
            func.sum(Transaction.amount).desc()
        )
        
        categories = query.all()
        
        # Calculate total for percentage calculation
        total_amount = sum(float(cat.total) for cat in categories)
        
        return jsonify({
            'status': 'success',
            'data': {
                'categories': [{
                    'name': cat.name,
                    'amount': float(cat.total),
                    'percentage': round((float(cat.total) / total_amount * 100), 2) if total_amount > 0 else 0,
                    'formatted_amount': format_currency(cat.total)
                } for cat in categories],
                'total_amount': total_amount,
                'period_days': days,
                'transaction_type': transaction_type
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching category breakdown: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch category breakdown'
        }), 500


@home.route('/api/monthly-trend')
@login_required
def api_monthly_trend():
    """API endpoint for monthly income/expense trend data."""
    try:
        months = []
        current_date = datetime.now()
        
        for i in range(12):
            # Calculate month and year
            if current_date.month - i <= 0:
                month = current_date.month - i + 12
                year = current_date.year - 1
            else:
                month = current_date.month - i
                year = current_date.year
            
            # Get month boundaries
            month_start, month_end = _get_month_boundaries(year, month)
            
            # Calculate monthly statistics with proper date filtering
            month_income = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                _get_transaction_filter(g.user.id, 'income'),
                Transaction.date >= month_start,
                Transaction.date <= month_end
            ).scalar()
            
            month_expenses = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                _get_transaction_filter(g.user.id, 'expense'),
                Transaction.date >= month_start,
                Transaction.date <= month_end
            ).scalar()
            
            months.append({
                'month': calendar.month_name[month],
                'year': year,
                'income': float(month_income),
                'expenses': float(month_expenses),
                'net': float(month_income - month_expenses),
                'month_num': month
            })
        
        # Reverse to get chronological order
        months.reverse()
        
        return jsonify({
            'status': 'success',
            'data': months
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching monthly trend: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch monthly trend data'
        }), 500


@home.route('/api/daily-activity')
@login_required
def api_daily_activity():
    """API endpoint for daily activity chart data for the current month."""
    try:
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        
        # Calculate last day of current month
        month_start, current_month_end = _get_month_boundaries(now.year, now.month)
        
        days_data = []
        current_date = current_month_start
        
        while current_date <= current_month_end:
            day_start = current_date
            day_end = current_date.replace(hour=23, minute=59, second=59)
            
            # Calculate daily income
            daily_income = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                _get_transaction_filter(g.user.id, 'income'),
                Transaction.date >= day_start,
                Transaction.date <= day_end
            ).scalar()
            
            # Calculate daily expenses
            daily_expenses = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                _get_transaction_filter(g.user.id, 'expense'),
                Transaction.date >= day_start,
                Transaction.date <= day_end
            ).scalar()
            
            days_data.append({
                'day': current_date.day,
                'date': current_date.strftime('%Y-%m-%d'),
                'income': float(daily_income),
                'expenses': float(daily_expenses),
                'net': float(daily_income - daily_expenses)
            })
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'status': 'success',
            'data': days_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching daily activity: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch daily activity data'
        }), 500

@home.route('/api/weekly-expenses')
@login_required
def api_weekly_expenses():
    """API endpoint for weekly expenses breakdown."""
    try:
        now = datetime.now()
        # Get the start of the week (Monday)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        weekly_data = []
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        for i in range(7):  # Monday to Sunday
            day_date = start_of_week + timedelta(days=i)
            day_end = day_date.replace(hour=23, minute=59, second=59)
            
            # Get expenses for this day
            daily_expenses = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                _get_transaction_filter(g.user.id, 'expense'),
                Transaction.date >= day_date,
                Transaction.date <= day_end
            ).scalar()
            
            weekly_data.append({
                'day': day_date.strftime('%Y-%m-%d'),
                'day_name': day_names[i],
                'expenses': float(daily_expenses)
            })
        
        return jsonify({
            'status': 'success',
            'data': weekly_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching weekly expenses: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch weekly expenses data'
        }), 500

@home.route('/api/daily-expenses')
@login_required
def api_daily_expenses():
    """API endpoint for daily expenses breakdown of current month."""
    try:
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        
        # Calculate last day of current month
        month_start, current_month_end = _get_month_boundaries(now.year, now.month)
        
        daily_data = []
        current_date = current_month_start
        
        while current_date <= current_month_end:
            day_start = current_date
            day_end = current_date.replace(hour=23, minute=59, second=59)
            
            # Calculate daily expenses
            daily_expenses = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                _get_transaction_filter(g.user.id, 'expense'),
                Transaction.date >= day_start,
                Transaction.date <= day_end
            ).scalar()
            
            daily_data.append({
                'day': current_date.day,
                'day_name': f"Day {current_date.day}",
                'date': current_date.strftime('%Y-%m-%d'),
                'expenses': float(daily_expenses)
            })
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'status': 'success',
            'data': daily_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching daily expenses: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch daily expenses data'
        }), 500


@home.route('/api/monthly-expenses')
@login_required
def api_monthly_expenses():
    """API endpoint for monthly expenses breakdown of current year."""
    try:
        now = datetime.now()
        monthly_data = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Get all months of current year
        for month_num in range(1, 13):
            # Get month boundaries
            month_start, month_end = _get_month_boundaries(now.year, month_num)
            
            # Get expenses for this month
            monthly_expenses = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                _get_transaction_filter(g.user.id, 'expense'),
                Transaction.date >= month_start,
                Transaction.date <= month_end
            ).scalar()
            
            monthly_data.append({
                'month': f"{month_names[month_num-1]} {now.year}",
                'month_name': month_names[month_num-1],
                'year': now.year,
                'expenses': float(monthly_expenses)
            })
        
        return jsonify({
            'status': 'success',
            'data': monthly_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching monthly expenses: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch monthly expenses data'
        }), 500



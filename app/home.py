"""
Home blueprint for the dashboard functionality.
Provides overview statistics, recent transactions, and quick actions.
"""

from flask import Blueprint, render_template, jsonify, request, current_app, g
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from app.models import Transaction, Category, db
from app.auth import login_required
from app.utils import format_currency
import calendar

home = Blueprint('home', __name__, url_prefix='/home')


@home.route('/')
@login_required
def dashboard():
    """Main dashboard view with overview statistics and recent transactions."""
    # Get current date information
    now = datetime.now()
    current_month_start = datetime(now.year, now.month, 1)
    
    # Calculate total balance
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == g.user.id,
        Transaction.category.has(Category.type == 'income')
    ).scalar() or 0
    
    total_expenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == g.user.id,
        Transaction.category.has(Category.type == 'expense')
    ).scalar() or 0
    
    total_balance = total_income - total_expenses
    
    # Calculate current month income and expenses
    month_income = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        and_(
            Transaction.user_id == g.user.id,
            Transaction.category.has(Category.type == 'income'),
            Transaction.date >= current_month_start
        )
    ).scalar()
    
    month_expenses = db.session.query(
        func.coalesce(func.sum(Transaction.amount), 0)
    ).filter(
        and_(
            Transaction.user_id == g.user.id,
            Transaction.category.has(Category.type == 'expense'),
            Transaction.date >= current_month_start
        )
    ).scalar()
    
    # Get recent transactions (last 10)
    recent_transactions = Transaction.query.filter(
        Transaction.user_id == g.user.id
    ).order_by(Transaction.date.desc(), Transaction.id.desc()).limit(10).all()
    
    # Get top categories this month
    top_categories = db.session.query(
        Category.name,
        Category.type,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        and_(
            Transaction.user_id == g.user.id,
            Transaction.date >= current_month_start
        )
    ).group_by(Category.id, Category.name, Category.type).order_by(
        func.sum(Transaction.amount).desc()
    ).limit(5).all()
    
    return render_template('dashboard/home.html', 
                         title='Dashboard',
                         total_balance=total_balance,
                         month_income=month_income,
                         month_expenses=month_expenses,
                         month_net=month_income - month_expenses,
                         recent_transactions=recent_transactions,
                         top_categories=top_categories,
                         current_month=calendar.month_name[now.month])


@home.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics."""
    try:
        # Get date range from query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # Calculate statistics
        total_income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == g.user.id,
            Transaction.category.has(Category.type == 'income')
        ).scalar() or 0
        
        total_expenses = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == g.user.id,
            Transaction.category.has(Category.type == 'expense')
        ).scalar() or 0
        
        total_balance = total_income - total_expenses
        
        period_income = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            and_(
                Transaction.user_id == g.user.id,
                Transaction.category.has(Category.type == 'income'),
                Transaction.date >= start_date
            )
        ).scalar()
        
        period_expenses = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            and_(
                Transaction.user_id == g.user.id,
                Transaction.category.has(Category.type == 'expense'),
                Transaction.date >= start_date
            )
        ).scalar()
        
        transaction_count = db.session.query(func.count(Transaction.id)).filter(
            and_(
                Transaction.user_id == g.user.id,
                Transaction.date >= start_date
            )
        ).scalar()
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_balance': float(total_balance),
                'period_income': float(period_income),
                'period_expenses': float(period_expenses),
                'period_net': float(period_income - period_expenses),
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
    """API endpoint for recent transactions."""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # Cap at 50 transactions
        
        transactions = Transaction.query.filter(
            Transaction.user_id == g.user.id
        ).order_by(Transaction.date.desc(), Transaction.id.desc()).limit(limit).all()
        
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
        # Get date range from query parameters
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        transaction_type = request.args.get('type', 'expense')  # 'income' or 'expense'
        
        # Get category breakdown
        categories = db.session.query(
            Category.name,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            and_(
                Transaction.user_id == g.user.id,
                Category.type == transaction_type,
                Transaction.date >= start_date
            )
        ).group_by(Category.id, Category.name).order_by(
            func.sum(Transaction.amount).desc()
        ).all()
        
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
    """API endpoint for monthly income/expense trend."""
    try:
        # Get last 12 months of data
        months = []
        current_date = datetime.now()
        
        for i in range(12):
            # Calculate month start and end
            if current_date.month - i <= 0:
                month = current_date.month - i + 12
                year = current_date.year - 1
            else:
                month = current_date.month - i
                year = current_date.year
            
            month_start = datetime(year, month, 1)
            if month == 12:
                month_end = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Get income and expenses for this month
            month_income = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                and_(
                    Transaction.user_id == g.user.id,
                    Transaction.category.has(Category.type == 'income'),
                    Transaction.date >= month_start,
                    Transaction.date <= month_end
                )
            ).scalar()
            
            month_expenses = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                and_(
                    Transaction.user_id == g.user.id,
                    Transaction.category.has(Category.type == 'expense'),
                    Transaction.date >= month_start,
                    Transaction.date <= month_end
                )
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
        # Get current month
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        
        # Calculate last day of current month
        if now.month == 12:
            next_month_start = datetime(now.year + 1, 1, 1)
        else:
            next_month_start = datetime(now.year, now.month + 1, 1)
        current_month_end = next_month_start - timedelta(days=1)
        
        # Get all days in the current month
        days_data = []
        current_date = current_month_start
        
        while current_date <= current_month_end:
            day_start = current_date
            day_end = current_date.replace(hour=23, minute=59, second=59)
            
            # Calculate daily income
            daily_income = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                and_(
                    Transaction.user_id == g.user.id,
                    Transaction.category.has(Category.type == 'income'),
                    Transaction.date >= day_start,
                    Transaction.date <= day_end
                )
            ).scalar()
            
            # Calculate daily expenses
            daily_expenses = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0)
            ).filter(
                and_(
                    Transaction.user_id == g.user.id,
                    Transaction.category.has(Category.type == 'expense'),
                    Transaction.date >= day_start,
                    Transaction.date <= day_end
                )
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

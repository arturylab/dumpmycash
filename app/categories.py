"""
Category management module for DumpMyCash.

This module handles all category-related operations including:
- Creating, reading, updating, and deleting categories
- Category filtering and statistics
- Time-based analysis
- Top expense categories reporting

All categories are properly isolated by user and support both income and expense types.
"""

from flask import Blueprint, render_template, request, jsonify, g
from app.auth import login_required, api_login_required
from app import db
from app.models import Category, Transaction
from sqlalchemy import func, or_, and_
from datetime import datetime, timedelta

# Initialize category blueprint
category_bp = Blueprint('categories', __name__, url_prefix='/categories')

# Configuration constants
DEFAULT_TIME_FILTER = 'month'
TOP_CATEGORIES_LIMIT = 10
DEFAULT_EMOJI_INCOME = '💰'
DEFAULT_EMOJI_EXPENSE = '💸'


def get_date_range(filter_type, start_date_str=None, end_date_str=None):
    """
    Get date range based on filter type.
    
    Args:
        filter_type (str): Type of filter ('today', 'week', 'month', 'quarter', 'year', 'custom', 'all')
        start_date_str (str, optional): Start date for custom range in YYYY-MM-DD format
        end_date_str (str, optional): End date for custom range in YYYY-MM-DD format
        
    Returns:
        tuple: (start_date, end_date) or (None, None) for 'all' filter
    """
    now = datetime.now()
    
    # Handle custom date range
    if filter_type == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            return start_date, end_date
        except ValueError:
            # Invalid date format, fall back to default month filter
            filter_type = 'month'
    
    if filter_type == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == 'week':
        # Monday of this week
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
    elif filter_type == 'month':
        # First day of current month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Last day of current month
        if now.month == 12:
            end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(microseconds=1)
        else:
            end_date = now.replace(month=now.month + 1, day=1) - timedelta(microseconds=1)
    elif filter_type == 'quarter':
        # Calculate current quarter
        quarter = (now.month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        start_date = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Last day of the quarter
        end_month = start_month + 2
        if end_month > 12:
            # Next year's January 1st minus 1 microsecond = December 31st 23:59:59.999999
            end_date = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)
        else:
            # First day of next month minus 1 microsecond = Last day of quarter at 23:59:59.999999
            end_date = now.replace(month=end_month + 1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1)
    elif filter_type == 'year':
        # First day of current year
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        # Last day of current year
        end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(microseconds=1)
    elif filter_type == 'all':
        return None, None
    else:  # Invalid filter, default to 'month'
        # First day of current month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Last day of current month
        if now.month == 12:
            end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(microseconds=1)
        else:
            end_date = now.replace(month=now.month + 1, day=1) - timedelta(microseconds=1)
    
    return start_date, end_date


def _build_category_query_with_totals(category_type, start_date=None, end_date=None):
    """
    Build a query to get categories with their transaction totals.
    
    Args:
        category_type (str): 'income' or 'expense'
        start_date (datetime, optional): Start date for filtering transactions
        end_date (datetime, optional): End date for filtering transactions
        
    Returns:
        SQLAlchemy query: Query object ready for execution
    """
    query = db.session.query(
        Category,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).outerjoin(Transaction, Category.id == Transaction.category_id)
    
    # Apply date filter if provided
    if start_date and end_date:
        query = query.filter(
            or_(
                Transaction.date == None,
                and_(Transaction.date >= start_date, Transaction.date <= end_date)
            )
        )
    
    # Apply category filters
    query = query.filter(
        Category.user_id == g.user.id,
        Category.type == category_type
    ).group_by(Category.id)
    
    return query


def _format_category_data(categories_query_result):
    """
    Format category data for template rendering.
    
    Args:
        categories_query_result: Result from category query with totals
        
    Returns:
        list: Formatted category dictionaries
    """
    categories = []
    for category, total in categories_query_result:
        category_dict = {
            'id': category.id,
            'name': category.name,
            'type': category.type,
            'unicode_emoji': category.unicode_emoji,
            'total': float(total)
        }
        categories.append(category_dict)
    return categories


def _get_filter_display_names():
    """
    Get mapping of filter types to display names.
    
    Returns:
        dict: Mapping of filter keys to display names
    """
    return {
        'today': 'Today',
        'week': 'This Week',
        'month': 'This Month',
        'quarter': 'This Quarter',
        'year': 'This Year',
        'custom': 'Custom Range',
        'all': 'All Time'
    }


@category_bp.route('/')
@login_required
def list_categories():
    """
    Display the categories page with all user categories.
    
    Supports filtering by time period and shows statistics for each category.
    Excludes transfer transactions from calculations.
    """
    # Get filter parameters
    time_filter = request.args.get('filter', DEFAULT_TIME_FILTER)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Get date range based on filter type
    start_date, end_date = get_date_range(time_filter, start_date_str, end_date_str)
    
    # Get categories with totals using helper functions
    income_categories_result = _build_category_query_with_totals('income', start_date, end_date).all()
    expense_categories_result = _build_category_query_with_totals('expense', start_date, end_date).all()
    
    # Format data for template
    income_categories = _format_category_data(income_categories_result)
    expense_categories = _format_category_data(expense_categories_result)
    
    # Calculate statistics
    total_income_categories = len(income_categories)
    total_expense_categories = len(expense_categories)
    total_income = sum(cat['total'] for cat in income_categories)
    total_expenses = sum(cat['total'] for cat in expense_categories)
    
    # Get filter display names
    filter_names = _get_filter_display_names()
    
    # Default to 'month' for invalid filters
    display_filter = time_filter if time_filter in filter_names else DEFAULT_TIME_FILTER
    
    # For custom range, show the date range in display name
    if display_filter == 'custom' and start_date_str and end_date_str:
        filter_display_name = f"Custom Range ({start_date_str} to {end_date_str})"
    else:
        filter_display_name = filter_names.get(display_filter, 'This Month')
    
    return render_template('dashboard/categories.html',
                         income_categories=income_categories,
                         expense_categories=expense_categories,
                         total_income_categories=total_income_categories,
                         total_expense_categories=total_expense_categories,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         current_filter=display_filter,
                         filter_display_name=filter_display_name)


# API Endpoints for CRUD operations

@category_bp.route('/api/categories', methods=['GET'])
@api_login_required
def api_get_categories():
    """API endpoint to get all user categories."""
    try:
        categories = Category.query.filter_by(user_id=g.user.id).all()
        categories_data = []
        
        for cat in categories:
            categories_data.append({
                'id': cat.id,
                'name': cat.name,
                'type': cat.type,
                'type_label': 'Income' if cat.type == 'income' else 'Expense',
                'unicode_emoji': cat.unicode_emoji,
                'user_id': cat.user_id
            })
        
        return jsonify({
            'success': True,
            'categories': categories_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving categories: {str(e)}'
        }), 500


@category_bp.route('/api/categories', methods=['POST'])
@api_login_required
def api_create_category():
    """API endpoint to create a new category."""
    try:
        data = request.get_json()
        
        # Check if data is None (common issue with JSON parsing)
        if data is None:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data provided'
            }), 400
        
        # Basic validation
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Category name is required'
            }), 400
        
        if 'type' not in data or data['type'] not in ['income', 'expense']:
            return jsonify({
                'success': False,
                'error': 'Valid category type is required (income or expense)'
            }), 400
        
        # Check if category with same name and type already exists
        existing_category = Category.query.filter_by(
            user_id=g.user.id,
            name=data['name'],
            type=data['type']
        ).first()
        
        if existing_category:
            return jsonify({
                'success': False,
                'error': f'Category with name "{data["name"]}" and type "{data["type"]}" already exists'
            }), 400
        
        # Set default emoji based on type
        default_emoji = DEFAULT_EMOJI_INCOME if data['type'] == 'income' else DEFAULT_EMOJI_EXPENSE
        
        # Create new category
        new_category = Category(
            name=data['name'],
            type=data['type'],
            unicode_emoji=data.get('unicode_emoji', default_emoji),
            user_id=g.user.id
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category created successfully',
            'category': {
                'id': new_category.id,
                'name': new_category.name,
                'type': new_category.type,
                'type_label': 'Income' if new_category.type == 'income' else 'Expense',
                'unicode_emoji': new_category.unicode_emoji,
                'user_id': new_category.user_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error creating category: {str(e)}'
        }), 500


@category_bp.route('/api/categories/<int:category_id>', methods=['GET'])
@api_login_required
def api_get_category(category_id):
    """API endpoint to get a specific category."""
    try:
        cat = Category.query.filter_by(
            id=category_id,
            user_id=g.user.id
        ).first()
        
        if not cat:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
        return jsonify({
            'success': True,
            'category': {
                'id': cat.id,
                'name': cat.name,
                'type': cat.type,
                'type_label': 'Income' if cat.type == 'income' else 'Expense',
                'unicode_emoji': cat.unicode_emoji,
                'user_id': cat.user_id
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving category: {str(e)}'
        }), 500


@category_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
@api_login_required
def api_update_category(category_id):
    """API endpoint to update a category."""
    try:
        cat = Category.query.filter_by(
            id=category_id,
            user_id=g.user.id
        ).first()
        
        if not cat:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
        data = request.get_json()
        
        # Basic validation
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Category name is required'
            }), 400
        
        if 'type' not in data or data['type'] not in ['income', 'expense']:
            return jsonify({
                'success': False,
                'error': 'Valid category type is required (income or expense)'
            }), 400
        
        # Check if another category with same name and type exists
        existing_category = Category.query.filter_by(
            user_id=g.user.id,
            name=data['name'],
            type=data['type']
        ).filter(Category.id != category_id).first()
        
        if existing_category:
            return jsonify({
                'success': False,
                'error': f'Another category with name "{data["name"]}" and type "{data["type"]}" already exists'
            }), 400
        
        # Update category
        cat.name = data['name']
        cat.type = data['type']
        cat.unicode_emoji = data.get('unicode_emoji', cat.unicode_emoji)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category updated successfully',
            'category': {
                'id': cat.id,
                'name': cat.name,
                'type': cat.type,
                'type_label': 'Income' if cat.type == 'income' else 'Expense',
                'unicode_emoji': cat.unicode_emoji,
                'user_id': cat.user_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error updating category: {str(e)}'
        }), 500


@category_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
@api_login_required
def api_delete_category(category_id):
    """API endpoint to delete a category."""
    try:
        cat = Category.query.filter_by(
            id=category_id,
            user_id=g.user.id
        ).first()
        
        if not cat:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
        # Check if category has associated transactions
        transaction_count = Transaction.query.filter_by(
            category_id=category_id,
            user_id=g.user.id
        ).count()
        
        if transaction_count > 0:
            return jsonify({
                'success': False,
                'error': f'Cannot delete category "{cat.name}". It has {transaction_count} associated transaction{"s" if transaction_count > 1 else ""}. Please remove all transactions first.'
            }), 400
        
        category_name = cat.name
        db.session.delete(cat)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Category "{category_name}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Error deleting category: {str(e)}'
        }), 500


# Additional functionality endpoints

@category_bp.route('/api/categories/stats', methods=['GET'])
@api_login_required
def api_category_stats():
    """API endpoint to get category statistics with time filtering."""
    try:
        # Get filter parameters
        time_filter = request.args.get('filter', 'month')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Get date range based on filter type and custom dates
        start_date, end_date = get_date_range(time_filter, start_date_str, end_date_str)
        
        # Count categories by type
        income_categories = Category.query.filter_by(
            user_id=g.user.id,
            type='income'
        ).count()
        
        expense_categories = Category.query.filter_by(
            user_id=g.user.id,
            type='expense'
        ).count()
        
        # Calculate real totals from transactions with date filter
        income_query = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).join(Category).filter(
            Category.user_id == g.user.id,
            Category.type == 'income'
        )
        
        expense_query = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).join(Category).filter(
            Category.user_id == g.user.id,
            Category.type == 'expense'
        )
        
        # Apply date filter if not 'all'
        if start_date and end_date:
            income_query = income_query.filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
            expense_query = expense_query.filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        
        total_income = income_query.scalar() or 0.0
        total_expenses = expense_query.scalar() or 0.0

        return jsonify({
            'success': True,
            'stats': {
                'income_categories': income_categories,
                'expense_categories': expense_categories,
                'total_income': float(total_income),
                'total_expenses': float(total_expenses),
                'net_income': float(total_income - total_expenses),
                'filter': time_filter
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving category statistics: {str(e)}'
        }), 500


@category_bp.route('/api/categories/top-expenses', methods=['GET'])
@api_login_required
def api_top_expense_categories():
    """API endpoint to get top expense categories with time filtering."""
    try:
        # Get filter parameters
        time_filter = request.args.get('filter', 'month')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Get date range based on filter type
        start_date, end_date = get_date_range(time_filter, start_date_str, end_date_str)
        
        # Base query for top expense categories
        query = db.session.query(
            Category.name,
            Category.unicode_emoji,
            func.sum(Transaction.amount).label('total')
        ).join(Transaction).filter(
            Category.user_id == g.user.id,
            Category.type == 'expense'
        )
        
        # Apply date filter if provided
        if start_date and end_date:
            query = query.filter(
                Transaction.date >= start_date,
                Transaction.date <= end_date
            )
        
        # Get top expenses
        top_expenses = query.group_by(Category.id).order_by(
            func.sum(Transaction.amount).desc()
        ).limit(TOP_CATEGORIES_LIMIT).all()
        
        # Format data for chart
        chart_data = {
            'labels': [expense.name for expense in top_expenses],
            'data': [float(expense.total) for expense in top_expenses],
            'emojis': [expense.unicode_emoji or DEFAULT_EMOJI_EXPENSE for expense in top_expenses]
        }
        
        return jsonify({
            'success': True,
            'chart_data': chart_data,
            'has_data': len(top_expenses) > 0,
            'filter': time_filter
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error retrieving top expense categories: {str(e)}'
        }), 500

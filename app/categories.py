from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g
from app.auth import login_required, api_login_required
from app import db
from app.models import Category, Transaction
from sqlalchemy import func
from datetime import datetime, timedelta

category_bp = Blueprint('categories', __name__, url_prefix='/categories')

def get_date_range(filter_type):
    """Obtener el rango de fechas basado en el tipo de filtro"""
    now = datetime.now()
    
    if filter_type == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif filter_type == 'week':
        # Lunes de esta semana
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)
    elif filter_type == 'month' or not filter_type or filter_type not in ['today', 'week', 'quarter', 'year', 'all']:
        # Primer día del mes actual (default para filtros inválidos)
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Último día del mes actual
        if now.month == 12:
            end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(microseconds=1)
        else:
            end_date = now.replace(month=now.month + 1, day=1) - timedelta(microseconds=1)
    elif filter_type == 'quarter':
        # Calcular el trimestre actual
        quarter = (now.month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        start_date = now.replace(month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        end_month = start_month + 2
        if end_month > 12:
            end_date = now.replace(year=now.year + 1, month=end_month - 12, day=1) - timedelta(microseconds=1)
        else:
            if end_month == 12:
                end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(microseconds=1)
            else:
                end_date = now.replace(month=end_month + 1, day=1) - timedelta(microseconds=1)
    elif filter_type == 'year':
        # Primer día del año actual
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        # Último día del año actual
        end_date = now.replace(year=now.year + 1, month=1, day=1) - timedelta(microseconds=1)
    else:  # 'all'
        return None, None
    
    return start_date, end_date

@category_bp.route('/')
@login_required
def list_categories():
    """Mostrar la página de categorías con todas las categorías del usuario"""
    # Obtener el filtro de tiempo de la query string, por defecto 'month'
    time_filter = request.args.get('filter', 'month')
    start_date, end_date = get_date_range(time_filter)
    
    # Base query for categories
    income_query = db.session.query(
        Category,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).outerjoin(Transaction, Category.id == Transaction.category_id)
    
    expense_query = db.session.query(
        Category,
        func.coalesce(func.sum(Transaction.amount), 0).label('total')
    ).outerjoin(Transaction, Category.id == Transaction.category_id)
    
    # Apply date filter if not 'all'
    if start_date and end_date:
        income_query = income_query.filter(
            db.or_(
                Transaction.date == None,  # Categories without transactions
                db.and_(Transaction.date >= start_date, Transaction.date <= end_date)
            )
        )
        expense_query = expense_query.filter(
            db.or_(
                Transaction.date == None,  # Categories without transactions
                db.and_(Transaction.date >= start_date, Transaction.date <= end_date)
            )
        )
    
    # Apply category filters
    income_categories_query = income_query.filter(
        Category.user_id == g.user.id,
        Category.type == 'income'
    ).group_by(Category.id).all()
    
    expense_categories_query = expense_query.filter(
        Category.user_id == g.user.id,
        Category.type == 'expense'
    ).group_by(Category.id).all()
    
    # Format the results for template
    income_categories = []
    for category, total in income_categories_query:
        category_dict = {
            'id': category.id,
            'name': category.name,
            'type': category.type,
            'unicode_emoji': category.unicode_emoji,
            'total': float(total)
        }
        income_categories.append(category_dict)
    
    expense_categories = []
    for category, total in expense_categories_query:
        category_dict = {
            'id': category.id,
            'name': category.name,
            'type': category.type,
            'unicode_emoji': category.unicode_emoji,
            'total': float(total)
        }
        expense_categories.append(category_dict)
    
    # Calcular estadísticas
    total_income_categories = len(income_categories)
    total_expense_categories = len(expense_categories)
    
    # Calculate total amounts
    total_income = sum(cat['total'] for cat in income_categories)
    total_expenses = sum(cat['total'] for cat in expense_categories)
    
    # Get filter display name
    filter_names = {
        'today': 'Today',
        'week': 'This Week',
        'month': 'This Month',
        'quarter': 'This Quarter',
        'year': 'This Year',
        'all': 'All Time'
    }
    
    # Default to month for invalid filters
    display_filter = time_filter if time_filter in filter_names else 'month'
    
    return render_template('dashboard/categories.html',
                         income_categories=income_categories,
                         expense_categories=expense_categories,
                         total_income_categories=total_income_categories,
                         total_expense_categories=total_expense_categories,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         current_filter=display_filter,
                         filter_display_name=filter_names.get(display_filter, 'This Month'))

# API Endpoints para operaciones CRUD

@category_bp.route('/api/categories', methods=['GET'])
@api_login_required
def api_get_categories():
    """API endpoint para obtener todas las categorías del usuario"""
    try:
        categories = Category.query.filter_by(user_id=g.user.id).all()
        categories_data = []
        
        for cat in categories:
            categories_data.append({
                'id': cat.id,
                'name': cat.name,
                'type': cat.type,
                'type_label': 'Income' if cat.type == 'income' else 'Expense',
                'unicode_emoji': cat.unicode_emoji or '📂',
                'user_id': cat.user_id
            })
        
        return jsonify({
            'success': True,
            'categories': categories_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@category_bp.route('/api/categories', methods=['POST'])
@api_login_required
def api_create_category():
    """API endpoint para crear una nueva categoría"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"DEBUG: Received data: {data}")
        print(f"DEBUG: Content-Type: {request.content_type}")
        print(f"DEBUG: Raw data: {request.get_data()}")
        
        # Check if data is None (common issue with JSON parsing)
        if data is None:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data or Content-Type not set to application/json'
            }), 400
        
        # Validación básica
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Category name is required'
            }), 400
        
        if 'type' not in data:
            return jsonify({
                'success': False,
                'error': 'Category type is required'
            }), 400
        
        # Verificar si ya existe una categoría con el mismo nombre y tipo
        existing_category = Category.query.filter_by(
            user_id=g.user.id,
            name=data['name'],
            type=data['type']
        ).first()
        
        if existing_category:
            return jsonify({
                'success': False,
                'error': 'A category with this name and type already exists'
            }), 400
        
        # Crear nueva categoría
        new_category = Category(
            name=data['name'],
            type=data['type'],
            unicode_emoji=data.get('unicode_emoji', '📂'),
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
            'error': str(e)
        }), 500

@category_bp.route('/api/categories/<int:category_id>', methods=['GET'])
@api_login_required
def api_get_category(category_id):
    """API endpoint para obtener una categoría específica"""
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
            'error': str(e)
        }), 500

@category_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
@api_login_required
def api_update_category(category_id):
    """API endpoint para actualizar una categoría"""
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
        
        # Validación básica
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Category name is required'
            }), 400
        
        if 'type' not in data:
            return jsonify({
                'success': False,
                'error': 'Category type is required'
            }), 400
        
        # Verificar si ya existe otra categoría con el mismo nombre y tipo
        existing_category = Category.query.filter_by(
            user_id=g.user.id,
            name=data['name'],
            type=data['type']
        ).filter(Category.id != category_id).first()
        
        if existing_category:
            return jsonify({
                'success': False,
                'error': 'Another category with this name and type already exists'
            }), 400
        
        # Actualizar categoría
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
            'error': str(e)
        }), 500

@category_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
@api_login_required
def api_delete_category(category_id):
    """API endpoint para eliminar una categoría"""
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
        
        # TODO: Verificar si la categoría tiene transacciones asociadas
        # En el futuro, cuando se implemente el modelo de transacciones,
        # se debe verificar si existen transacciones asociadas a esta categoría
        
        db.session.delete(cat)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Category deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Rutas adicionales para funcionalidades específicas

@category_bp.route('/api/categories/stats', methods=['GET'])
@api_login_required
def api_category_stats():
    """API endpoint para obtener estadísticas de categorías con filtro de tiempo"""
    try:
        # Obtener el filtro de tiempo de la query string
        time_filter = request.args.get('filter', 'month')
        start_date, end_date = get_date_range(time_filter)
        
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
                'filter': time_filter
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Endpoint de prueba sin CSRF
@category_bp.route('/api/test-categories', methods=['POST'])
@api_login_required
def api_test_create_category():
    """API endpoint de prueba para crear una nueva categoría (sin CSRF)"""
    try:
        data = request.get_json()
        
        # Debug logging
        print(f"DEBUG TEST: Received data: {data}")
        print(f"DEBUG TEST: Content-Type: {request.content_type}")
        print(f"DEBUG TEST: User: {g.user.username if g.user else 'None'}")
        
        # Check if data is None (common issue with JSON parsing)
        if data is None:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON data or Content-Type not set to application/json'
            }), 400
        
        # Validación básica
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Category name is required'
            }), 400
        
        if 'type' not in data:
            return jsonify({
                'success': False,
                'error': 'Category type is required'
            }), 400
        
        # Verificar si ya existe una categoría con el mismo nombre y tipo
        existing_category = Category.query.filter_by(
            user_id=g.user.id,
            name=data['name'],
            type=data['type']
        ).first()
        
        if existing_category:
            return jsonify({
                'success': False,
                'error': 'A category with this name and type already exists'
            }), 400
        
        # Crear nueva categoría
        new_category = Category(
            name=data['name'] + ' (TEST)',  # Agregar TEST para distinguir
            type=data['type'],
            unicode_emoji=data.get('unicode_emoji', '🧪'),
            user_id=g.user.id
        )
        
        db.session.add(new_category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Test category created successfully',
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
        print(f"DEBUG TEST: Exception: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
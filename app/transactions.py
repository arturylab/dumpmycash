from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g, Response
from app.auth import login_required, api_login_required
from app.models import db, Transaction, Account, Category
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, desc, func
import csv
import io

transaction_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

transaction_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

def parse_datetime_local(date_string):
    """Parse datetime string from frontend, treating it as local time"""
    if not date_string:
        return datetime.now()
    
    try:
        # The frontend sends datetime-local format: YYYY-MM-DDTHH:MM
        # We need to parse this as local time, not UTC
        if 'T' in date_string:
            # Remove timezone info if present and parse as local time
            if date_string.endswith('Z'):
                date_string = date_string[:-1]
            
            # Parse the datetime string
            dt = datetime.fromisoformat(date_string)
            return dt
        else:
            # If only date is provided, set time to current time
            dt = datetime.strptime(date_string, '%Y-%m-%d')
            now = datetime.now()
            return dt.replace(hour=now.hour, minute=now.minute, second=now.second)
    except (ValueError, TypeError):
        # If parsing fails, return current time
        return datetime.now()

def get_date_range(filter_type, start_date_str=None, end_date_str=None):
    """Obtener el rango de fechas basado en el tipo de filtro"""
    now = datetime.now()
    
    # Handle custom date range
    if filter_type == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            return start_date, end_date
        except ValueError:
            # If custom dates are invalid, fallback to month
            filter_type = 'month'
    
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

@transaction_bp.route('/')
@login_required
def list_transactions():
    """Mostrar la página de transacciones con todas las transacciones del usuario"""
    # Obtener parámetros de filtrado
    account_id = request.args.get('account_id', type=int)
    category_id = request.args.get('category_id', type=int)
    date_range = request.args.get('date_range', 'last_30_days')
    time_filter = request.args.get('filter')  # Solo si se pasa explícitamente
    start_date_str = request.args.get('start_date')  # For custom date range
    end_date_str = request.args.get('end_date')      # For custom date range
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Construir query base - excluir categorías de Transfer
    query = Transaction.query.filter(
        Transaction.user_id == g.user.id,
        ~Transaction.category.has(Category.name == 'Transfer')  # Excluir transferencias
    )
    
    # Aplicar filtros
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    
    # Nuevo filtro por tiempo (prioridad sobre date_range)
    if time_filter:
        if time_filter != 'all':
            start_date, end_date = get_date_range(time_filter, start_date_str, end_date_str)
            if start_date and end_date:
                query = query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
    else:
        # Si no hay filtro de tiempo especificado, usar 'month' como default
        start_date, end_date = get_date_range('month', start_date_str, end_date_str)
        if start_date and end_date:
            query = query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
        time_filter = 'month'  # Set for display purposes
    
    # Filtro por búsqueda
    if search:
        query = query.filter(
            or_(
                Transaction.description.ilike(f'%{search}%'),
                Transaction.category.has(Category.name.ilike(f'%{search}%')),
                Transaction.account.has(Account.name.ilike(f'%{search}%'))
            )
        )
    
    # Ordenar por fecha descendente
    query = query.order_by(desc(Transaction.date))
    
    # Paginar resultados
    transactions = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Obtener cuentas y categorías para los filtros
    accounts = Account.query.filter_by(user_id=g.user.id).all()
    categories = Category.query.filter_by(user_id=g.user.id).all()
    
    # Calcular estadísticas basadas en el filtro aplicado - excluir transferencias
    stats_query = Transaction.query.filter(
        Transaction.user_id == g.user.id,
        ~Transaction.category.has(Category.name == 'Transfer')  # Excluir transferencias
    )
    if time_filter:
        if time_filter != 'all':
            start_date, end_date = get_date_range(time_filter, start_date_str, end_date_str)
            if start_date and end_date:
                stats_query = stats_query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
    else:
        # Si no hay filtro de tiempo especificado, usar 'month' como default
        start_date, end_date = get_date_range('month', start_date_str, end_date_str)
        if start_date and end_date:
            stats_query = stats_query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
    
    # Calcular estadísticas
    total_income = stats_query.filter(
        Transaction.category.has(Category.type == 'income')
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    total_expenses = stats_query.filter(
        Transaction.category.has(Category.type == 'expense')
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    # Obtener nombre para mostrar del filtro
    filter_display_names = {
        'today': 'Today',
        'week': 'This Week', 
        'month': 'This Month',
        'quarter': 'This Quarter',
        'year': 'This Year',
        'custom': 'Custom Range',
        'all': 'All Time'
    }
    
    # Si no hay time_filter especificado, usar 'month' como default
    effective_filter = time_filter if time_filter else 'month'
    
    # For custom range, show the date range in display name
    if effective_filter == 'custom' and start_date_str and end_date_str:
        try:
            start_display = datetime.strptime(start_date_str, '%Y-%m-%d').strftime('%m/%d/%Y')
            end_display = datetime.strptime(end_date_str, '%Y-%m-%d').strftime('%m/%d/%Y')
            filter_display_name = f'{start_display} - {end_display}'
        except ValueError:
            filter_display_name = 'Custom Range'
    else:
        filter_display_name = filter_display_names.get(effective_filter, 'This Month')
    
    current_filter = effective_filter
    
    return render_template('dashboard/transactions.html',
                         transactions=transactions,
                         accounts=accounts,
                         categories=categories,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         current_filters={
                             'account_id': account_id,
                             'category_id': category_id,
                             'date_range': date_range,
                             'search': search,
                             'filter': time_filter,
                             'start_date': start_date_str,
                             'end_date': end_date_str
                         },
                         filter_display_name=filter_display_name,
                         current_filter=current_filter)

@transaction_bp.route('/api/transactions')
@api_login_required
def api_list_transactions():
    """API endpoint para obtener transacciones en formato JSON"""
    # Obtener parámetros de filtrado
    account_id = request.args.get('account_id', type=int)
    category_id = request.args.get('category_id', type=int)
    date_range = request.args.get('date_range', 'last_30_days')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Construir query base - excluir categorías de Transfer
    query = Transaction.query.filter(
        Transaction.user_id == g.user.id,
        ~Transaction.category.has(Category.name == 'Transfer')  # Excluir transferencias
    )
    
    # Aplicar filtros (mismo código que en list_transactions)
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    
    # Filtro por rango de fechas
    if date_range == 'last_30_days':
        start_date = datetime.now() - timedelta(days=30)
        query = query.filter(Transaction.date >= start_date)
    elif date_range == 'last_3_months':
        start_date = datetime.now() - timedelta(days=90)
        query = query.filter(Transaction.date >= start_date)
    elif date_range == 'last_6_months':
        start_date = datetime.now() - timedelta(days=180)
        query = query.filter(Transaction.date >= start_date)
    elif date_range == 'this_year':
        start_date = datetime(datetime.now().year, 1, 1)
        query = query.filter(Transaction.date >= start_date)
    
    # Filtro por búsqueda
    if search:
        query = query.filter(
            or_(
                Transaction.description.ilike(f'%{search}%'),
                Transaction.category.has(Category.name.ilike(f'%{search}%')),
                Transaction.account.has(Account.name.ilike(f'%{search}%'))
            )
        )
    
    # Ordenar por fecha descendente
    query = query.order_by(desc(Transaction.date))
    
    # Paginar resultados
    transactions = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'transactions': [{
            'id': t.id,
            'amount': t.amount,
            'date': t.date.isoformat(),
            'description': t.description,
            'account': {
                'id': t.account.id,
                'name': t.account.name
            },
            'category': {
                'id': t.category.id,
                'name': t.category.name,
                'type': t.category.type,
                'unicode_emoji': t.category.unicode_emoji
            }
        } for t in transactions.items],
        'pagination': {
            'page': transactions.page,
            'pages': transactions.pages,
            'per_page': transactions.per_page,
            'total': transactions.total,
            'has_next': transactions.has_next,
            'has_prev': transactions.has_prev
        }
    })

@transaction_bp.route('/api/transactions', methods=['POST'])
@api_login_required
def api_create_transaction():
    """API endpoint para crear una nueva transacción"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['amount', 'account_id', 'category_id']
        for field in required_fields:
            if field not in data or data[field] is None:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        # Validar que la cuenta pertenece al usuario
        account = Account.query.filter_by(id=data['account_id'], user_id=g.user.id).first()
        if not account:
            return jsonify({'error': 'Cuenta no encontrada'}), 404
        
        # Validar que la categoría pertenece al usuario
        category = Category.query.filter_by(id=data['category_id'], user_id=g.user.id).first()
        if not category:
            return jsonify({'error': 'Categoría no encontrada'}), 404
        
        # Crear nueva transacción
        transaction = Transaction(
            amount=float(data['amount']),
            description=data.get('description', ''),
            account_id=data['account_id'],
            category_id=data['category_id'],
            user_id=g.user.id,
            date=parse_datetime_local(data.get('date'))
        )
        
        db.session.add(transaction)
        
        # Actualizar balance de la cuenta
        if category.type == 'income':
            account.balance += transaction.amount
        else:  # expense
            account.balance -= transaction.amount
        
        db.session.commit()
        
        return jsonify({
            'id': transaction.id,
            'amount': transaction.amount,
            'date': transaction.date.isoformat(),
            'description': transaction.description,
            'account': {
                'id': transaction.account.id,
                'name': transaction.account.name
            },
            'category': {
                'id': transaction.category.id,
                'name': transaction.category.name,
                'type': transaction.category.type,
                'unicode_emoji': transaction.category.unicode_emoji
            }
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Monto inválido'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error al crear la transacción'}), 500
        
        # Actualizar balance de la cuenta
        if category.type == 'income':
            account.balance += transaction.amount
        else:  # expense
            account.balance -= transaction.amount
        
        db.session.commit()
        
        return jsonify({
            'id': transaction.id,
            'amount': transaction.amount,
            'date': transaction.date.isoformat(),
            'description': transaction.description,
            'account': {
                'id': account.id,
                'name': account.name,
                'balance': account.balance
            },
            'category': {
                'id': category.id,
                'name': category.name,
                'type': category.type,
                'unicode_emoji': category.unicode_emoji
            }
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Datos inválidos'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@transaction_bp.route('/api/transactions/<int:transaction_id>')
@api_login_required
def api_get_transaction(transaction_id):
    """API endpoint para obtener una transacción específica"""
    transaction = Transaction.query.filter_by(
        id=transaction_id, 
        user_id=g.user.id
    ).first_or_404()
    
    return jsonify({
        'id': transaction.id,
        'amount': transaction.amount,
        'date': transaction.date.isoformat(),
        'description': transaction.description,
        'account': {
            'id': transaction.account.id,
            'name': transaction.account.name
        },
        'category': {
            'id': transaction.category.id,
            'name': transaction.category.name,
            'type': transaction.category.type,
            'unicode_emoji': transaction.category.unicode_emoji
        }
    })

@transaction_bp.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
@api_login_required
def api_update_transaction(transaction_id):
    """API endpoint para actualizar una transacción"""
    try:
        transaction = Transaction.query.filter_by(
            id=transaction_id, 
            user_id=g.user.id
        ).first_or_404()
        
        data = request.get_json()
        
        # Guardar valores anteriores para revertir balance
        old_amount = transaction.amount
        old_category = transaction.category
        old_account = transaction.account
        
        # Validar nueva cuenta si se cambió
        if 'account_id' in data and data['account_id'] != transaction.account_id:
            new_account = Account.query.filter_by(id=data['account_id'], user_id=g.user.id).first()
            if not new_account:
                return jsonify({'error': 'Cuenta no encontrada'}), 404
        else:
            new_account = old_account
        
        # Validar nueva categoría si se cambió
        if 'category_id' in data and data['category_id'] != transaction.category_id:
            new_category = Category.query.filter_by(id=data['category_id'], user_id=g.user.id).first()
            if not new_category:
                return jsonify({'error': 'Categoría no encontrada'}), 404
        else:
            new_category = old_category
        
        # Revertir balance anterior
        if old_category.type == 'income':
            old_account.balance -= old_amount
        else:  # expense
            old_account.balance += old_amount
        
        # Actualizar campos de la transacción
        if 'amount' in data:
            transaction.amount = float(data['amount'])
        if 'description' in data:
            transaction.description = data['description']
        if 'account_id' in data:
            transaction.account_id = data['account_id']
        if 'category_id' in data:
            transaction.category_id = data['category_id']
        if 'date' in data:
            transaction.date = parse_datetime_local(data['date'])
        
        # Aplicar nuevo balance
        if new_category.type == 'income':
            new_account.balance += transaction.amount
        else:  # expense
            new_account.balance -= transaction.amount
        
        db.session.commit()
        
        return jsonify({
            'id': transaction.id,
            'amount': transaction.amount,
            'date': transaction.date.isoformat(),
            'description': transaction.description,
            'account': {
                'id': new_account.id,
                'name': new_account.name,
                'balance': new_account.balance
            },
            'category': {
                'id': new_category.id,
                'name': new_category.name,
                'type': new_category.type,
                'unicode_emoji': new_category.unicode_emoji
            }
        })
        
    except ValueError:
        return jsonify({'error': 'Datos inválidos'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@transaction_bp.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@api_login_required
def api_delete_transaction(transaction_id):
    """API endpoint para eliminar una transacción"""
    transaction = Transaction.query.filter_by(
        id=transaction_id, 
        user_id=g.user.id
    ).first_or_404()
    
    try:
        # Revertir balance de la cuenta
        account = transaction.account
        category = transaction.category
        
        if category.type == 'income':
            account.balance -= transaction.amount
        else:  # expense
            account.balance += transaction.amount
        
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Transacción eliminada exitosamente',
            'account_balance': account.balance
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@transaction_bp.route('/api/statistics')
@api_login_required
def api_transaction_statistics():
    """API endpoint para obtener estadísticas de transacciones"""
    # Obtener rango de fechas
    date_range = request.args.get('date_range', 'last_30_days')
    
    # Calcular fecha de inicio
    if date_range == 'last_30_days':
        start_date = datetime.now() - timedelta(days=30)
    elif date_range == 'last_3_months':
        start_date = datetime.now() - timedelta(days=90)
    elif date_range == 'last_6_months':
        start_date = datetime.now() - timedelta(days=180)
    elif date_range == 'this_year':
        start_date = datetime(datetime.now().year, 1, 1)
    else:
        start_date = datetime.now() - timedelta(days=30)
    
    # Estadísticas generales
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == g.user.id,
        Transaction.date >= start_date,
        Transaction.category.has(Category.type == 'income'),
        Transaction.category.has(Category.name != 'Transfer')  # Excluir transferencias
    ).scalar() or 0
    
    total_expenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == g.user.id,
        Transaction.date >= start_date,
        Transaction.category.has(Category.type == 'expense'),
        Transaction.category.has(Category.name != 'Transfer')  # Excluir transferencias
    ).scalar() or 0
    
    transaction_count = Transaction.query.filter(
        Transaction.user_id == g.user.id,
        Transaction.date >= start_date,
        ~Transaction.category.has(Category.name == 'Transfer')  # Excluir transferencias
    ).count()
    
    # Gastos por categoría
    expenses_by_category = db.session.query(
        Category.name,
        Category.unicode_emoji,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == g.user.id,
        Transaction.date >= start_date,
        Category.type == 'expense',
        Category.name != 'Transfer'  # Excluir categorías de transferencia
    ).group_by(Category.id, Category.name, Category.unicode_emoji).all()
    
    # Ingresos por categoría
    income_by_category = db.session.query(
        Category.name,
        Category.unicode_emoji,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction).filter(
        Transaction.user_id == g.user.id,
        Transaction.date >= start_date,
        Category.type == 'income',
        Category.name != 'Transfer'  # Excluir categorías de transferencia
    ).group_by(Category.id, Category.name, Category.unicode_emoji).all()
    
    return jsonify({
        'period': date_range,
        'start_date': start_date.isoformat(),
        'summary': {
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'net_income': float(total_income - total_expenses),
            'transaction_count': transaction_count
        },
        'expenses_by_category': [
            {
                'category': row.name,
                'emoji': row.unicode_emoji,
                'amount': float(row.total)
            } for row in expenses_by_category
        ],
        'income_by_category': [
            {
                'category': row.name,
                'emoji': row.unicode_emoji,
                'amount': float(row.total)
            } for row in income_by_category
        ]
    })

@transaction_bp.route('/api/transactions/bulk', methods=['POST'])
@api_login_required
def api_bulk_operations():
    """API endpoint para operaciones masivas en transacciones"""
    try:
        data = request.get_json()
        operation = data.get('operation')
        transaction_ids = data.get('transaction_ids', [])
        
        if not operation or not transaction_ids:
            return jsonify({'error': 'Operación y IDs de transacciones son requeridos'}), 400
        
        # Verificar que todas las transacciones pertenecen al usuario
        transactions = Transaction.query.filter(
            Transaction.id.in_(transaction_ids),
            Transaction.user_id == g.user.id
        ).all()
        
        if len(transactions) != len(transaction_ids):
            return jsonify({'error': 'Algunas transacciones no fueron encontradas'}), 404
        
        if operation == 'delete':
            # Eliminar transacciones y actualizar balances
            for transaction in transactions:
                account = transaction.account
                category = transaction.category
                
                if category.type == 'income':
                    account.balance -= transaction.amount
                else:  # expense
                    account.balance += transaction.amount
                
                db.session.delete(transaction)
            
            db.session.commit()
            return jsonify({'message': f'{len(transactions)} transacciones eliminadas exitosamente'})
        
        else:
            return jsonify({'error': 'Operación no soportada'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno del servidor'}), 500

@transaction_bp.route('/export/csv')
@login_required
def export_csv():
    """Export transactions to CSV format"""
    try:
        # Get same filter parameters as list_transactions
        account_id = request.args.get('account_id', type=int)
        category_id = request.args.get('category_id', type=int)
        search = request.args.get('search', '')
        time_filter = request.args.get('filter', 'month')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Build query with same logic as list_transactions - excluir transferencias
        query = Transaction.query.filter(
            Transaction.user_id == g.user.id,
            ~Transaction.category.has(Category.name == 'Transfer')  # Excluir transferencias
        )
        
        # Apply filters
        if account_id:
            query = query.filter_by(account_id=account_id)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                or_(
                    Transaction.description.ilike(search_term),
                    Transaction.account.has(Account.name.ilike(search_term)),
                    Transaction.category.has(Category.name.ilike(search_term))
                )
            )
        
        # Apply time filter
        if time_filter and time_filter != 'all':
            start_date, end_date = get_date_range(time_filter, start_date_str, end_date_str)
            query = query.filter(
                and_(
                    Transaction.date >= start_date,
                    Transaction.date <= end_date
                )
            )
        
        # Get all transactions (no pagination for export)
        transactions = query.join(Account).join(Category).order_by(desc(Transaction.date)).all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['id', 'date', 'description', 'category', 'account', 'amount'])
        
        # Write transaction data
        for transaction in transactions:
            writer.writerow([
                transaction.id,
                transaction.date.strftime('%Y-%m-%d'),
                transaction.description or '',
                transaction.category.name,
                transaction.account.name,
                float(transaction.amount)
            ])
        
        # Prepare response
        output.seek(0)
        filename = f'transactions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        flash(f'Error exporting transactions: {str(e)}', 'error')
        return redirect(url_for('transactions.list_transactions'))

@transaction_bp.route('/success/<operation>')
@login_required
def transaction_success(operation):
    """Endpoint para mostrar mensajes de éxito después de operaciones de transacciones"""
    messages = {
        'create': 'Transaction created successfully!',
        'update': 'Transaction updated successfully!',
        'delete': 'Transaction deleted successfully!'
    }
    
    message = messages.get(operation, 'Operation completed successfully!')
    flash(message, 'success')
    return redirect(url_for('transactions.list_transactions'))

@transaction_bp.route('/error/<operation>')
@login_required
def transaction_error(operation):
    """Endpoint para mostrar mensajes de error después de operaciones de transacciones"""
    error_message = request.args.get('message', 'An error occurred during the operation.')
    flash(error_message, 'error')
    return redirect(url_for('transactions.list_transactions'))

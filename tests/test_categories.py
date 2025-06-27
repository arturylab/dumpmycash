from app.models import db, User, Category, Transaction
import uuid
import json
import pytest
from datetime import datetime, timedelta

def unique_email():
    """Generate a unique email address for testing."""
    return f"test-{uuid.uuid4().hex[:8]}@example.com"

def unique_username():
    """Generate a unique username for testing."""
    return f"testuser-{uuid.uuid4().hex[:8]}"

@pytest.fixture
def test_user(app, db):
    """Create a test user."""
    with app.app_context():
        user = User(
            username=unique_username(),
            email=unique_email()
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        # Refresh to ensure the user is attached to the session
        db.session.refresh(user)
        yield user

@pytest.fixture
def logged_in_client(client, test_user):
    """A test client logged in as test_user."""
    with client.session_transaction() as sess:
        sess['user_id'] = test_user.id
    return client

@pytest.fixture
def sample_categories(app, db, test_user):
    """Create sample categories for testing."""
    with app.app_context():
        income_category = Category(
            name='Salary',
            type='income',  # Income
            unicode_emoji='💰',
            user_id=test_user.id
        )
        
        expense_category = Category(
            name='Food',
            type='expense',  # Expense
            unicode_emoji='🍕',
            user_id=test_user.id
        )
        
        db.session.add(income_category)
        db.session.add(expense_category)
        db.session.commit()
        
        # Refresh to ensure they are attached to the session
        db.session.refresh(income_category)
        db.session.refresh(expense_category)
        
        yield {
            'income': income_category,
            'expense': expense_category
        }

@pytest.fixture
def sample_transactions(app, db, test_user, sample_categories):
    """Create sample transactions for testing time filters."""
    with app.app_context():
        from app.models import Account
        
        # Create a test account
        account = Account(
            name='Test Account',
            user_id=test_user.id,
            balance=1000.0
        )
        db.session.add(account)
        db.session.commit()
        db.session.refresh(account)
        
        now = datetime.now()
        
        # Create transactions for different time periods
        transactions = []
        
        # Today's transactions
        today_income = Transaction(
            amount=500.0,
            date=now.replace(hour=10),
            description='Today Income',
            account_id=account.id,
            category_id=sample_categories['income'].id,
            user_id=test_user.id
        )
        
        today_expense = Transaction(
            amount=100.0,
            date=now.replace(hour=14),
            description='Today Expense',
            account_id=account.id,
            category_id=sample_categories['expense'].id,
            user_id=test_user.id
        )
        
        # This week's transactions (3 days ago)
        week_income = Transaction(
            amount=300.0,
            date=now - timedelta(days=3),
            description='Week Income',
            account_id=account.id,
            category_id=sample_categories['income'].id,
            user_id=test_user.id
        )
        
        # This month's transactions (15 days ago)
        month_expense = Transaction(
            amount=200.0,
            date=now - timedelta(days=15),
            description='Month Expense',
            account_id=account.id,
            category_id=sample_categories['expense'].id,
            user_id=test_user.id
        )
        
        # Last year's transaction (400 days ago)
        old_income = Transaction(
            amount=1000.0,
            date=now - timedelta(days=400),
            description='Old Income',
            account_id=account.id,
            category_id=sample_categories['income'].id,
            user_id=test_user.id
        )
        
        transactions = [today_income, today_expense, week_income, month_expense, old_income]
        
        for transaction in transactions:
            db.session.add(transaction)
        
        db.session.commit()
        
        for transaction in transactions:
            db.session.refresh(transaction)
        
        yield {
            'account': account,
            'today_income': today_income,
            'today_expense': today_expense,
            'week_income': week_income,
            'month_expense': month_expense,
            'old_income': old_income
        }

class TestCategoriesViews:
    """Test category view routes."""
    
    def test_categories_page_requires_login(self, client):
        """Test that categories page requires login."""
        response = client.get('/categories/')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']
    
    def test_categories_page_renders(self, logged_in_client, sample_categories):
        """Test that categories page renders correctly."""
        response = logged_in_client.get('/categories/')
        assert response.status_code == 200
        assert b'Categories' in response.data
        assert b'Income Categories' in response.data
        assert b'Expense Categories' in response.data
    
    def test_categories_page_shows_user_categories(self, logged_in_client, sample_categories):
        """Test that categories page shows user's categories."""
        response = logged_in_client.get('/categories/')
        assert response.status_code == 200
        assert b'Salary' in response.data
        assert b'Food' in response.data
        # Check for emoji using unicode encoding
        assert '💰'.encode('utf-8') in response.data
        assert '🍕'.encode('utf-8') in response.data
    
    def test_categories_page_empty_state(self, logged_in_client):
        """Test categories page with no categories."""
        response = logged_in_client.get('/categories/')
        assert response.status_code == 200
        assert b'No income categories yet' in response.data
        assert b'No expense categories yet' in response.data

class TestCategoriesAPI:
    """Test category API endpoints."""
    
    def test_get_categories_requires_login(self, client):
        """Test that get categories API requires login."""
        response = client.get('/categories/api/categories')
        assert response.status_code == 401
    
    def test_get_categories_empty(self, logged_in_client):
        """Test get categories API with no categories."""
        response = logged_in_client.get('/categories/api/categories')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['categories'] == []
    
    def test_get_categories_with_data(self, logged_in_client, sample_categories):
        """Test get categories API with sample data."""
        response = logged_in_client.get('/categories/api/categories')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['categories']) == 2
        
        # Check categories structure
        category_names = [cat['name'] for cat in data['categories']]
        assert 'Salary' in category_names
        assert 'Food' in category_names
    
    def test_create_category_requires_login(self, client):
        """Test that create category API requires login."""
        response = client.post('/categories/api/categories', json={
            'name': 'Test Category',
            'type': 'income'
        })
        assert response.status_code == 401
    
    def test_create_category_success(self, logged_in_client):
        """Test successful category creation."""
        category_data = {
            'name': 'Freelance Work',
            'type': 'income',
            'unicode_emoji': '💼'
        }
        
        response = logged_in_client.post('/categories/api/categories', 
                                       json=category_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Category created successfully'
        assert data['category']['name'] == 'Freelance Work'
        assert data['category']['type'] == 'income'
        assert data['category']['unicode_emoji'] == '💼'
    
    def test_create_category_missing_name(self, logged_in_client):
        """Test category creation with missing name."""
        response = logged_in_client.post('/categories/api/categories', json={
            'type': 'income'
        })
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'name is required' in data['error']
    
    def test_create_category_missing_type(self, logged_in_client):
        """Test category creation with missing type."""
        response = logged_in_client.post('/categories/api/categories', json={
            'name': 'Test Category'
        })
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'type is required' in data['error']
    
    def test_create_category_duplicate(self, logged_in_client, sample_categories):
        """Test creating duplicate category."""
        response = logged_in_client.post('/categories/api/categories', json={
            'name': 'Salary',
            'type': 'income'
        })
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'already exists' in data['error']
    
    def test_get_category_requires_login(self, client, sample_categories):
        """Test that get category API requires login."""
        response = client.get(f'/categories/api/categories/{sample_categories["income"].id}')
        assert response.status_code == 401
    
    def test_get_category_success(self, logged_in_client, sample_categories):
        """Test successful category retrieval."""
        response = logged_in_client.get(f'/categories/api/categories/{sample_categories["income"].id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['category']['name'] == 'Salary'
        assert data['category']['type'] == 'income'
    
    def test_get_category_not_found(self, logged_in_client):
        """Test get category with non-existent ID."""
        response = logged_in_client.get('/categories/api/categories/999')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['error']
    
    def test_update_category_requires_login(self, client, sample_categories):
        """Test that update category API requires login."""
        response = client.put(f'/categories/api/categories/{sample_categories["income"].id}', 
                            json={'name': 'Updated Category', 'type': 'income'})
        assert response.status_code == 401
    
    def test_update_category_success(self, logged_in_client, sample_categories):
        """Test successful category update."""
        category_id = sample_categories['income'].id
        update_data = {
            'name': 'Monthly Salary',
            'type': 'income',
            'unicode_emoji': '💵'
        }
        
        response = logged_in_client.put(f'/categories/api/categories/{category_id}', 
                                      json=update_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Category updated successfully'
        assert data['category']['name'] == 'Monthly Salary'
        assert data['category']['unicode_emoji'] == '💵'
    
    def test_update_category_not_found(self, logged_in_client):
        """Test update category with non-existent ID."""
        response = logged_in_client.put('/categories/api/categories/999', 
                                      json={'name': 'Updated Category', 'type': 'income'})
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['error']
    
    def test_update_category_missing_name(self, logged_in_client, sample_categories):
        """Test update category with missing name."""
        category_id = sample_categories['income'].id
        response = logged_in_client.put(f'/categories/api/categories/{category_id}', 
                                      json={'type': 'income'})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'name is required' in data['error']
    
    def test_update_category_duplicate_name(self, logged_in_client, sample_categories):
        """Test update category with duplicate name."""
        category_id = sample_categories['income'].id
        response = logged_in_client.put(f'/categories/api/categories/{category_id}', 
                                      json={'name': 'Food', 'type': 'expense'})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'already exists' in data['error']
    
    def test_delete_category_requires_login(self, client, sample_categories):
        """Test that delete category API requires login."""
        response = client.delete(f'/categories/api/categories/{sample_categories["income"].id}')
        assert response.status_code == 401
    
    def test_delete_category_success(self, logged_in_client, sample_categories):
        """Test successful category deletion."""
        category_id = sample_categories['income'].id
        category_name = sample_categories['income'].name
        
        response = logged_in_client.delete(f'/categories/api/categories/{category_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert f'Category "{category_name}" deleted successfully' in data['message']
        
        # Verify category is actually deleted
        response = logged_in_client.get(f'/categories/api/categories/{category_id}')
        assert response.status_code == 404
    
    def test_delete_category_not_found(self, logged_in_client):
        """Test delete category with non-existent ID."""
        response = logged_in_client.delete('/categories/api/categories/999')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not found' in data['error']
    
    def test_delete_category_with_transactions(self, logged_in_client, sample_categories):
        """Test that category cannot be deleted if it has associated transactions."""
        from app.models import Transaction, Account
        from app import db
        
        # Create a test account first
        account = Account(
            name='Test Account',
            user_id=sample_categories['expense'].user_id,
            balance=1000.0
        )
        db.session.add(account)
        db.session.commit()
        db.session.refresh(account)
        
        # Create a transaction associated with the category
        category = sample_categories['expense']
        
        transaction = Transaction(
            amount=100.0,
            description="Test transaction",
            account_id=account.id,
            category_id=category.id,
            user_id=category.user_id
        )
        db.session.add(transaction)
        db.session.commit()
        
        # Try to delete the category
        response = logged_in_client.delete(f'/categories/api/categories/{category.id}')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Cannot delete category' in data['error']
        assert category.name in data['error']
        assert '1 associated transaction' in data['error']
        
        # Verify category still exists
        response = logged_in_client.get(f'/categories/api/categories/{category.id}')
        assert response.status_code == 200
    
    def test_delete_category_with_multiple_transactions(self, logged_in_client, sample_categories):
        """Test that category cannot be deleted if it has multiple associated transactions with correct plural message."""
        from app.models import Transaction, Account
        from app import db
        
        # Create a test account first
        account = Account(
            name='Test Account',
            user_id=sample_categories['expense'].user_id,
            balance=1000.0
        )
        db.session.add(account)
        db.session.commit()
        db.session.refresh(account)
        
        # Create multiple transactions associated with the category
        category = sample_categories['expense']
        
        transactions = [
            Transaction(
                amount=100.0,
                description="Test transaction 1",
                account_id=account.id,
                category_id=category.id,
                user_id=category.user_id
            ),
            Transaction(
                amount=200.0,
                description="Test transaction 2",
                account_id=account.id,
                category_id=category.id,
                user_id=category.user_id
            ),
            Transaction(
                amount=300.0,
                description="Test transaction 3",
                account_id=account.id,
                category_id=category.id,
                user_id=category.user_id
            )
        ]
        
        for transaction in transactions:
            db.session.add(transaction)
        db.session.commit()
        
        # Try to delete the category
        response = logged_in_client.delete(f'/categories/api/categories/{category.id}')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Cannot delete category' in data['error']
        assert category.name in data['error']
        assert '3 associated transactions' in data['error']  # Plural form
        
        # Verify category still exists
        response = logged_in_client.get(f'/categories/api/categories/{category.id}')
        assert response.status_code == 200
    
    def test_category_stats_requires_login(self, client):
        """Test that category stats API requires login."""
        response = client.get('/categories/api/categories/stats')
        assert response.status_code == 401
    
    def test_category_stats_empty(self, logged_in_client):
        """Test category stats with no categories."""
        response = logged_in_client.get('/categories/api/categories/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stats']['income_categories'] == 0
        assert data['stats']['expense_categories'] == 0
        assert data['stats']['total_income'] == 0.00
        assert data['stats']['total_expenses'] == 0.00
    
    def test_category_stats_with_data(self, logged_in_client, sample_categories):
        """Test category stats with sample data."""
        response = logged_in_client.get('/categories/api/categories/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stats']['income_categories'] == 1
        assert data['stats']['expense_categories'] == 1
        assert data['stats']['total_income'] == 0.00  # No transactions yet
        assert data['stats']['total_expenses'] == 0.00  # No transactions yet

class TestCategoriesTimeFiltering:
    """Test time filtering functionality for categories."""
    
    def test_categories_page_with_time_filter(self, logged_in_client, sample_transactions):
        """Test categories page with different time filters."""
        # Test default (month) filter
        response = logged_in_client.get('/categories/')
        assert response.status_code == 200
        assert b'This Month' in response.data
        
        # Test today filter
        response = logged_in_client.get('/categories/?filter=today')
        assert response.status_code == 200
        assert b'Today' in response.data
        
        # Test week filter
        response = logged_in_client.get('/categories/?filter=week')
        assert response.status_code == 200
        assert b'This Week' in response.data
        
        # Test year filter
        response = logged_in_client.get('/categories/?filter=year')
        assert response.status_code == 200
        assert b'This Year' in response.data
        
        # Test all time filter
        response = logged_in_client.get('/categories/?filter=all')
        assert response.status_code == 200
        assert b'All Time' in response.data
    
    def test_category_totals_with_today_filter(self, logged_in_client, sample_transactions):
        """Test that today filter shows only today's transactions."""
        response = logged_in_client.get('/categories/?filter=today')
        assert response.status_code == 200
        
        # Check that only today's amounts are shown
        # Today: $500 income, $100 expense
        response_text = response.data.decode('utf-8')
        assert '$500.00' in response_text  # Today's income
        assert '$100.00' in response_text  # Today's expense
    
    def test_category_totals_with_week_filter(self, logged_in_client, sample_transactions):
        """Test that week filter shows this week's transactions."""
        response = logged_in_client.get('/categories/?filter=week')
        assert response.status_code == 200
        
        # Check that week totals include this week's transactions
        # (3 days ago is Monday of current week, so it should be included)
        # Week total: $500 (today) + $300 (3 days ago) = $800 income, $100 expense
        response_text = response.data.decode('utf-8')
        assert '$800.00' in response_text  # Week's total income (today + 3 days ago)
        assert '$100.00' in response_text  # Week's total expense
    
    def test_category_totals_with_month_filter(self, logged_in_client, sample_transactions):
        """Test that month filter shows this month's transactions."""
        response = logged_in_client.get('/categories/?filter=month')
        assert response.status_code == 200
        
        # Check that month totals include all this month's transactions
        # Month total: $500 (today) + $300 (week) = $800 income, $100 (today) + $200 (month) = $300 expense
        response_text = response.data.decode('utf-8')
        assert '$800.00' in response_text  # Month's total income
        assert '$300.00' in response_text  # Month's total expense
    
    def test_category_totals_with_all_filter(self, logged_in_client, sample_transactions):
        """Test that all time filter shows all transactions."""
        response = logged_in_client.get('/categories/?filter=all')
        assert response.status_code == 200
        
        # Check that all time totals include everything
        # All time total: $500 + $300 + $1000 = $1800 income, $100 + $200 = $300 expense
        response_text = response.data.decode('utf-8')
        assert '$1,800.00' in response_text  # All time total income
        assert '$300.00' in response_text   # All time total expense
    
    def test_category_stats_api_with_time_filter(self, logged_in_client, sample_transactions):
        """Test category stats API with time filters."""
        # Test today filter
        response = logged_in_client.get('/categories/api/categories/stats?filter=today')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stats']['filter'] == 'today'
        assert data['stats']['total_income'] == 500.0
        assert data['stats']['total_expenses'] == 100.0
        
        # Test week filter
        response = logged_in_client.get('/categories/api/categories/stats?filter=week')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stats']['filter'] == 'week'
        assert data['stats']['total_income'] == 800.0  # Today (500) + 3 days ago (300) = 800
        assert data['stats']['total_expenses'] == 100.0
        
        # Test month filter
        response = logged_in_client.get('/categories/api/categories/stats?filter=month')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stats']['filter'] == 'month'
        assert data['stats']['total_income'] == 800.0   # 500 + 300
        assert data['stats']['total_expenses'] == 300.0  # 100 + 200
        
        # Test all time filter
        response = logged_in_client.get('/categories/api/categories/stats?filter=all')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['stats']['filter'] == 'all'
        assert data['stats']['total_income'] == 1800.0  # 500 + 300 + 1000
        assert data['stats']['total_expenses'] == 300.0  # 100 + 200
    
    def test_invalid_time_filter_defaults_to_month(self, logged_in_client, sample_transactions):
        """Test that invalid time filter defaults to month."""
        response = logged_in_client.get('/categories/?filter=invalid')
        assert response.status_code == 200
        
        # Should default to month behavior and show "This Month" in UI
        response_text = response.data.decode('utf-8')
        assert 'This Month' in response_text
        assert '$800.00' in response_text  # Month's total income
        assert '$300.00' in response_text  # Month's total expense
    
    def test_categories_without_transactions_show_zero(self, logged_in_client, sample_categories):
        """Test that categories without transactions show $0.00 regardless of filter."""
        # Test with different filters
        for filter_type in ['today', 'week', 'month', 'year', 'all']:
            response = logged_in_client.get(f'/categories/?filter={filter_type}')
            assert response.status_code == 200
            
            response_text = response.data.decode('utf-8')
            # Should show categories with $0.00
            assert '$0.00' in response_text
    
    def test_quarter_filter_functionality(self, logged_in_client, sample_transactions):
        """Test quarter filter functionality - should default to month when quarter is not available."""
        response = logged_in_client.get('/categories/?filter=quarter')
        assert response.status_code == 200
        # Since quarter was removed from frontend, it should behave like month filter
        response_text = response.data.decode('utf-8')
        # Should show month-level data or all time data
        
        # Quarter should include this month's data
        response_text = response.data.decode('utf-8')
        assert '$800.00' in response_text  # Quarter's total income
        assert '$300.00' in response_text  # Quarter's total expense
    
    def test_year_filter_functionality(self, logged_in_client, sample_transactions):
        """Test year filter functionality."""
        response = logged_in_client.get('/categories/?filter=year')
        assert response.status_code == 200
        
        # Year should include this year's data (excludes 400 days ago transaction)
        response_text = response.data.decode('utf-8')
        assert '$800.00' in response_text  # Year's total income
        assert '$300.00' in response_text  # Year's total expense

class TestCategoriesDateRangeHelper:
    """Test the get_date_range helper function."""
    
    def test_get_date_range_function(self, app):
        """Test the get_date_range helper function directly."""
        with app.app_context():
            from app.categories import get_date_range
            
            # Test today range
            start, end = get_date_range('today')
            assert start is not None
            assert end is not None
            assert start.hour == 0
            assert end.hour == 23
            
            # Test week range
            start, end = get_date_range('week')
            assert start is not None
            assert end is not None
            assert start.weekday() == 0  # Monday
            
            # Test month range
            start, end = get_date_range('month')
            assert start is not None
            assert end is not None
            assert start.day == 1
            
            # Test all range
            start, end = get_date_range('all')
            assert start is None
            assert end is None
            
            # Test invalid filter (should default to month)
            start, end = get_date_range('invalid')
            assert start is not None
            assert end is not None
            assert start.day == 1  # Should behave like month
            
            # Test empty filter (should default to month)
            start, end = get_date_range('')
            assert start is not None
            assert end is not None
            assert start.day == 1  # Should behave like month

class TestCategoriesNewFilters:
    """Test cases for new filtering options (quarter and custom range)."""
    
    def test_quarter_filter_with_categories_page(self, logged_in_client, sample_transactions):
        """Test quarter filter on categories page."""
        response = logged_in_client.get('/categories/?filter=quarter')
        assert response.status_code == 200
        
        # Check that quarter filter is active
        html_content = response.get_data(as_text=True)
        assert 'This Quarter' in html_content
        
    def test_custom_range_filter_with_categories_page(self, logged_in_client, sample_transactions):
        """Test custom range filter on categories page."""
        # Test with a specific date range
        start_date = '2024-01-01'
        end_date = '2024-01-31'
        
        response = logged_in_client.get(f'/categories/?filter=custom&start_date={start_date}&end_date={end_date}')
        assert response.status_code == 200
        
        # Check that custom filter is displayed
        html_content = response.get_data(as_text=True)
        assert 'Custom Range' in html_content
        assert start_date in html_content
        assert end_date in html_content
        
    def test_get_date_range_quarter_functionality(self, app):
        """Test quarter date range calculation in detail."""
        from app.categories import get_date_range
        
        with app.app_context():
            # Test that quarter function returns valid dates
            start, end = get_date_range('quarter')
            assert start is not None
            assert end is not None
            assert start.day == 1
            assert start.hour == 0
            assert start.minute == 0
            assert start.second == 0
            assert end.hour == 23
            assert end.minute == 59
            assert end.second == 59
            
            # Verify quarter calculation logic
            from datetime import datetime
            now = datetime.now()
            quarter = (now.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            
            assert start.month == start_month
            assert start.year == now.year
                
    def test_get_date_range_custom_functionality(self, app):
        """Test custom date range functionality."""
        from app.categories import get_date_range
        
        with app.app_context():
            # Test valid custom range
            start, end = get_date_range('custom', '2024-01-01', '2024-01-31')
            assert start is not None
            assert end is not None
            assert start.year == 2024
            assert start.month == 1
            assert start.day == 1
            assert start.hour == 0
            assert end.year == 2024
            assert end.month == 1
            assert end.day == 31
            assert end.hour == 23
            
            # Test invalid date format (should fall back to month)
            start, end = get_date_range('custom', 'invalid-date', '2024-01-31')
            assert start is not None
            assert end is not None
            assert start.day == 1  # Should fall back to month behavior
            
            # Test missing dates (should fall back to month)
            start, end = get_date_range('custom', None, None)
            assert start is not None
            assert end is not None
            assert start.day == 1  # Should fall back to month behavior
            
    def test_quarter_filter_display_name(self, app):
        """Test that quarter filter shows correct display name."""
        from app.categories import _get_filter_display_names
        
        with app.app_context():
            filter_names = _get_filter_display_names()
            assert 'quarter' in filter_names
            assert filter_names['quarter'] == 'This Quarter'
            
    def test_custom_filter_display_name(self, app):
        """Test that custom filter shows correct display name.""" 
        from app.categories import _get_filter_display_names
        
        with app.app_context():
            filter_names = _get_filter_display_names()
            assert 'custom' in filter_names
            assert filter_names['custom'] == 'Custom Range'

    def test_category_stats_api_with_quarter_filter(self, logged_in_client, sample_transactions):
        """Test category stats API with quarter filter."""
        response = logged_in_client.get('/categories/api/categories/stats?filter=quarter')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'stats' in data
        assert data['stats']['filter'] == 'quarter'
        
    def test_category_stats_api_with_custom_filter(self, logged_in_client, sample_transactions):
        """Test category stats API with custom date range."""
        start_date = '2024-01-01'
        end_date = '2024-01-31'
        
        response = logged_in_client.get(f'/categories/api/categories/stats?filter=custom&start_date={start_date}&end_date={end_date}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'stats' in data
        assert data['stats']['filter'] == 'custom'

    def test_top_expenses_chart_with_quarter_filter(self, logged_in_client, sample_transactions):
        """Test top expenses chart API with quarter filter."""
        response = logged_in_client.get('/categories/api/categories/top-expenses?filter=quarter')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'chart_data' in data
        assert 'filter' in data
        assert data['filter'] == 'quarter'
        
    def test_top_expenses_chart_with_custom_filter(self, logged_in_client, sample_transactions):
        """Test top expenses chart API with custom date range."""
        start_date = '2024-01-01'
        end_date = '2024-01-31'
        
        response = logged_in_client.get(f'/categories/api/categories/top-expenses?filter=custom&start_date={start_date}&end_date={end_date}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'success' in data
        assert data['success'] is True
        assert 'chart_data' in data
        assert 'filter' in data
        assert data['filter'] == 'custom'

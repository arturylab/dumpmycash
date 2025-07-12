"""
Tests for the home/dashboard functionality.
"""

import pytest
from datetime import datetime, timedelta
from app.models import Transaction, Category, Account, db


class TestHomeDashboard:
    """Test cases for home dashboard functionality."""
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires login."""
        response = client.get('/home/')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_dashboard_authenticated(self, client, auth_client):
        """Test dashboard loads for authenticated user."""
        # Create and login user
        user = auth_client.create_user()
        auth_client.login()
        
        response = client.get('/home/')
        assert response.status_code == 200
        assert b'Total Balance' in response.data
    
    def test_dashboard_empty_state(self, client, auth_client):
        """Test dashboard shows empty state when no transactions."""
        user = auth_client.create_user()
        auth_client.login()
        
        response = client.get('/home/')
        assert response.status_code == 200
        assert b'$0.00' in response.data  # Total balance should be 0
        assert b'Financial Overview' in response.data
    
    def test_dashboard_with_transactions(self, client, auth_client, db):
        """Test dashboard shows correct structure and calculates balance properly."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create a category (this is expense category, so both transactions will be expenses)
        category = Category(name="Food", type="expense", user_id=user.id)
        db.session.add(category)
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()

        # Create some transactions (both are expenses since category is expense type)
        transactions = [
            Transaction(
                amount=100.00,
                description="Salary",
                date=datetime.now(),
                user_id=user.id,
                category_id=category.id,
                account_id=account.id
            ),
            Transaction(
                amount=50.00,
                description="Groceries",
                date=datetime.now(),
                user_id=user.id,
                category_id=category.id,
                account_id=account.id
            )
        ]
        
        for t in transactions:
            db.session.add(t)
        db.session.commit()
        
        response = client.get('/home/')
        assert response.status_code == 200
        # Check for dashboard structure elements instead of transaction details
        assert b'Total Balance' in response.data
        assert b'Financial Overview' in response.data
        assert b'Quick Actions' in response.data
        assert b'Daily Expenses' in response.data
        assert b'Monthly Expenses' in response.data
        # Since both transactions are expenses, balance should be -$150.00
        assert b'-$150.00' in response.data  # Total balance (0 - 100 - 50)
    
    def test_api_stats_requires_login(self, client):
        """Test that API stats endpoint requires login."""
        response = client.get('/home/api/stats')
        assert response.status_code == 302
    
    def test_api_stats_authenticated(self, client, auth_client, db):
        """Test API stats endpoint returns correct data."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create some transactions
        category = Category(name="Test", type="income", user_id=user.id)
        db.session.add(category)
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()

        transaction = Transaction(
            amount=100.00,
            description="Test Income",
            date=datetime.now(),
            user_id=user.id,
            category_id=category.id,
            account_id=account.id
        )
        db.session.add(transaction)
        db.session.commit()
        
        response = client.get('/home/api/stats')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'total_balance' in data['data']
        assert data['data']['total_balance'] == 100.0
    
    def test_api_stats_with_days_parameter(self, client, auth_client, db):
        """Test API stats endpoint with days parameter."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create transactions from different periods
        category = Category(name="Test", type="income", user_id=user.id)
        db.session.add(category)
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        # Recent transaction (last 7 days)
        recent_transaction = Transaction(
            amount=100.00,
            description="Recent",
            date=datetime.now() - timedelta(days=3),
            user_id=user.id,
            category_id=category.id,
            account_id=account.id
        )
        
        # Old transaction (more than 30 days)
        old_transaction = Transaction(
            amount=50.00,
            description="Old",
            date=datetime.now() - timedelta(days=40),
            user_id=user.id,
            category_id=category.id,
            account_id=account.id
        )
        
        db.session.add_all([recent_transaction, old_transaction])
        db.session.commit()
        
        # Test with 7 days filter
        response = client.get('/home/api/stats?days=7')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['period_income'] == 100.0  # Only recent transaction
        assert data['data']['total_balance'] == 150.0  # Both transactions for total
    
    def test_api_recent_transactions(self, client, auth_client, db):
        """Test API recent transactions endpoint."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create multiple transactions
        category = Category(name="Test", type="expense", user_id=user.id)
        db.session.add(category)
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        transactions = []
        for i in range(15):  # More than default limit
            transaction = Transaction(
                amount=10.00 * i,
                description=f"Transaction {i}",
                date=datetime.now() - timedelta(days=i),
                user_id=user.id,
                category_id=category.id,
                account_id=account.id
            )
            transactions.append(transaction)
        
        db.session.add_all(transactions)
        db.session.commit()
        
        response = client.get('/home/api/recent-transactions')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['data']) == 10  # Default limit
        
        # Test with custom limit
        response = client.get('/home/api/recent-transactions?limit=5')
        data = response.get_json()
        assert len(data['data']) == 5
        
        # Verify transactions are ordered by date (newest first)
        first_transaction = data['data'][0]
        assert first_transaction['description'] == 'Transaction 0'
    
    def test_api_category_breakdown(self, client, auth_client, db):
        """Test API category breakdown endpoint."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create categories and transactions
        food_category = Category(name="Food", type="expense", user_id=user.id)
        transport_category = Category(name="Transport", type="expense", user_id=user.id)
        db.session.add_all([food_category, transport_category])
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        transactions = [
            Transaction(
                amount=100.00,
                description="Groceries",
                date=datetime.now(),
                user_id=user.id,
                category_id=food_category.id,
                account_id=account.id
            ),
            Transaction(
                amount=50.00,
                description="Gas",
                date=datetime.now(),
                user_id=user.id,
                category_id=transport_category.id,
                account_id=account.id
            ),
            Transaction(
                amount=25.00,
                description="Restaurant",
                date=datetime.now(),
                user_id=user.id,
                category_id=food_category.id,
                account_id=account.id
            )
        ]
        
        db.session.add_all(transactions)
        db.session.commit()
        
        response = client.get('/home/api/category-breakdown')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['data']['categories']) == 2
        
        # Food should be first (higher amount: 125)
        food_data = data['data']['categories'][0]
        assert food_data['name'] == 'Food'
        assert food_data['amount'] == 125.0
        assert food_data['percentage'] > 70  # Should be about 71.4%
    
    def test_api_category_breakdown_income(self, client, auth_client, db):
        """Test API category breakdown for income transactions."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create category and income transaction
        salary_category = Category(name="Salary", type="income", user_id=user.id)
        db.session.add(salary_category)
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        transaction = Transaction(
            amount=1000.00,
            description="Monthly Salary",
            date=datetime.now(),
            user_id=user.id,
            category_id=salary_category.id,
            account_id=account.id
        )
        db.session.add(transaction)
        db.session.commit()
        
        response = client.get('/home/api/category-breakdown?type=income')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['data']['categories']) == 1
        assert data['data']['categories'][0]['name'] == 'Salary'
        assert data['data']['categories'][0]['amount'] == 1000.0
    
    def test_api_monthly_trend(self, client, auth_client, db):
        """Test API monthly trend endpoint."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create categories for different transaction types
        expense_category = Category(name="Expenses", type="expense", user_id=user.id)
        income_category = Category(name="Income", type="income", user_id=user.id)
        db.session.add_all([expense_category, income_category])
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        # Create transactions for different months
        current_date = datetime.now()
        
        # Current month income
        current_income = Transaction(
            amount=1000.00,
            description="Current Income",
            date=current_date,
            user_id=user.id,
            category_id=income_category.id,
            account_id=account.id
        )
        
        # Current month expense
        current_expense = Transaction(
            amount=500.00,
            description="Current Expense",
            date=current_date,
            user_id=user.id,
            category_id=expense_category.id,
            account_id=account.id
        )
        
        # Previous month transactions
        prev_month = current_date.replace(day=1) - timedelta(days=1)
        prev_income = Transaction(
            amount=800.00,
            description="Previous Income",
            date=prev_month,
            user_id=user.id,
            category_id=income_category.id,
            account_id=account.id
        )
        
        db.session.add_all([current_income, current_expense, prev_income])
        db.session.commit()
        
        response = client.get('/home/api/monthly-trend')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert len(data['data']) == 12  # 12 months of data
        
        # Current month should have income and expenses
        current_month_data = None
        for month_data in data['data']:
            if month_data['month_num'] == current_date.month and month_data['year'] == current_date.year:
                current_month_data = month_data
                break
        
        assert current_month_data is not None
        assert current_month_data['income'] == 1000.0
        assert current_month_data['expenses'] == 500.0
        assert current_month_data['net'] == 500.0
    
    def test_dashboard_redirect_from_root(self, client, auth_client):
        """Test that root path redirects to dashboard for authenticated users."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.get('/')
        assert response.status_code == 302
        assert '/home/' in response.location
    
    def test_dashboard_redirect_from_dashboard_home(self, client, auth_client):
        """Test that /home redirects to home blueprint."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.get('/home')
        assert response.status_code == 302
        assert '/home/' in response.location
    
    def test_balance_calculation_mixed_transactions(self, client, auth_client, db):
        """Test balance calculation with mixed income and expense transactions."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create categories for different transaction types
        expense_category = Category(name="Expenses", type="expense", user_id=user.id)
        income_category = Category(name="Income", type="income", user_id=user.id)
        db.session.add_all([expense_category, income_category])
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        # Create mixed transactions
        transactions = [
            Transaction(amount=1000, description="Salary", 
                       date=datetime.now(), user_id=user.id, category_id=income_category.id, account_id=account.id),
            Transaction(amount=200, description="Rent", 
                       date=datetime.now(), user_id=user.id, category_id=expense_category.id, account_id=account.id),
            Transaction(amount=50, description="Food", 
                       date=datetime.now(), user_id=user.id, category_id=expense_category.id, account_id=account.id),
            Transaction(amount=500, description="Bonus", 
                       date=datetime.now(), user_id=user.id, category_id=income_category.id, account_id=account.id),
        ]
        
        db.session.add_all(transactions)
        db.session.commit()
        
        response = client.get('/home/api/stats')
        data = response.get_json()
        
        # Balance should be: (1000 + 500) - (200 + 50) = 1250
        assert data['data']['total_balance'] == 1250.0
        assert data['data']['period_income'] == 1500.0
        assert data['data']['period_expenses'] == 250.0
    
    def test_api_error_handling(self, client, auth_client):
        """Test API error handling for invalid requests."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Test with invalid limit (should cap at 50)
        response = client.get('/home/api/recent-transactions?limit=100')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['data']) <= 50  # Should be capped
        
        # Test with invalid days parameter
        response = client.get('/home/api/stats?days=invalid')
        assert response.status_code == 200  # Should default to 30
        
        data = response.get_json()
        assert data['data']['period_days'] == 30
    
    def test_api_daily_activity(self, client, auth_client, db):
        """Test API daily activity endpoint."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create categories and account
        income_category = Category(name="Salary", type="income", user_id=user.id)
        expense_category = Category(name="Food", type="expense", user_id=user.id)
        db.session.add_all([income_category, expense_category])
        db.session.commit()
        
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        # Create transactions for different days in current month
        now = datetime.now()
        transactions = [
            Transaction(
                amount=100.00,
                description="Daily Income",
                date=now.replace(day=1, hour=10, minute=0, second=0),
                user_id=user.id,
                category_id=income_category.id,
                account_id=account.id
            ),
            Transaction(
                amount=50.00,
                description="Daily Expense",
                date=now.replace(day=1, hour=15, minute=0, second=0),
                user_id=user.id,
                category_id=expense_category.id,
                account_id=account.id
            ),
            Transaction(
                amount=200.00,
                description="Another Income",
                date=now.replace(day=2, hour=9, minute=0, second=0),
                user_id=user.id,
                category_id=income_category.id,
                account_id=account.id
            )
        ]
        
        db.session.add_all(transactions)
        db.session.commit()
        
        response = client.get('/home/api/daily-activity')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        
        daily_data = data['data']
        assert len(daily_data) > 0  # Should have days from current month
        
        # Check data structure
        first_day = daily_data[0]
        required_fields = ['day', 'date', 'income', 'expenses', 'net']
        for field in required_fields:
            assert field in first_day
        
        # Find day 1 and verify calculations
        day_1_data = next((d for d in daily_data if d['day'] == 1), None)
        if day_1_data:
            assert day_1_data['income'] == 100.0
            assert day_1_data['expenses'] == 50.0
            assert day_1_data['net'] == 50.0
        
        # Find day 2 and verify
        day_2_data = next((d for d in daily_data if d['day'] == 2), None)
        if day_2_data:
            assert day_2_data['income'] == 200.0
            assert day_2_data['expenses'] == 0.0
            assert day_2_data['net'] == 200.0
    
    def test_api_weekly_expenses(self, client, auth_client, db):
        """Test API weekly expenses endpoint."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create expense category
        expense_category = Category(name="Expenses", type="expense", user_id=user.id)
        db.session.add(expense_category)
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        # Create transactions for different days of current week
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        
        transactions = []
        # Add expenses for Monday (day 0) and Wednesday (day 2)
        for day_offset, amount in [(0, 100.0), (2, 150.0)]:
            transaction_date = start_of_week + timedelta(days=day_offset)
            transaction = Transaction(
                amount=amount,
                description=f"Expense Day {day_offset}",
                date=transaction_date,
                user_id=user.id,
                category_id=expense_category.id,
                account_id=account.id
            )
            transactions.append(transaction)
        
        db.session.add_all(transactions)
        db.session.commit()
        
        response = client.get('/home/api/weekly-expenses')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        
        weekly_data = data['data']
        assert len(weekly_data) == 7  # Should have 7 days (Monday to Sunday)
        
        # Check data structure
        first_day = weekly_data[0]
        required_fields = ['day', 'day_name', 'expenses']
        for field in required_fields:
            assert field in first_day
        
        # Check day names are correct
        expected_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        actual_days = [day['day_name'] for day in weekly_data]
        assert actual_days == expected_days
        
        # Check Monday has 100.0 expenses
        monday_data = weekly_data[0]
        assert monday_data['day_name'] == 'Mon'
        assert monday_data['expenses'] == 100.0
        
        # Check Wednesday has 150.0 expenses
        wednesday_data = weekly_data[2]
        assert wednesday_data['day_name'] == 'Wed'
        assert wednesday_data['expenses'] == 150.0
        
        # Check other days have 0.0 expenses
        for i in [1, 3, 4, 5, 6]:  # Tue, Thu, Fri, Sat, Sun
            assert weekly_data[i]['expenses'] == 0.0
    
    def test_api_daily_expenses(self, client, auth_client, db):
        """Test API daily expenses endpoint."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create expense category
        expense_category = Category(name="Food", type="expense", user_id=user.id)
        db.session.add(expense_category)
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        # Create transactions for different days of current month
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        
        transactions = [
            Transaction(
                amount=50.0,
                description="Day 1 Expense",
                date=current_month_start.replace(day=1),
                user_id=user.id,
                category_id=expense_category.id,
                account_id=account.id
            ),
            Transaction(
                amount=75.0,
                description="Day 3 Expense",
                date=current_month_start.replace(day=3),
                user_id=user.id,
                category_id=expense_category.id,
                account_id=account.id
            ),
            Transaction(
                amount=25.0,
                description="Day 3 Another Expense",
                date=current_month_start.replace(day=3),
                user_id=user.id,
                category_id=expense_category.id,
                account_id=account.id
            )
        ]
        
        db.session.add_all(transactions)
        db.session.commit()
        
        response = client.get('/home/api/daily-expenses')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        
        daily_data = data['data']
        assert len(daily_data) > 0  # Should have days from current month
        
        # Check data structure
        first_day = daily_data[0]
        required_fields = ['day', 'day_name', 'date', 'expenses']
        for field in required_fields:
            assert field in first_day
        
        # Find day 1 and verify expenses
        day_1_data = next((d for d in daily_data if d['day'] == 1), None)
        assert day_1_data is not None
        assert day_1_data['expenses'] == 50.0
        
        # Find day 3 and verify combined expenses
        day_3_data = next((d for d in daily_data if d['day'] == 3), None)
        assert day_3_data is not None
        assert day_3_data['expenses'] == 100.0  # 75 + 25
        
        # Check that other days have 0.0 expenses
        day_2_data = next((d for d in daily_data if d['day'] == 2), None)
        assert day_2_data is not None
        assert day_2_data['expenses'] == 0.0

    def test_api_monthly_expenses_current_year(self, client, auth_client, db):
        """Test API monthly expenses endpoint for current year."""
        user = auth_client.create_user()
        auth_client.login()
        
        # Create expense category
        expense_category = Category(name="General", type="expense", user_id=user.id)
        db.session.add(expense_category)
        db.session.commit()
        
        # Create an account
        account = Account(name="Test Account", user_id=user.id, balance=1000.0)
        db.session.add(account)
        db.session.commit()
        
        # Create transactions for different months of current year
        now = datetime.now()
        current_year = now.year
        
        transactions = [
            # January expense
            Transaction(
                amount=200.0,
                description="January Expense",
                date=datetime(current_year, 1, 15),
                user_id=user.id,
                category_id=expense_category.id,
                account_id=account.id
            ),
            # March expense
            Transaction(
                amount=300.0,
                description="March Expense",
                date=datetime(current_year, 3, 10),
                user_id=user.id,
                category_id=expense_category.id,
                account_id=account.id
            ),
            # Current month expense
            Transaction(
                amount=150.0,
                description="Current Month Expense",
                date=datetime(current_year, now.month, 5),
                user_id=user.id,
                category_id=expense_category.id,
                account_id=account.id
            ),
            # Previous year expense (should not appear)
            Transaction(
                amount=500.0,
                description="Previous Year Expense",
                date=datetime(current_year - 1, 12, 25),
                user_id=user.id,
                category_id=expense_category.id,
                account_id=account.id
            )
        ]
        
        db.session.add_all(transactions)
        db.session.commit()
        
        response = client.get('/home/api/monthly-expenses')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        
        monthly_data = data['data']
        assert len(monthly_data) == 12  # Should have 12 months
        
        # Check data structure
        first_month = monthly_data[0]
        required_fields = ['month', 'month_name', 'year', 'expenses']
        for field in required_fields:
            assert field in first_month
        
        # All months should be from current year
        for month_data in monthly_data:
            assert month_data['year'] == current_year
        
        # Check specific months
        january_data = next((m for m in monthly_data if m['month_name'] == 'Jan'), None)
        assert january_data is not None
        assert january_data['expenses'] == 200.0
        
        march_data = next((m for m in monthly_data if m['month_name'] == 'Mar'), None)
        assert march_data is not None
        assert march_data['expenses'] == 300.0
        
        # Check current month
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        current_month_name = month_names[now.month - 1]
        current_month_data = next((m for m in monthly_data if m['month_name'] == current_month_name), None)
        assert current_month_data is not None
        assert current_month_data['expenses'] == 150.0
        
        # Check that February has 0.0 expenses
        february_data = next((m for m in monthly_data if m['month_name'] == 'Feb'), None)
        assert february_data is not None
        assert february_data['expenses'] == 0.0

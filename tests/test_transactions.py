import pytest
from datetime import datetime, timedelta
from app.models import User, Account, Category, Transaction, db


class TestTransactions:
    """Test suite for transaction functionality"""

    @pytest.fixture
    def user(self, db, auth_client):
        """Create a test user"""
        return auth_client.create_user()

    @pytest.fixture
    def account(self, db, user):
        """Create a test account"""
        account = Account(
            name='Test Account',
            user_id=user.id,
            balance=1000.00
        )
        db.session.add(account)
        db.session.commit()
        return account

    @pytest.fixture
    def category_income(self, db, user):
        """Create a test income category"""
        category = Category(
            name='Salary',
            type='income',
            unicode_emoji='💰',
            user_id=user.id
        )
        db.session.add(category)
        db.session.commit()
        return category

    @pytest.fixture
    def category_expense(self, db, user):
        """Create a test expense category"""
        category = Category(
            name='Food',
            type='expense',
            unicode_emoji='🍕',
            user_id=user.id
        )
        db.session.add(category)
        db.session.commit()
        return category

    @pytest.fixture
    def transaction(self, db, user, account, category_expense):
        """Create a test transaction"""
        transaction = Transaction(
            amount=50.00,
            description='Test transaction',
            account_id=account.id,
            category_id=category_expense.id,
            user_id=user.id,
            date=datetime.now()
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def test_list_transactions_requires_login(self, client):
        """Test that transaction list requires authentication"""
        response = client.get('/transactions/')
        assert response.status_code == 302  # Redirect to login

    def test_list_transactions_authenticated(self, client, auth_client, user, account, category_expense, transaction):
        """Test transaction list for authenticated user"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        assert b'Test transaction' in response.data

    def test_list_transactions_empty(self, client, auth_client, user):
        """Test transaction list when user has no transactions"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        assert b'No transactions found' in response.data

    def test_transaction_modal_elements(self, client, auth_client, user, account, category_expense):
        """Test that transaction modal elements are present"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        assert b'transactionModal' in response.data
        assert b'Add Transaction' in response.data

    def test_create_transaction_success(self, client, auth_client, user, account, category_expense):
        """Test successful transaction creation via API"""
        auth_client.login()
        initial_balance = account.balance
        
        response = client.post('/transactions/api/transactions', 
                              json={
                                  'amount': 75.50,
                                  'description': 'Groceries',
                                  'account_id': account.id,
                                  'category_id': category_expense.id,
                                  'date': datetime.now().isoformat()
                              })
        
        assert response.status_code == 201
        
        # Check if transaction was created in database
        transaction = Transaction.query.filter_by(description='Groceries').first()
        assert transaction is not None
        assert transaction.amount == 75.50
        assert transaction.user_id == user.id
        
        # Check if account balance was updated (expense should decrease balance)
        db.session.refresh(account)
        assert account.balance == initial_balance - 75.50

    def test_create_transaction_income(self, client, auth_client, user, account, category_income):
        """Test creating an income transaction via API"""
        auth_client.login()
        initial_balance = account.balance
        
        response = client.post('/transactions/api/transactions', 
                              json={
                                  'amount': 2500.00,
                                  'description': 'Monthly salary',
                                  'account_id': account.id,
                                  'category_id': category_income.id,
                                  'date': datetime.now().isoformat()
                              })
        
        assert response.status_code == 201
        
        # Check if account balance was updated (income should increase balance)
        db.session.refresh(account)
        assert account.balance == initial_balance + 2500.00

    def test_transaction_row_clickable(self, client, auth_client, user, transaction):
        """Test that transaction rows have clickable attributes"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        assert b'transaction-row' in response.data
        assert b'data-transaction-id' in response.data

    def test_view_transaction_not_found(self, client, auth_client, user):
        """Test getting non-existent transaction via API"""
        auth_client.login()
        
        response = client.get('/transactions/api/transactions/999')
        assert response.status_code == 404

    def test_edit_transaction_via_api(self, client, auth_client, user, transaction):
        """Test editing transaction via API"""
        auth_client.login()
        
        response = client.put(f'/transactions/api/transactions/{transaction.id}',
                             json={
                                 'amount': 65.00,
                                 'description': 'Updated transaction'
                             })
        
        assert response.status_code == 200
        
        # Check if transaction was updated in database
        db.session.refresh(transaction)
        assert transaction.amount == 65.00
        assert transaction.description == 'Updated transaction'

    def test_update_transaction_success(self, client, auth_client, user, transaction, account, category_expense):
        """Test successful transaction update via API"""
        auth_client.login()
        
        response = client.put(f'/transactions/api/transactions/{transaction.id}',
                             json={
                                 'amount': 65.00,
                                 'description': 'Updated transaction',
                                 'account_id': account.id,
                                 'category_id': category_expense.id,
                                 'date': datetime.now().isoformat()
                             })
        
        assert response.status_code == 200
        
        # Check if transaction was updated in database
        db.session.refresh(transaction)
        assert transaction.amount == 65.00
        assert transaction.description == 'Updated transaction'

    def test_delete_transaction_success(self, client, auth_client, user, transaction, account):
        """Test successful transaction deletion via API"""
        auth_client.login()
        initial_balance = account.balance
        transaction_amount = transaction.amount
        
        response = client.delete(f'/transactions/api/transactions/{transaction.id}')
        
        assert response.status_code == 200
        
        # Check if transaction was deleted from database
        deleted_transaction = Transaction.query.get(transaction.id)
        assert deleted_transaction is None
        
        # Check if account balance was reverted (expense deletion should increase balance)
        db.session.refresh(account)
        assert account.balance == initial_balance + transaction_amount

    def test_delete_transaction_not_found(self, client, auth_client, user):
        """Test deleting non-existent transaction via API"""
        auth_client.login()
        
        response = client.delete('/transactions/api/transactions/999')
        assert response.status_code == 404

    # API Tests
    def test_api_list_transactions_requires_login(self, client):
        """Test that API transaction list requires authentication"""
        response = client.get('/transactions/api/transactions')
        # API login required returns 401, not 302
        assert response.status_code == 401

    def test_api_list_transactions_authenticated(self, client, auth_client, user, transaction):
        """Test API transaction list for authenticated user"""
        auth_client.login()
        
        response = client.get('/transactions/api/transactions')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'transactions' in data
        assert len(data['transactions']) == 1
        assert data['transactions'][0]['description'] == 'Test transaction'

    def test_api_create_transaction_success(self, client, auth_client, user, account, category_expense):
        """Test successful API transaction creation"""
        auth_client.login()
        
        response = client.post('/transactions/api/transactions', 
                              json={
                                  'amount': 100.00,
                                  'description': 'API transaction',
                                  'account_id': account.id,
                                  'category_id': category_expense.id,
                                  'date': datetime.now().isoformat()
                              })
        
        assert response.status_code == 201
        
        data = response.get_json()
        assert data['amount'] == 100.00
        assert data['description'] == 'API transaction'

    def test_api_create_transaction_validation(self, client, auth_client, user):
        """Test API transaction creation validation"""
        auth_client.login()
        
        # Test missing required fields
        response = client.post('/transactions/api/transactions', 
                              json={'description': 'Invalid transaction'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_api_get_transaction(self, client, auth_client, user, transaction):
        """Test getting a specific transaction via API"""
        auth_client.login()
        
        response = client.get(f'/transactions/api/transactions/{transaction.id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == transaction.id
        assert data['description'] == 'Test transaction'

    def test_api_update_transaction_success(self, client, auth_client, user, transaction, account, category_expense):
        """Test successful API transaction update"""
        auth_client.login()
        
        response = client.put(f'/transactions/api/transactions/{transaction.id}',
                             json={
                                 'amount': 80.00,
                                 'description': 'Updated via API'
                             })
        
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['amount'] == 80.00
        assert data['description'] == 'Updated via API'

    def test_api_delete_transaction_success(self, client, auth_client, user, transaction):
        """Test successful API transaction deletion"""
        auth_client.login()
        
        response = client.delete(f'/transactions/api/transactions/{transaction.id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'message' in data

    def test_api_statistics(self, client, auth_client, user, account, category_income, category_expense):
        """Test API statistics endpoint"""
        # Create some transactions
        
        # Income transaction
        income_transaction = Transaction(
            amount=2000.00,
            description='Salary',
            account_id=account.id,
            category_id=category_income.id,
            user_id=user.id,
            date=datetime.now()
        )
        db.session.add(income_transaction)
        
        # Expense transaction
        expense_transaction = Transaction(
            amount=500.00,
            description='Rent',
            account_id=account.id,
            category_id=category_expense.id,
            user_id=user.id,
            date=datetime.now()
        )
        db.session.add(expense_transaction)
        db.session.commit()
        
        auth_client.login()
        
        response = client.get('/transactions/api/statistics')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'summary' in data
        assert data['summary']['total_income'] == 2000.00
        assert data['summary']['total_expenses'] == 500.00
        assert data['summary']['net_income'] == 1500.00

    def test_transaction_balance_calculations(self, client, auth_client, user, account, category_income, category_expense):
        """Test that transaction operations correctly update account balances via API"""
        auth_client.login()
        initial_balance = account.balance
        
        # Create income transaction via API
        client.post('/transactions/api/transactions', 
                   json={
                       'amount': 1000.00,
                       'description': 'Salary',
                       'account_id': account.id,
                       'category_id': category_income.id,
                       'date': datetime.now().isoformat()
                   })
        
        db.session.refresh(account)
        assert account.balance == initial_balance + 1000.00
        
        # Create expense transaction via API
        client.post('/transactions/api/transactions', 
                   json={
                       'amount': 200.00,
                       'description': 'Groceries',
                       'account_id': account.id,
                       'category_id': category_expense.id,
                       'date': datetime.now().isoformat()
                   })
        
        db.session.refresh(account)
        assert account.balance == initial_balance + 1000.00 - 200.00

    def test_transaction_date_filtering(self, client, auth_client, user, account, category_expense):
        """Test transaction filtering by date range using new time filter"""
        
        # Create transactions with different dates
        old_transaction = Transaction(
            amount=50.00,
            description='Old transaction',
            account_id=account.id,
            category_id=category_expense.id,
            user_id=user.id,
            date=datetime.now() - timedelta(days=60)
        )
        
        recent_transaction = Transaction(
            amount=75.00,
            description='Recent transaction',
            account_id=account.id,
            category_id=category_expense.id,
            user_id=user.id,
            date=datetime.now() - timedelta(days=10)
        )
        
        db.session.add_all([old_transaction, recent_transaction])
        db.session.commit()
        
        auth_client.login()
        
        # Test this month filter (default) - should only show recent transaction
        response = client.get('/transactions/?filter=month')
        assert response.status_code == 200
        assert b'Recent transaction' in response.data
        assert b'Old transaction' not in response.data
        
        # Test this year filter - should show both transactions
        response = client.get('/transactions/?filter=year')
        assert response.status_code == 200
        assert b'Recent transaction' in response.data
        assert b'Old transaction' in response.data
        
        # Test all time filter - should show both transactions
        response = client.get('/transactions/?filter=all')
        assert response.status_code == 200
        assert b'Recent transaction' in response.data
        assert b'Old transaction' in response.data

    def test_custom_date_range_filtering(self, client, auth_client, user, account, category_expense, category_income):
        """Test custom date range filtering functionality"""
        
        # Create transactions with different dates
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Transaction from a week ago
        transaction_week = Transaction(
            amount=100.00,
            description='Week ago transaction',
            date=week_ago,
            user_id=user.id,
            account_id=account.id,
            category_id=category_expense.id
        )
        
        # Transaction from a month ago
        transaction_month = Transaction(
            amount=200.00,
            description='Month ago transaction',
            date=month_ago,
            user_id=user.id,
            account_id=account.id,
            category_id=category_income.id
        )
        
        # Transaction from today
        transaction_today = Transaction(
            amount=50.00,
            description='Today transaction',
            date=today,
            user_id=user.id,
            account_id=account.id,
            category_id=category_expense.id
        )
        
        db.session.add_all([transaction_week, transaction_month, transaction_today])
        db.session.commit()
        
        auth_client.login()
        
        # Test custom date range filtering (last 10 days)
        start_date = (today - timedelta(days=10)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        
        response = client.get(f'/transactions/?filter=custom&start_date={start_date}&end_date={end_date}')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Should include transactions from last week and today
        assert 'Week ago transaction' in response_text
        assert 'Today transaction' in response_text
        # Should NOT include transaction from month ago
        assert 'Month ago transaction' not in response_text
        
        # Check that custom range display name is shown
        start_display = (today - timedelta(days=10)).strftime('%m/%d/%Y')
        end_display = today.strftime('%m/%d/%Y')
        assert f'{start_display} - {end_display}' in response_text
        
        # Test edge case: single day range
        single_date = today.strftime('%Y-%m-%d')
        response = client.get(f'/transactions/?filter=custom&start_date={single_date}&end_date={single_date}')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Should only include today's transaction
        assert 'Today transaction' in response_text
        assert 'Week ago transaction' not in response_text
        assert 'Month ago transaction' not in response_text
        
        # Test that the custom range modal elements are present in the template
        response = client.get('/transactions/')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert 'customDateRangeModal' in response_text
        assert 'Custom Range' in response_text
        assert 'data-filter="custom"' in response_text

    def test_filter_buttons_and_clear_functionality(self, client, auth_client, user, account, category_expense):
        """Test filter application and clear functionality"""
        
        # Create a test transaction
        transaction = Transaction(
            amount=100.00,
            description='Test transaction',
            date=datetime.now().date(),
            user_id=user.id,
            account_id=account.id,
            category_id=category_expense.id
        )
        db.session.add(transaction)
        db.session.commit()
        
        auth_client.login()
        
        # Test that filter page contains the new button labels
        response = client.get('/transactions/')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Check for new button text
        assert 'Apply Filters' in response_text
        assert 'Clear Filters' in response_text
        
        # Test applying filters
        response = client.get(f'/transactions/?category_id={category_expense.id}&search=Test')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert 'Test transaction' in response_text
        
        # Test that clear filters link works (goes back to base URL)
        response = client.get('/transactions/')
        assert response.status_code == 200
        # Should show all transactions without filters

    def test_csv_export_functionality(self, client, auth_client, user, account, category_expense, category_income):
        """Test CSV export functionality"""
        
        # Create test transactions with different properties
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        
        transactions_data = [
            {
                'amount': 100.50,
                'description': 'Test expense transaction',
                'date': today,
                'category': category_expense
            },
            {
                'amount': 250.75,
                'description': 'Test income transaction',
                'date': week_ago,
                'category': category_income
            },
            {
                'amount': 75.25,
                'description': 'Another expense',
                'date': today,
                'category': category_expense
            }
        ]
        
        # Create transactions in database
        for data in transactions_data:
            transaction = Transaction(
                amount=data['amount'],
                description=data['description'],
                date=data['date'],
                user_id=user.id,
                account_id=account.id,
                category_id=data['category'].id
            )
            db.session.add(transaction)
        
        db.session.commit()
        auth_client.login()
        
        # Test basic CSV export (all transactions)
        response = client.get('/transactions/export/csv')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'text/csv; charset=utf-8'
        assert 'attachment' in response.headers['Content-Disposition']
        assert 'transactions_' in response.headers['Content-Disposition']
        assert '.csv' in response.headers['Content-Disposition']
        
        # Check CSV content
        csv_content = response.data.decode('utf-8')
        lines = csv_content.strip().split('\n')
        
        # Check headers (remove any carriage returns for Windows compatibility)
        header_line = lines[0].replace('\r', '')
        assert header_line == 'id,date,description,category,account,amount'
        
        # Check that all transactions are included
        assert 'Test expense transaction' in csv_content
        assert 'Test income transaction' in csv_content
        assert 'Another expense' in csv_content
        assert '100.5' in csv_content
        assert '250.75' in csv_content
        assert '75.25' in csv_content
        
        # Test CSV export with category filter
        response = client.get(f'/transactions/export/csv?category_id={category_expense.id}')
        assert response.status_code == 200
        csv_content = response.data.decode('utf-8')
        
        # Should only include expense transactions
        assert 'Test expense transaction' in csv_content
        assert 'Another expense' in csv_content
        assert 'Test income transaction' not in csv_content
        
        # Test CSV export with search filter
        response = client.get('/transactions/export/csv?search=income')
        assert response.status_code == 200
        csv_content = response.data.decode('utf-8')
        
        # Should only include transactions matching search
        assert 'Test income transaction' in csv_content
        assert 'Test expense transaction' not in csv_content
        
        # Test CSV export with custom date range
        start_date = week_ago.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        response = client.get(f'/transactions/export/csv?filter=custom&start_date={start_date}&end_date={end_date}')
        assert response.status_code == 200
        csv_content = response.data.decode('utf-8')
        
        # Should include all transactions within date range
        assert 'Test expense transaction' in csv_content
        assert 'Test income transaction' in csv_content
        assert 'Another expense' in csv_content

    def test_csv_export_button_presence(self, client, auth_client, user):
        """Test that CSV export button is present in the UI"""
        
        auth_client.login()
        response = client.get('/transactions/')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Check for Export CSV button
        assert 'Export CSV' in response_text
        assert '/transactions/export/csv' in response_text

    def test_transaction_rows_are_clickable(self, client, auth_client, user, account, category_expense):
        """Test that transaction rows are clickable and have proper data attributes"""
        
        # Create a regular transaction to ensure page renders
        transaction = Transaction(
            amount=100.00,
            description='Test transaction',
            date=datetime.now().date(),
            user_id=user.id,
            account_id=account.id,
            category_id=category_expense.id
        )
        db.session.add(transaction)
        db.session.commit()
        
        auth_client.login()
        response = client.get('/transactions/')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Check that transaction rows have proper attributes for being clickable
        assert 'transaction-row' in response_text
        assert 'data-transaction-id' in response_text
        assert 'cursor: pointer' in response_text
        
        # Verify that we no longer have Actions column in the transactions table
        # (Note: "Actions" might appear in "Quick Actions" but not in table headers)
        import re
        table_headers = re.search(r'<thead.*?</thead>', response_text, re.DOTALL)
        if table_headers:
            table_header_text = table_headers.group(0)
            # Count how many times "Actions" appears in table headers specifically
            actions_in_headers = table_header_text.count('Actions')
            assert actions_in_headers == 0, f"Found 'Actions' {actions_in_headers} times in table headers"

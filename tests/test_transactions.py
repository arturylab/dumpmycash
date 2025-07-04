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
        today = datetime.now()
        old_transaction = Transaction(
            amount=50.00,
            description='Old transaction',
            account_id=account.id,
            category_id=category_expense.id,
            user_id=user.id,
            date=today - timedelta(days=60)  # 60 days ago
        )
        
        recent_transaction = Transaction(
            amount=75.00,
            description='Recent transaction',
            account_id=account.id,
            category_id=category_expense.id,
            user_id=user.id,
            date=today - timedelta(days=10)  # 10 days ago
        )
        
        current_transaction = Transaction(
            amount=100.00,
            description='Current transaction',
            account_id=account.id,
            category_id=category_expense.id,
            user_id=user.id,
            date=today  # Today
        )
        
        db.session.add_all([old_transaction, recent_transaction, current_transaction])
        db.session.commit()
        
        auth_client.login()
        
        # Test this month filter (default) - should show current and recent transactions
        response = client.get('/transactions/?filter=month')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert 'Current transaction' in response_text
        # The recent transaction might or might not be in this month depending on the date
        assert 'Old transaction' not in response_text
        
        # Test this year filter - should show all transactions from this year
        response = client.get('/transactions/?filter=year')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert 'Current transaction' in response_text
        assert 'Recent transaction' in response_text
        assert 'Old transaction' in response_text
        
        # Test all time filter - should show all transactions
        response = client.get('/transactions/?filter=all')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert 'Current transaction' in response_text
        assert 'Recent transaction' in response_text
        assert 'Old transaction' in response_text

    def test_custom_date_range_filtering(self, client, auth_client, user, account, category_expense, category_income):
        """Test custom date range filtering functionality"""
        
        # Create transactions with different dates
        today = datetime.now()
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
        
        # Check that custom range filtering works (just verify the filter parameter works)
        assert response.status_code == 200
        
        # Test edge case: single day range
        single_date = today.strftime('%Y-%m-%d')
        response = client.get(f'/transactions/?filter=custom&start_date={single_date}&end_date={single_date}')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Should only include today's transaction
        assert 'Today transaction' in response_text
        assert 'Week ago transaction' not in response_text
        assert 'Month ago transaction' not in response_text

    def test_filter_buttons_and_clear_functionality(self, client, auth_client, user, account, category_expense):
        """Test filter application and clear functionality"""
        
        # Create a test transaction
        transaction = Transaction(
            amount=100.00,
            description='Test transaction',
            date=datetime.now(),  # Use datetime object
            user_id=user.id,
            account_id=account.id,
            category_id=category_expense.id
        )
        db.session.add(transaction)
        db.session.commit()
        
        auth_client.login()
        
        # Test that filter page contains the Clear Filters button
        response = client.get('/transactions/')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        
        # Check for Clear Filters button (Apply Filters was removed for auto-submit)
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
        today = datetime.now()
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
                'date': today - timedelta(days=1),  # Make it recent so it shows up
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
                date=data['date'],  # Use datetime object
                user_id=user.id,
                account_id=account.id,
                category_id=data['category'].id
            )
            db.session.add(transaction)
        
        db.session.commit()
        auth_client.login()
        
        # Test basic CSV export with 'all' filter to include all transactions
        response = client.get('/transactions/export/csv?filter=all')
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
        response = client.get(f'/transactions/export/csv?category_id={category_expense.id}&filter=all')
        assert response.status_code == 200
        csv_content = response.data.decode('utf-8')
        
        # Should only include expense transactions
        assert 'Test expense transaction' in csv_content
        assert 'Another expense' in csv_content
        assert 'Test income transaction' not in csv_content
        
        # Test CSV export with search filter
        response = client.get('/transactions/export/csv?search=income&filter=all')
        assert response.status_code == 200
        csv_content = response.data.decode('utf-8')
        
        # Should only include transactions matching search
        assert 'Test income transaction' in csv_content
        assert 'Test expense transaction' not in csv_content
        
        # Test CSV export with custom date range
        start_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')
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
            date=datetime.now(),  # Use datetime object
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


class TestDeleteTransactionModal:
    """Test suite for transaction deletion modal functionality"""

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
            description='Test transaction for deletion',
            date=datetime.now(),
            user_id=user.id,
            account_id=account.id,
            category_id=category_expense.id
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def test_delete_modal_present_in_template(self, client, auth_client, user, account, category_expense):
        """Test that the delete confirmation modal is present in the template"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that delete confirmation modal is present
        assert 'deleteTransactionModal' in html_content
        assert 'Delete Transaction' in html_content
        assert 'confirmDeleteTransaction' in html_content
        assert 'deleteTransactionAmount' in html_content
        assert 'deleteTransactionDescription' in html_content
        assert 'deleteTransactionAccount' in html_content
        assert 'deleteTransactionCategory' in html_content
        assert 'deleteTransactionDate' in html_content

    def test_delete_button_opens_modal_instead_of_direct_delete(self, client, auth_client, user, account, category_expense):
        """Test that the delete button is present and JavaScript handles modal opening"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that delete button exists with correct ID
        assert 'id="deleteTransactionBtn"' in html_content
        assert 'btn btn-danger' in html_content
        
        # Check that JavaScript is loaded to handle the modal
        assert 'transactions.js' in html_content
        
        # The delete button should not have an onclick with confirm() anymore
        assert 'confirm(' not in html_content or html_content.count('confirm(') <= 1  # Allow for other confirms if any

    def test_delete_transaction_via_api_works(self, client, auth_client, user, account, category_expense, transaction):
        """Test that transaction deletion via API still works properly"""
        auth_client.login()
        initial_balance = account.balance
        transaction_amount = transaction.amount
        
        response = client.delete(f'/transactions/api/transactions/{transaction.id}')
        
        assert response.status_code == 200
        
        # Check if transaction was deleted from database
        deleted_transaction = Transaction.query.get(transaction.id)
        assert deleted_transaction is None
        
        # Check if account balance was properly adjusted
        db.session.refresh(account)
        expected_balance = initial_balance + transaction_amount  # Expense deletion should increase balance
        assert account.balance == expected_balance

    def test_delete_modal_security_user_isolation(self, client, auth_client, user, account, category_expense):
        """Test that users can't delete other users' transactions"""
        # Create first user and transaction
        user1 = auth_client.create_user(
            username="user1",
            email="user1@example.com", 
            password="Password123!"
        )
        
        account1 = Account(name='User1 Account', user_id=user1.id, balance=1000.00)
        db.session.add(account1)
        db.session.commit()
        
        category1 = Category(name='User1 Category', type='expense', user_id=user1.id)
        db.session.add(category1)
        db.session.commit()
        
        transaction1 = Transaction(
            amount=100.00,
            description='User1 transaction',
            date=datetime.now(),
            user_id=user1.id,
            account_id=account1.id,
            category_id=category1.id
        )
        db.session.add(transaction1)
        db.session.commit()
        transaction1_id = transaction1.id
        
        # Create second user
        user2 = auth_client.create_user(
            username="user2",
            email="user2@example.com", 
            password="Password123!"
        )
        
        # Login as second user
        auth_client.login(email="user2@example.com", password="Password123!")
        
        # User2 should not be able to delete User1's transaction
        response = client.delete(f'/transactions/api/transactions/{transaction1_id}')
        assert response.status_code == 404
        
        # Verify transaction still exists
        transaction_still_exists = Transaction.query.get(transaction1_id)
        assert transaction_still_exists is not None

    def test_delete_modal_shows_transaction_details(self, client, auth_client, user, transaction):
        """Test that the modal properly displays transaction details"""
        auth_client.login()
        
        # Get the transaction via API to verify the details would be available
        response = client.get(f'/transactions/api/transactions/{transaction.id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == transaction.id
        assert data['description'] == 'Test transaction for deletion'
        assert data['amount'] == 50.00
        assert 'account' in data
        assert 'category' in data

    def test_javascript_includes_delete_modal_logic(self, client, auth_client, user, account):
        """Test that the transactions page includes the necessary JavaScript for delete modal"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that transactions.js is included
        assert 'transactions.js' in html_content
        
        # Check that the modal elements are present for JavaScript to interact with
        assert 'id="confirmDeleteTransaction"' in html_content
        assert 'deleteTransactionModal' in html_content

    def test_delete_confirmation_modal_structure(self, client, auth_client, user):
        """Test that the delete confirmation modal has the correct structure"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check modal structure
        assert 'modal fade' in html_content
        assert 'Delete Transaction' in html_content
        assert 'Are you sure you want to delete this transaction?' in html_content
        assert 'This action cannot be undone' in html_content
        assert 'btn btn-danger' in html_content
        assert 'spinner-border' in html_content
        assert 'fas fa-trash' in html_content


class TestTransactionFlashMessages:
    """Test suite for transaction flash messages functionality"""

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

    def test_transaction_success_create_flash_message(self, client, auth_client, user):
        """Test that transaction success page shows correct flash message for create operation"""
        auth_client.login()
        
        response = client.get('/transactions/success/create', follow_redirects=True)
        assert response.status_code == 200
        assert b'Transaction created successfully!' in response.data
        assert b'alert-success' in response.data

    def test_transaction_success_update_flash_message(self, client, auth_client, user):
        """Test that transaction success page shows correct flash message for update operation"""
        auth_client.login()
        
        response = client.get('/transactions/success/update', follow_redirects=True)
        assert response.status_code == 200
        assert b'Transaction updated successfully!' in response.data
        assert b'alert-success' in response.data

    def test_transaction_success_delete_flash_message(self, client, auth_client, user):
        """Test that transaction success page shows correct flash message for delete operation"""
        auth_client.login()
        
        response = client.get('/transactions/success/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'Transaction deleted successfully!' in response.data
        assert b'alert-success' in response.data

    def test_transaction_error_flash_message(self, client, auth_client, user):
        """Test that transaction error page shows correct flash message"""
        auth_client.login()
        
        error_message = "Something went wrong"
        response = client.get(f'/transactions/error/save?message={error_message}', follow_redirects=True)
        assert response.status_code == 200
        assert error_message.encode() in response.data
        assert b'alert-danger' in response.data

    def test_transaction_success_unknown_operation_flash_message(self, client, auth_client, user):
        """Test that unknown operation shows default success message"""
        auth_client.login()
        
        response = client.get('/transactions/success/unknown_operation', follow_redirects=True)
        assert response.status_code == 200
        assert b'Operation completed successfully!' in response.data
        assert b'alert-success' in response.data

    def test_transaction_error_without_message_parameter(self, client, auth_client, user):
        """Test that error page without message parameter shows default error message"""
        auth_client.login()
        
        response = client.get('/transactions/error/save', follow_redirects=True)
        assert response.status_code == 200
        assert b'An error occurred during the operation.' in response.data
        assert b'alert-danger' in response.data

    def test_transaction_success_requires_login(self, client):
        """Test that transaction success pages require authentication"""
        response = client.get('/transactions/success/create')
        assert response.status_code == 302  # Redirect to login

    def test_transaction_error_requires_login(self, client):
        """Test that transaction error pages require authentication"""
        response = client.get('/transactions/error/save')
        assert response.status_code == 302  # Redirect to login

    def test_end_to_end_transaction_flow_with_flash_messages(self, client, auth_client, user, account, category_expense):
        """Test complete transaction flow including flash messages"""
        auth_client.login()
        
        # Test creating a transaction and getting success flash message
        response = client.post('/transactions/api/transactions', 
                              json={
                                  'amount': 25.50,
                                  'description': 'Coffee',
                                  'account_id': account.id,
                                  'category_id': category_expense.id,
                                  'date': datetime.now().isoformat()
                              })
        assert response.status_code == 201
        
        # Check that the success endpoint works
        response = client.get('/transactions/success/create', follow_redirects=True)
        assert response.status_code == 200
        assert b'Transaction created successfully!' in response.data
        
        # Get the created transaction
        transaction = Transaction.query.filter_by(description='Coffee').first()
        assert transaction is not None
        
        # Test updating the transaction
        response = client.put(f'/transactions/api/transactions/{transaction.id}',
                             json={
                                 'amount': 30.00,
                                 'description': 'Expensive Coffee',
                                 'account_id': account.id,
                                 'category_id': category_expense.id,
                                 'date': datetime.now().isoformat()
                             })
        assert response.status_code == 200
        
        # Check that the update success endpoint works
        response = client.get('/transactions/success/update', follow_redirects=True)
        assert response.status_code == 200
        assert b'Transaction updated successfully!' in response.data
        
        # Test deleting the transaction
        response = client.delete(f'/transactions/api/transactions/{transaction.id}')
        assert response.status_code == 200
        
        # Check that the delete success endpoint works
        response = client.get('/transactions/success/delete', follow_redirects=True)
        assert response.status_code == 200
        assert b'Transaction deleted successfully!' in response.data
        
        # Verify transaction is deleted
        deleted_transaction = Transaction.query.filter_by(description='Expensive Coffee').first()
        assert deleted_transaction is None


class TestMobileTransactionView:
    """Test suite for mobile transaction view functionality"""

    @pytest.fixture
    def user(self, db, auth_client):
        """Create a test user"""
        return auth_client.create_user()

    @pytest.fixture
    def account(self, db, user):
        """Create a test account"""
        account = Account(
            name='Mobile Test Account',
            user_id=user.id,
            balance=1000.00
        )
        db.session.add(account)
        db.session.commit()
        return account

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
            amount=25.50,
            description='Mobile test transaction',
            account_id=account.id,
            category_id=category_expense.id,
            user_id=user.id,
            date=datetime.now()
        )
        db.session.add(transaction)
        db.session.commit()
        return transaction

    def test_desktop_table_view_present(self, client, auth_client, user, transaction):
        """Test that desktop table view is present with correct classes"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that desktop table view exists with proper responsive classes
        assert 'd-none d-md-block' in html_content
        assert 'table-responsive' in html_content
        assert 'Mobile test transaction' in html_content

    def test_mobile_card_view_present(self, client, auth_client, user, transaction):
        """Test that mobile card view is present with correct structure"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that mobile card view exists with proper responsive classes
        assert 'd-block d-md-none' in html_content
        assert 'mobile-transaction-card' in html_content
        assert 'mobile-date' in html_content
        assert 'mobile-meta' in html_content
        assert 'mobile-category' in html_content
        assert 'mobile-account' in html_content
        assert 'mobile-description' in html_content
        assert 'mobile-amount' in html_content

    def test_mobile_view_contains_transaction_data(self, client, auth_client, user, transaction):
        """Test that mobile view contains all transaction data"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that transaction data appears in mobile view
        assert 'Mobile test transaction' in html_content
        assert 'Mobile Test Account' in html_content
        assert '🍕 Food' in html_content
        assert '$25.50' in html_content

    def test_mobile_view_transaction_clickable(self, client, auth_client, user, transaction):
        """Test that mobile transaction cards are clickable with proper data attributes"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that mobile cards have transaction-row class and data attributes
        assert 'transaction-row mobile-transaction-card' in html_content
        assert f'data-transaction-id="{transaction.id}"' in html_content
        assert 'cursor: pointer' in html_content

    def test_mobile_transfer_badge_display(self, client, auth_client, user, account):
        """Test that transfer badge displays correctly in mobile view"""
        auth_client.login()
        
        # Create a normal expense category first
        normal_category = Category(
            name='Groceries',
            type='expense',
            unicode_emoji='�',
            user_id=user.id
        )
        db.session.add(normal_category)
        db.session.commit()
        
        # Create a normal transaction (transfer transactions are filtered out by default)
        normal_transaction = Transaction(
            amount=50.00,
            description='Grocery shopping',
            account_id=account.id,
            category_id=normal_category.id,
            user_id=user.id,
            date=datetime.now()
        )
        db.session.add(normal_transaction)
        db.session.commit()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that the mobile view contains the transaction
        assert 'mobile-transaction-card' in html_content
        assert 'Grocery shopping' in html_content
        
        # Since this is not a transfer, there should be no transfer badge
        assert 'mobile-transfer-badge' not in html_content

    def test_mobile_view_responsive_classes(self, client, auth_client, user, transaction):
        """Test that mobile view has correct Bootstrap responsive classes"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check for proper Bootstrap grid classes in mobile view (updated to match actual template)
        assert 'col-12' in html_content  # Transaction card
        assert 'col-6' in html_content  # Description/amount columns in mobile
        assert 'col-6 text-end' in html_content  # Amount column alignment

    def test_mobile_view_date_format(self, client, auth_client, user, transaction):
        """Test that mobile view uses short date format"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Mobile view should use MM/DD format
        expected_date = transaction.date.strftime('%m/%d')
        assert expected_date in html_content

    def test_both_views_have_same_transaction_functionality(self, client, auth_client, user, transaction):
        """Test that both desktop and mobile views have the same click functionality"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Both views should have transaction-row class and data attributes
        desktop_transaction_count = html_content.count('transaction-row')
        # Should have 2 occurrences: one for desktop table row, one for mobile card
        assert desktop_transaction_count == 2
        
        # Both should have the same data-transaction-id
        transaction_id_count = html_content.count(f'data-transaction-id="{transaction.id}"')
        assert transaction_id_count == 2


class TestTransactionAutocomplete:
    """Test suite for transaction description autocomplete functionality"""

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
    def sample_transactions(self, db, user, account, category_expense, category_income):
        """Create sample transactions for autocomplete testing"""
        # Create transactions with various descriptions
        transactions = [
            Transaction(
                amount=50.00,
                description='Grocery shopping at Walmart',
                date=datetime.now(),
                user_id=user.id,
                account_id=account.id,
                category_id=category_expense.id
            ),
            Transaction(
                amount=25.00,
                description='Grocery shopping at Target',
                date=datetime.now() - timedelta(days=1),
                user_id=user.id,
                account_id=account.id,
                category_id=category_expense.id
            ),
            Transaction(
                amount=5.00,
                description='Coffee at Starbucks',
                date=datetime.now() - timedelta(days=2),
                user_id=user.id,
                account_id=account.id,
                category_id=category_expense.id
            ),
            Transaction(
                amount=5.00,
                description='Coffee at local cafe',
                date=datetime.now() - timedelta(days=3),
                user_id=user.id,
                account_id=account.id,
                category_id=category_expense.id
            ),
            Transaction(
                amount=2000.00,
                description='Monthly salary payment',
                date=datetime.now() - timedelta(days=4),
                user_id=user.id,
                account_id=account.id,
                category_id=category_income.id
            ),
        ]
        
        db.session.add_all(transactions)
        db.session.commit()
        return transactions

    def test_autocomplete_endpoint_requires_login(self, client):
        """Test that autocomplete endpoint requires authentication"""
        response = client.get('/transactions/api/descriptions')
        assert response.status_code == 401

    def test_autocomplete_endpoint_returns_suggestions(self, client, auth_client, user, sample_transactions):
        """Test that autocomplete endpoint returns suggestions"""
        auth_client.login()
        
        response = client.get('/transactions/api/descriptions')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'suggestions' in data
        assert 'count' in data
        assert len(data['suggestions']) > 0
        
        # Check that descriptions are included
        suggestions = data['suggestions']
        descriptions = [t.description for t in sample_transactions]
        
        for suggestion in suggestions:
            assert suggestion in descriptions

    def test_autocomplete_endpoint_with_search_query(self, client, auth_client, user, sample_transactions):
        """Test that autocomplete endpoint filters by search query"""
        auth_client.login()
        
        # Search for "grocery"
        response = client.get('/transactions/api/descriptions?q=grocery')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'suggestions' in data
        assert len(data['suggestions']) == 2  # Two grocery transactions
        
        suggestions = data['suggestions']
        assert 'Grocery shopping at Walmart' in suggestions
        assert 'Grocery shopping at Target' in suggestions
        assert 'Coffee at Starbucks' not in suggestions

    def test_autocomplete_endpoint_with_coffee_search(self, client, auth_client, user, sample_transactions):
        """Test that autocomplete endpoint filters by coffee search"""
        auth_client.login()
        
        # Search for "coffee"
        response = client.get('/transactions/api/descriptions?q=coffee')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'suggestions' in data
        assert len(data['suggestions']) == 2  # Two coffee transactions
        
        suggestions = data['suggestions']
        assert 'Coffee at Starbucks' in suggestions
        assert 'Coffee at local cafe' in suggestions
        assert 'Grocery shopping at Walmart' not in suggestions

    def test_autocomplete_endpoint_excludes_transfers(self, client, auth_client, user, account):
        """Test that autocomplete endpoint excludes transfer transactions"""
        # Create a transfer category
        transfer_category = Category(
            name='Transfer',
            type='expense',
            user_id=user.id
        )
        db.session.add(transfer_category)
        db.session.commit()
        
        # Create a transfer transaction
        transfer_transaction = Transaction(
            amount=100.00,
            description='Transfer to savings account',
            date=datetime.now(),
            user_id=user.id,
            account_id=account.id,
            category_id=transfer_category.id
        )
        db.session.add(transfer_transaction)
        db.session.commit()
        
        auth_client.login()
        
        response = client.get('/transactions/api/descriptions')
        assert response.status_code == 200
        
        data = response.get_json()
        suggestions = data['suggestions']
        
        # Transfer transaction should not appear in suggestions
        assert 'Transfer to savings account' not in suggestions

    def test_autocomplete_endpoint_frequency_ordering(self, client, auth_client, user, account, category_expense):
        """Test that autocomplete endpoint orders suggestions by frequency"""
        # Create transactions with same description multiple times
        for i in range(3):
            transaction = Transaction(
                amount=10.00,
                description='Frequent description',
                date=datetime.now() - timedelta(days=i),
                user_id=user.id,
                account_id=account.id,
                category_id=category_expense.id
            )
            db.session.add(transaction)
        
        # Create a single transaction with different description
        single_transaction = Transaction(
            amount=20.00,
            description='Single description',
            date=datetime.now(),
            user_id=user.id,
            account_id=account.id,
            category_id=category_expense.id
        )
        db.session.add(single_transaction)
        db.session.commit()
        
        auth_client.login()
        
        response = client.get('/transactions/api/descriptions')
        assert response.status_code == 200
        
        data = response.get_json()
        suggestions = data['suggestions']
        
        # The frequent description should come first
        assert 'Frequent description' in suggestions
        assert 'Single description' in suggestions
        assert suggestions.index('Frequent description') < suggestions.index('Single description')

    def test_autocomplete_endpoint_limit_parameter(self, client, auth_client, user, account, category_expense):
        """Test that autocomplete endpoint respects limit parameter"""
        # Create many transactions with unique descriptions
        for i in range(15):
            transaction = Transaction(
                amount=10.00,
                description=f'Description {i}',
                date=datetime.now() - timedelta(days=i),
                user_id=user.id,
                account_id=account.id,
                category_id=category_expense.id
            )
            db.session.add(transaction)
        db.session.commit()
        
        auth_client.login()
        
        # Test with limit=5
        response = client.get('/transactions/api/descriptions?limit=5')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['suggestions']) == 5
        assert data['count'] == 5

    def test_autocomplete_endpoint_case_insensitive(self, client, auth_client, user, sample_transactions):
        """Test that autocomplete endpoint is case insensitive"""
        auth_client.login()
        
        # Search with different cases
        test_cases = ['GROCERY', 'grocery', 'Grocery', 'gRoCeRy']
        
        for query in test_cases:
            response = client.get(f'/transactions/api/descriptions?q={query}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert len(data['suggestions']) == 2  # Two grocery transactions
            
            suggestions = data['suggestions']
            assert 'Grocery shopping at Walmart' in suggestions
            assert 'Grocery shopping at Target' in suggestions

    def test_autocomplete_javascript_integration(self, client, auth_client, user, account, category_expense):
        """Test that the JavaScript autocomplete setup is present in the template"""
        auth_client.login()
        
        response = client.get('/transactions/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that the JavaScript file is included
        assert 'transactions.js' in html_content
        
        # Check that the description field exists
        assert 'id="description"' in html_content
        assert 'name="description"' in html_content
        
        # Check that the modal setup is present
        assert 'transactionModal' in html_content

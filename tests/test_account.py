import pytest
from flask import url_for
from app.models import User, Account, Transaction, Category, Transfer, db
from datetime import datetime


class TestAccountAccess:
    """Test account endpoints access control."""
    
    def test_account_index_requires_login(self, client):
        """Test that account index redirects to login when not authenticated."""
        response = client.get('/account/')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_account_create_requires_login(self, client):
        """Test that account create redirects to login when not authenticated."""
        response = client.post('/account/create')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_account_edit_requires_login(self, client):
        """Test that account edit redirects to login when not authenticated."""
        response = client.post('/account/edit/1')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_account_delete_requires_login(self, client):
        """Test that account delete redirects to login when not authenticated."""
        response = client.post('/account/delete/1')
        assert response.status_code == 302
        assert '/login' in response.location


class TestAccountAuthenticated:
    """Test account endpoints when user is authenticated."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        """Create and login a user for each test in this class."""
        self.user = auth_client.create_user(
            username="accountuser",
            email="account@example.com", 
            password="Password123!"
        )
        auth_client.login(email="account@example.com", password="Password123!")
    
    def test_account_index_empty(self, client):
        """Test account index with no accounts."""
        response = client.get('/account/')
        assert response.status_code == 200
        assert b"No accounts found" in response.data
        assert b"Add Your First Account" in response.data
    
    def test_account_create_valid(self, client, app):
        """Test creating a valid account."""
        response = client.post('/account/create', data={
            'name': 'Test Checking',
            'balance': '1000.50'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'created successfully!' in response.data
        
        # Verify account was created in database
        with app.app_context():
            account = Account.query.filter_by(name='Test Checking').first()
            assert account is not None
            assert account.balance == 1000.50
    
    def test_account_create_invalid_name(self, client):
        """Test creating account with invalid name."""
        response = client.post('/account/create', data={
            'name': '',
            'balance': '1000.00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Account name is required.' in response.data
    
    def test_account_create_invalid_balance(self, client):
        """Test creating account with invalid balance."""
        response = client.post('/account/create', data={
            'name': 'Test Account',
            'balance': 'invalid'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid balance amount.' in response.data
    
    def test_account_index_with_accounts(self, client, app):
        """Test account index with existing accounts."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='Checking', balance=1000.0, user_id=self.user.id)
            account2 = Account(name='Savings', balance=2000.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
        
        response = client.get('/account/')
        assert response.status_code == 200
        assert b'Checking' in response.data
        assert b'Savings' in response.data
        assert b'$1,000.00' in response.data
        assert b'$2,000.00' in response.data
    
    def test_account_edit_valid(self, client, app):
        """Test editing an existing account."""
        # Create test account
        with app.app_context():
            account = Account(name='Original Name', balance=500.0, user_id=self.user.id)
            db.session.add(account)
            db.session.commit()
            account_id = account.id
        
        response = client.post(f'/account/edit/{account_id}', data={
            'name': 'Updated Name',
            'balance': '750.25'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'updated successfully!' in response.data
        
        # Verify account was updated
        with app.app_context():
            account = Account.query.get(account_id)
            assert account.name == 'Updated Name'
            assert account.balance == 750.25
    
    def test_account_edit_nonexistent(self, client):
        """Test editing a non-existent account."""
        response = client.post('/account/edit/999', data={
            'name': 'Test',
            'balance': '100.00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Account not found.' in response.data
    
    def test_account_delete_valid(self, client, app):
        """Test deleting an existing account."""
        # Create test account
        with app.app_context():
            account = Account(name='To Delete', balance=100.0, user_id=self.user.id)
            db.session.add(account)
            db.session.commit()
            account_id = account.id
        
        response = client.post(f'/account/delete/{account_id}', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'deleted successfully!' in response.data
        
        # Verify account was deleted
        with app.app_context():
            account = Account.query.get(account_id)
            assert account is None
    
    def test_account_delete_nonexistent(self, client):
        """Test deleting a non-existent account."""
        response = client.post('/account/delete/999', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Account not found.' in response.data
    
    def test_account_balance_adjustment_creates_transaction(self, client, app):
        """Test that editing account balance creates a balance adjustment transaction."""
        # Create account with initial balance
        response = client.post('/account/create', data={
            'name': 'Test Account',
            'balance': '1000.00',
            'color': '#FF6384'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            account = Account.query.filter_by(name='Test Account').first()
            assert account is not None
            initial_balance = account.balance
            
            # Verify initial deposit transaction exists
            initial_transactions = Transaction.query.filter_by(account_id=account.id).count()
            assert initial_transactions == 1  # Initial deposit transaction
        
        # Edit account balance to a higher amount (increase)
        new_balance = 1500.00
        response = client.post(f'/account/edit/{account.id}', data={
            'name': 'Test Account',
            'balance': str(new_balance),
            'color': '#FF6384'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Balance adjustment transaction created' in response.data
        
        with app.app_context():
            # Verify account balance was updated
            updated_account = Account.query.get(account.id)
            assert updated_account.balance == new_balance
            
            # Verify adjustment transaction was created
            all_transactions = Transaction.query.filter_by(account_id=account.id).all()
            assert len(all_transactions) == 2  # Initial deposit + balance adjustment
            
            # Find the adjustment transaction
            adjustment_transaction = [tx for tx in all_transactions if 'adjustment' in tx.description.lower()][0]
            assert adjustment_transaction.amount == abs(new_balance - initial_balance)
            assert 'Manual balance adjustment' in adjustment_transaction.description
            assert adjustment_transaction.category.name == 'Balance Adjustment (Increase)'
            assert adjustment_transaction.category.type == 'income'
            assert adjustment_transaction.category.unicode_emoji == '📈'
    
    def test_account_balance_decrease_creates_expense_transaction(self, client, app):
        """Test that decreasing account balance creates an expense transaction."""
        # Create account with initial balance
        response = client.post('/account/create', data={
            'name': 'Test Account Decrease',
            'balance': '1000.00',
            'color': '#FF6384'
        }, follow_redirects=True)
        
        with app.app_context():
            account = Account.query.filter_by(name='Test Account Decrease').first()
            initial_balance = account.balance
        
        # Edit account balance to a lower amount (decrease)
        new_balance = 750.00
        response = client.post(f'/account/edit/{account.id}', data={
            'name': 'Test Account Decrease',
            'balance': str(new_balance),
            'color': '#FF6384'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        with app.app_context():
            # Verify account balance was updated
            updated_account = Account.query.get(account.id)
            assert updated_account.balance == new_balance
            
            # Find the adjustment transaction
            adjustment_transactions = Transaction.query.filter(
                Transaction.account_id == account.id,
                Transaction.description.like('%adjustment%')
            ).all()
            
            assert len(adjustment_transactions) == 1
            adjustment_transaction = adjustment_transactions[0]
            assert adjustment_transaction.amount == abs(new_balance - initial_balance)
            assert adjustment_transaction.category.name == 'Balance Adjustment (Decrease)'
            assert adjustment_transaction.category.type == 'expense'
            assert adjustment_transaction.category.unicode_emoji == '📉'
    
    def test_account_edit_without_balance_change_no_transaction(self, client, app):
        """Test that editing account without changing balance doesn't create adjustment transaction."""
        # Create account
        response = client.post('/account/create', data={
            'name': 'Test Account No Change',
            'balance': '500.00',
            'color': '#FF6384'
        }, follow_redirects=True)
        
        with app.app_context():
            account = Account.query.filter_by(name='Test Account No Change').first()
            initial_transaction_count = Transaction.query.filter_by(account_id=account.id).count()
        
        # Edit account name and color only, keep same balance
        response = client.post(f'/account/edit/{account.id}', data={
            'name': 'Renamed Account',
            'balance': '500.00',
            'color': '#36A2EB'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Balance adjustment transaction created' not in response.data
        
        with app.app_context():
            # Verify no new transactions were created
            final_transaction_count = Transaction.query.filter_by(account_id=account.id).count()
            assert final_transaction_count == initial_transaction_count


class TestAccountAPI:
    """Test account API endpoints."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        """Create and login a user for each test in this class."""
        self.user = auth_client.create_user(
            username="apiuser",
            email="api@example.com", 
            password="Password123!"
        )
        auth_client.login(email="api@example.com", password="Password123!")
    
    def test_api_accounts_empty(self, client):
        """Test API accounts endpoint with no accounts."""
        response = client.get('/account/api/accounts')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_api_accounts_with_data(self, client, app):
        """Test API accounts endpoint with existing accounts."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='API Test 1', balance=100.0, user_id=self.user.id)
            account2 = Account(name='API Test 2', balance=200.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
        
        response = client.get('/account/api/accounts')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Check account data
        account_names = [acc['name'] for acc in data]
        assert 'API Test 1' in account_names
        assert 'API Test 2' in account_names


class TestAccountSecurity:
    """Test account security and isolation."""
    
    def test_user_isolation(self, client, auth_client, app):
        """Test that users can only see their own accounts."""
        # Create first user and account
        user1 = auth_client.create_user(
            username="user1",
            email="user1@example.com", 
            password="Password123!"
        )
        
        with app.app_context():
            account1 = Account(name='User1 Account', balance=1000.0, user_id=user1.id)
            db.session.add(account1)
            db.session.commit()
        
        # Create second user
        user2 = auth_client.create_user(
            username="user2",
            email="user2@example.com", 
            password="Password123!"
        )
        
        # Login as user2
        auth_client.login(email="user2@example.com", password="Password123!")
        
        # User2 should not see User1's accounts
        response = client.get('/account/')
        assert response.status_code == 200
        assert b'User1 Account' not in response.data
        assert b'No accounts found' in response.data
    
    def test_edit_other_user_account(self, client, auth_client, app):
        """Test that users cannot edit other users' accounts."""
        # Create first user and account
        user1 = auth_client.create_user(
            username="owner",
            email="owner@example.com", 
            password="Password123!"
        )
        
        with app.app_context():
            account = Account(name='Protected Account', balance=1000.0, user_id=user1.id)
            db.session.add(account)
            db.session.commit()
            account_id = account.id
        
        # Create second user
        auth_client.create_user(
            username="attacker",
            email="attacker@example.com", 
            password="Password123!"
        )
        
        # Login as second user
        auth_client.login(email="attacker@example.com", password="Password123!")
        
        # Try to edit first user's account
        response = client.post(f'/account/edit/{account_id}', data={
            'name': 'Hacked Account',
            'balance': '0.00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Account not found.' in response.data
        
        # Verify account was not modified
        with app.app_context():
            account = Account.query.get(account_id)
            assert account.name == 'Protected Account'
            assert account.balance == 1000.0


class TestAccountTransfers:
    """Test account transfer functionality."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        """Create and login a user for each test in this class."""
        self.user = auth_client.create_user(
            username="transferuser",
            email="transfer@example.com", 
            password="Password123!"
        )
        auth_client.login(email="transfer@example.com", password="Password123!")
    
    def test_transfer_success(self, client, app):
        """Test successful transfer between accounts."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='Checking', balance=1000.0, user_id=self.user.id)
            account2 = Account(name='Savings', balance=500.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            account1_id = account1.id
            account2_id = account2.id
        
        response = client.post('/account/transfer', data={
            'from_account': account1_id,
            'to_account': account2_id,
            'amount': '200.00',
            'description': 'Test transfer'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Successfully transferred' in response.data
        
        # Verify balances were updated
        with app.app_context():
            account1 = Account.query.get(account1_id)
            account2 = Account.query.get(account2_id)
            assert account1.balance == 800.0
            assert account2.balance == 700.0
    
    def test_transfer_insufficient_funds(self, client, app):
        """Test transfer with insufficient funds."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='Checking', balance=100.0, user_id=self.user.id)
            account2 = Account(name='Savings', balance=500.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            account1_id = account1.id
            account2_id = account2.id
        
        response = client.post('/account/transfer', data={
            'from_account': account1_id,
            'to_account': account2_id,
            'amount': '200.00',
            'description': 'Test transfer'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Insufficient balance' in response.data
        
        # Verify balances were not changed
        with app.app_context():
            account1 = Account.query.get(account1_id)
            account2 = Account.query.get(account2_id)
            assert account1.balance == 100.0
            assert account2.balance == 500.0
    
    def test_transfer_same_account(self, client, app):
        """Test transfer to same account."""
        # Create test account
        with app.app_context():
            account = Account(name='Checking', balance=1000.0, user_id=self.user.id)
            db.session.add(account)
            db.session.commit()
            account_id = account.id
        
        response = client.post('/account/transfer', data={
            'from_account': account_id,
            'to_account': account_id,
            'amount': '200.00',
            'description': 'Test transfer'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Source and destination accounts must be different' in response.data
    
    def test_transfer_invalid_amount(self, client, app):
        """Test transfer with invalid amount."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='Checking', balance=1000.0, user_id=self.user.id)
            account2 = Account(name='Savings', balance=500.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            account1_id = account1.id
            account2_id = account2.id
        
        response = client.post('/account/transfer', data={
            'from_account': account1_id,
            'to_account': account2_id,
            'amount': 'invalid',
            'description': 'Test transfer'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Invalid transfer amount' in response.data


class TestAccountChartAPI:
    """Test account chart data API."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        self.user = auth_client.create_user(
            username="testuser",
            email="test@example.com", 
            password="Password123!"
        )
        auth_client.login(email="test@example.com", password="Password123!")
    
    def test_api_chart_data_empty(self, client):
        """Test chart data API with no accounts."""
        response = client.get('/account/api/chart-data')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['labels'] == []
        assert data['data'] == []
        assert 'backgroundColor' in data
    
    def test_api_chart_data_with_accounts(self, client, app):
        """Test chart data API with existing accounts."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='Chart Test 1', balance=500.0, user_id=self.user.id)
            account2 = Account(name='Chart Test 2', balance=300.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
        
        response = client.get('/account/api/chart-data')
        assert response.status_code == 200
        
        data = response.get_json()
        assert len(data['labels']) == 2
        assert len(data['data']) == 2
        assert 'Chart Test 1' in data['labels']
        assert 'Chart Test 2' in data['labels']
        assert 500.0 in data['data']
        assert 300.0 in data['data']


class TestAccountTransfersAPI:
    """Test account transfers API."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        self.user = auth_client.create_user(
            username="transferuser",
            email="transfer@example.com", 
            password="Password123!"
        )
        auth_client.login(email="transfer@example.com", password="Password123!")
    
    def test_api_recent_transfers_empty(self, client):
        """Test recent transfers API with no transfers."""
        response = client.get('/account/api/recent-transfers')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['count'] == 0
        assert data['data']['transfers'] == []
    
    def test_api_recent_transfers_with_data(self, client, app):
        """Test recent transfers API with existing transfers."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='Source Account', balance=1000.0, user_id=self.user.id)
            account2 = Account(name='Dest Account', balance=500.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            account1_id = account1.id
            account2_id = account2.id
        
        # Make a transfer
        response = client.post('/account/transfer', data={
            'from_account': account1_id,
            'to_account': account2_id,
            'amount': '100.00',
            'description': 'Test transfer'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check recent transfers API
        response = client.get('/account/api/recent-transfers')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['count'] > 0
        assert len(data['data']['transfers']) > 0
        
        # Check transfer data structure
        transfer = data['data']['transfers'][0]
        assert 'description' in transfer
        assert 'amount' in transfer
        assert 'formatted_amount' in transfer
        assert 'date' in transfer
        assert 'formatted_date' in transfer
        assert 'from_account' in transfer
        assert 'to_account' in transfer
        assert transfer['amount'] == 100.0
        assert transfer['description'] == 'Test transfer'
        assert transfer['from_account'] == 'Source Account'
        assert transfer['to_account'] == 'Dest Account'


class TestAccountTransferAJAX:
    """Test account transfer AJAX functionality."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        self.user = auth_client.create_user(
            username="ajaxuser",
            email="ajax@example.com", 
            password="Password123!"
        )
        auth_client.login(email="ajax@example.com", password="Password123!")

    def test_transfer_ajax_success(self, client, app):
        """Test successful transfer via AJAX."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='AJAX Source', balance=1000.0, user_id=self.user.id)
            account2 = Account(name='AJAX Dest', balance=500.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            account1_id = account1.id
            account2_id = account2.id

        # Make AJAX transfer
        response = client.post('/account/transfer',
            data={
                'from_account': account1_id,
                'to_account': account2_id,
                'amount': '100.00',
                'description': 'AJAX transfer'
            },
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'Successfully transferred' in data['message']

        # Verify balances were updated
        with app.app_context():
            updated_account1 = Account.query.get(account1_id)
            updated_account2 = Account.query.get(account2_id)
            assert updated_account1.balance == 900.0
            assert updated_account2.balance == 600.0

            # Verify that NO transfer transactions were created (transfers don't create transactions anymore)
            expense_transactions = Transaction.query.join(Category).filter(
                Transaction.account_id == account1_id,
                Category.type == 'expense',
                Transaction.description.like('Transfer%')
            ).all()

            income_transactions = Transaction.query.join(Category).filter(
                Transaction.account_id == account2_id,
                Category.type == 'income',
                Transaction.description.like('Transfer%')
            ).all()

            # Transfers should NOT create transactions anymore
            assert len(expense_transactions) == 0
            assert len(income_transactions) == 0
            
            # Verify that a Transfer record was created instead
            from app.models import Transfer
            transfer_record = Transfer.query.filter_by(
                from_account_id=account1_id,
                to_account_id=account2_id,
                amount=100.0
            ).first()
            assert transfer_record is not None
            assert transfer_record.description == 'AJAX transfer'
    
    def test_transfer_ajax_error(self, client, app):
        """Test transfer error via AJAX."""
        # Create test account with insufficient funds
        with app.app_context():
            account1 = Account(name='Poor Account', balance=50.0, user_id=self.user.id)
            account2 = Account(name='Rich Account', balance=500.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            account1_id = account1.id
            account2_id = account2.id
        
        # Try AJAX transfer with insufficient funds
        response = client.post('/account/transfer', 
            data={
                'from_account': account1_id,
                'to_account': account2_id,
                'amount': '100.00',
                'description': 'Failed transfer'
            },
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Insufficient balance' in data['message']

    def test_reverse_transfer_success(self, client, app):
        """Test successful transfer reversal via AJAX."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='Source Account', balance=1000.0, user_id=self.user.id)
            account2 = Account(name='Dest Account', balance=500.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            account1_id = account1.id
            account2_id = account2.id
            initial_balance1 = account1.balance
            initial_balance2 = account2.balance

        # Create a transfer first
        response = client.post('/account/transfer', 
            data={
                'from_account': account1_id,
                'to_account': account2_id,
                'amount': '200.00',
                'description': 'Test transfer for reversal'
            },
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        
        # Verify transfer was created
        with app.app_context():
            transfer = Transfer.query.filter_by(user_id=self.user.id).first()
            assert transfer is not None
            assert transfer.amount == 200.0
            transfer_id = transfer.id
            
            # Verify balances changed
            updated_account1 = Account.query.get(account1_id)
            updated_account2 = Account.query.get(account2_id)
            assert updated_account1.balance == initial_balance1 - 200.0
            assert updated_account2.balance == initial_balance2 + 200.0
        
        # Now reverse the transfer
        response = client.post(f'/account/transfer/{transfer_id}/reverse',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'reversed successfully' in data['message']
        
        # Verify transfer and transactions were deleted and balances restored
        with app.app_context():
            transfer_exists = Transfer.query.get(transfer_id) is not None
            assert not transfer_exists
            
            # Verify balances are restored
            final_account1 = Account.query.get(account1_id)
            final_account2 = Account.query.get(account2_id)
            assert abs(final_account1.balance - initial_balance1) < 0.01
            assert abs(final_account2.balance - initial_balance2) < 0.01


class TestAccountColor:
    """Test account color functionality."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        """Create and login a user for each test in this class."""
        self.user = auth_client.create_user(
            username="coloruser",
            email="color@example.com", 
            password="Password123!"
        )
        auth_client.login(email="color@example.com", password="Password123!")
    
    def test_account_create_with_custom_color(self, client, app):
        """Test creating an account with a custom color."""
        response = client.post('/account/create', data={
            'name': 'Custom Color Account',
            'balance': '500.00',
            'color': '#36A2EB'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that account was created with the specified color
        with app.app_context():
            account = Account.query.filter_by(name='Custom Color Account').first()
            assert account is not None
            assert account.color == '#36A2EB'
            assert float(account.balance) == 500.0
    
    def test_account_create_default_color(self, client, app):
        """Test creating an account without specifying color uses default."""
        response = client.post('/account/create', data={
            'name': 'Default Color Account',
            'balance': '100.00'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that account was created with default color
        with app.app_context():
            account = Account.query.filter_by(name='Default Color Account').first()
            assert account is not None
            assert account.color == '#FF6384'  # Default color
    
    def test_account_edit_color(self, client, app):
        """Test editing an account's color."""
        # Create account
        response = client.post('/account/create', data={
            'name': 'Color Change Account',
            'balance': '200.00',
            'color': '#FF6384'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        with app.app_context():
            account = Account.query.filter_by(name='Color Change Account').first()
            account_id = account.id
        
        # Edit account color
        response = client.post(f'/account/edit/{account_id}', data={
            'name': 'Color Change Account',
            'balance': '250.00',
            'color': '#9966FF'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Check that color was updated
        with app.app_context():
            updated_account = Account.query.filter_by(id=account_id).first()
            assert updated_account.color == '#9966FF'
            assert float(updated_account.balance) == 250.0
    
    def test_api_chart_data_uses_account_colors(self, client):
        """Test that chart data API returns account colors."""
        # Create accounts with different colors
        client.post('/account/create', data={
            'name': 'Red Account',
            'balance': '100.00',
            'color': '#FF6B6B'
        })
        
        client.post('/account/create', data={
            'name': 'Blue Account',
            'balance': '200.00',
            'color': '#45B7D1'
        })
        
        response = client.get('/account/api/chart-data')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'labels' in data
        assert 'data' in data
        assert 'backgroundColor' in data
        
        # Check that colors match the accounts
        assert '#FF6B6B' in data['backgroundColor']
        assert '#45B7D1' in data['backgroundColor']
        assert len(data['backgroundColor']) == len(data['labels'])


class TestAccountInitialDeposit:
    """Test account initial deposit functionality."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        """Create and login a user for each test in this class."""
        self.user = auth_client.create_user(
            username="initialuser",
            email="initial@example.com", 
            password="Password123!"
        )
        auth_client.login(email="initial@example.com", password="Password123!")
    
    def test_account_create_with_zero_balance_no_transaction(self, client, app):
        """Test that creating an account with balance 0 does not create an initial deposit transaction."""
        # Create account with zero balance
        response = client.post('/account/create', data={
            'name': 'Zero Balance Account',
            'balance': '0.00',
            'color': '#FF6384'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'created successfully!' in response.data
        
        with app.app_context():
            account = Account.query.filter_by(name='Zero Balance Account').first()
            assert account is not None
            assert account.balance == 0.0
            
            # Verify no transactions were created
            transactions = Transaction.query.filter_by(account_id=account.id).all()
            assert len(transactions) == 0
    
    def test_account_create_with_positive_balance_creates_initial_deposit(self, client, app):
        """Test that creating an account with positive balance creates an initial deposit transaction."""
        initial_balance = 1500.0
        
        # Create account with positive balance
        response = client.post('/account/create', data={
            'name': 'Savings Account',
            'balance': str(initial_balance),
            'color': '#36A2EB'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'created successfully!' in response.data
        
        with app.app_context():
            account = Account.query.filter_by(name='Savings Account').first()
            assert account is not None
            assert account.balance == initial_balance
            
            # Verify initial deposit transaction was created
            transactions = Transaction.query.filter_by(account_id=account.id).all()
            assert len(transactions) == 1
            
            transaction = transactions[0]
            assert transaction.amount == initial_balance
            assert 'Initial deposit' in transaction.description
            assert transaction.user_id == self.user.id
            
            # Verify category is correct
            category = transaction.category
            assert category.name == 'Initial Deposit'
            assert category.type == 'income'
            assert category.unicode_emoji == '💰'
    
    def test_initial_deposit_category_reused_for_multiple_accounts(self, client, app):
        """Test that the Initial Deposit category is reused for multiple accounts."""
        # Create first account
        client.post('/account/create', data={
            'name': 'Account One',
            'balance': '1000.00',
            'color': '#FF6384'
        })
        
        # Create second account
        client.post('/account/create', data={
            'name': 'Account Two',
            'balance': '500.00',
            'color': '#36A2EB'
        })
        
        with app.app_context():
            # Check that only one Initial Deposit category was created
            initial_categories = Category.query.filter_by(
                name='Initial Deposit',
                user_id=self.user.id
            ).all()
            
            assert len(initial_categories) == 1
            category = initial_categories[0]
            
            # Check that both accounts have transactions with this category
            transactions = Transaction.query.filter_by(
                category_id=category.id,
                user_id=self.user.id
            ).all()
            
            assert len(transactions) == 2
            
            # Verify amounts
            amounts = [tx.amount for tx in transactions]
            assert 1000.0 in amounts
            assert 500.0 in amounts
    
class TestReverseTransferModal:
    """Test reverse transfer modal functionality."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        """Create and login a user for each test in this class."""
        self.user = auth_client.create_user(
            username="transferuser",
            email="transfer@example.com", 
            password="Password123!"
        )
        auth_client.login(email="transfer@example.com", password="Password123!")
    
    def test_reverse_transfer_modal_in_template(self, client, app):
        """Test that the reverse transfer modal is present in the account template."""
        # Create test accounts
        with app.app_context():
            account1 = Account(name='Source Account', balance=1000.0, user_id=self.user.id)
            account2 = Account(name='Dest Account', balance=500.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
        
        response = client.get('/account/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that reverse transfer modal is present
        assert 'reverseTransferModal' in html_content
        assert 'Reverse Transfer' in html_content
        assert 'confirmReverseTransfer' in html_content
        assert 'reverseTransferAmount' in html_content
        assert 'reverseTransferFrom' in html_content
        assert 'reverseTransferTo' in html_content
        assert 'reverseTransferDate' in html_content
        assert 'reverseTransferDescription' in html_content
    
    def test_transfer_api_detail_endpoint(self, client, app):
        """Test that transfer detail API endpoint works correctly."""
        # Create test accounts and transfer
        with app.app_context():
            account1 = Account(name='Test From', balance=1000.0, user_id=self.user.id)
            account2 = Account(name='Test To', balance=500.0, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            
            # Create transfer record
            transfer = Transfer(
                amount=200.0,
                description='Test transfer',
                from_account_id=account1.id,
                to_account_id=account2.id,
                user_id=self.user.id,
                date=datetime.now()
            )
            db.session.add(transfer)
            db.session.commit()
            transfer_id = transfer.id
        
        # Test API endpoint
        response = client.get(f'/account/api/transfer/{transfer_id}')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['id'] == transfer_id
        assert data['amount'] == 200.0
        assert data['formatted_amount'] == '$200.00'
        assert data['description'] == 'Test transfer'
        assert data['from_account']['name'] == 'Test From'
        assert data['to_account']['name'] == 'Test To'
        assert 'formatted_date' in data
    
    def test_transfer_api_detail_not_found(self, client):
        """Test transfer detail API with non-existent transfer."""
        response = client.get('/account/api/transfer/99999')
        assert response.status_code == 404
        
        data = response.get_json()
        assert 'error' in data
    
    def test_transfer_api_detail_security(self, client, auth_client, app):
        """Test that users can't access other users' transfer details."""
        # Create first user and transfer
        user1 = auth_client.create_user(
            username="user1",
            email="user1@example.com", 
            password="Password123!"
        )
        
        with app.app_context():
            account1 = Account(name='User1 From', balance=1000.0, user_id=user1.id)
            account2 = Account(name='User1 To', balance=500.0, user_id=user1.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            
            transfer = Transfer(
                amount=100.0,
                description='User1 transfer',
                from_account_id=account1.id,
                to_account_id=account2.id,
                user_id=user1.id,
                date=datetime.now()
            )
            db.session.add(transfer)
            db.session.commit()
            transfer_id = transfer.id
        
        # Create second user and login as them
        auth_client.create_user(
            username="user2",
            email="user2@example.com", 
            password="Password123!"
        )
        auth_client.login(email="user2@example.com", password="Password123!")
        
        # User2 should not be able to access User1's transfer
        response = client.get(f'/account/api/transfer/{transfer_id}')
        assert response.status_code == 404
    
    def test_reverse_transfer_functionality(self, client, app):
        """Test the complete reverse transfer functionality."""
        # Create test accounts
        initial_balance_from = 1000.0
        initial_balance_to = 500.0
        transfer_amount = 200.0
        
        with app.app_context():
            account1 = Account(name='Reverse From', balance=initial_balance_from, user_id=self.user.id)
            account2 = Account(name='Reverse To', balance=initial_balance_to, user_id=self.user.id)
            db.session.add(account1)
            db.session.add(account2)
            db.session.commit()
            account1_id = account1.id
            account2_id = account2.id
        
        # Perform transfer
        response = client.post('/account/transfer', data={
            'from_account': account1_id,
            'to_account': account2_id,
            'amount': str(transfer_amount),
            'description': 'Test reverse transfer'
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        
        # Verify balances after transfer
        with app.app_context():
            account1 = Account.query.get(account1_id)
            account2 = Account.query.get(account2_id)
            assert account1.balance == initial_balance_from - transfer_amount  # 800.0
            assert account2.balance == initial_balance_to + transfer_amount    # 700.0
            
            # Get the transfer for reversal
            transfer = Transfer.query.filter_by(user_id=self.user.id).first()
            assert transfer is not None
            transfer_id = transfer.id
        
        # Reverse the transfer
        response = client.post(f'/account/transfer/{transfer_id}/reverse', 
                             headers={'X-Requested-With': 'XMLHttpRequest'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'reversed successfully' in data['message']
        
        # Verify balances are restored
        with app.app_context():
            account1 = Account.query.get(account1_id)
            account2 = Account.query.get(account2_id)
            assert account1.balance == initial_balance_from  # Back to 1000.0
            assert account2.balance == initial_balance_to    # Back to 500.0
            
            # Verify transfer is deleted
            transfer = Transfer.query.get(transfer_id)
            assert transfer is None
    
    def test_reverse_transfer_nonexistent(self, client):
        """Test reversing a non-existent transfer."""
        response = client.post('/account/transfer/99999/reverse', 
                             headers={'X-Requested-With': 'XMLHttpRequest'})
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'not found' in data['message']
    
    def test_javascript_includes_reverse_modal_logic(self, client, app):
        """Test that the account page includes the necessary JavaScript for reverse modal."""
        with app.app_context():
            account = Account(name='JS Test Account', balance=1000.0, user_id=self.user.id)
            db.session.add(account)
            db.session.commit()
        
        response = client.get('/account/')
        assert response.status_code == 200
        
        html_content = response.get_data(as_text=True)
        
        # Check that account.js is included
        assert 'account.js' in html_content
        
        # Check that the modal elements are present for JavaScript to interact with
        assert 'id="confirmReverseTransfer"' in html_content
        assert 'reverseTransferModal' in html_content
        assert 'Reverse Transfer' in html_content

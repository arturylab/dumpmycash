import pytest
from flask import url_for, session
from app.models import User, Account, Category, Transaction, db
from datetime import datetime, timedelta
import io
import io

class TestProfilePage:
    """Test profile page access and rendering."""
    
    def test_profile_requires_login(self, client):
        """Test that profile page requires login."""
        response = client.get('/profile/')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_profile_authenticated_access(self, client, auth_client):
        """Test that authenticated users can access profile page."""
        auth_client.create_user()
        auth_client.login()
        response = client.get('/profile/')
        assert response.status_code == 200
        assert b'Account Statistics' in response.data
        assert b'Personal Information' in response.data
        assert b'Change Password' in response.data

    def test_profile_contains_user_info(self, client, auth_client):
        """Test that profile page shows user information."""
        auth_client.create_user()
        auth_client.login()
        response = client.get('/profile/')
        assert response.status_code == 200
        assert b'testuser' in response.data
        assert b'test@example.com' in response.data

class TestProfileStatistics:
    """Test profile statistics calculation."""
    
    def test_empty_statistics(self, client, auth_client):
        """Test statistics with no data."""
        auth_client.create_user()
        auth_client.login()
        response = client.get('/profile/api/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['total_transactions'] == 0
        assert data['categories_created'] == 0
        assert data['accounts_managed'] == 0
        assert data['days_active'] >= 0

    def test_statistics_with_data(self, client, auth_client, app):
        """Test statistics with actual data."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            # Create test data
            account = Account(name='Test Account', user_id=user.id, balance=1000.0)
            db.session.add(account)
            db.session.commit()
            
            category = Category(name='Test Category', type='expense', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=100.0,
                description='Test Transaction',
                account_id=account.id,
                category_id=category.id,
                user_id=user.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Test API
            response = client.get('/profile/api/stats')
            assert response.status_code == 200
            data = response.get_json()
            assert data['total_transactions'] == 1
            assert data['categories_created'] == 1
            assert data['accounts_managed'] == 1

    def test_days_active_calculation(self, client, auth_client, app):
        """Test days active calculation."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            # Update user creation date to 10 days ago
            user.created_at = datetime.now() - timedelta(days=10)
            db.session.commit()
            
            response = client.get('/profile/api/stats')
            assert response.status_code == 200
            data = response.get_json()
            assert data['days_active'] == 10

class TestProfileUpdate:
    """Test profile update functionality."""
    
    def test_update_profile_requires_login(self, client):
        """Test that profile update requires login."""
        response = client.post('/profile/update', json={'firstName': 'John', 'lastName': 'Doe'})
        assert response.status_code == 401

    def test_update_profile_success(self, client, auth_client, app):
        """Test successful profile update."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            response = client.post('/profile/update', json={
                'firstName': 'John',
                'lastName': 'Doe'
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'successfully' in data['message']
            
            # Verify database update
            updated_user = User.query.get(user.id)
            assert updated_user.name == 'John Doe'

    def test_update_profile_single_name(self, client, auth_client, app):
        """Test profile update with only first name."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            response = client.post('/profile/update', json={
                'firstName': 'Jane',
                'lastName': ''
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            # Verify database update
            updated_user = User.query.get(user.id)
            assert updated_user.name == 'Jane'

    def test_update_profile_empty_data(self, client, auth_client):
        """Test profile update with empty data."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/update', json={
            'firstName': '',
            'lastName': ''
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

    def test_update_profile_no_data(self, client, auth_client):
        """Test profile update with no JSON data."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/update')
        assert response.status_code == 400

    def test_update_profile_email_only(self, client, auth_client, app):
        """Test profile update with only email."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            response = client.post('/profile/update', json={
                'email': 'newemail@example.com'
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'successfully' in data['message']
            
            # Verify database update
            updated_user = User.query.get(user.id)
            assert updated_user.email == 'newemail@example.com'

    def test_update_profile_email_duplicate(self, client, auth_client, app):
        """Test profile update with duplicate email."""
        with app.app_context():
            # Create first user
            user1 = auth_client.create_user()
            
            # Create second user
            user2 = User(username='testuser2', email='test2@example.com')
            user2.set_password('testpass123')
            db.session.add(user2)
            db.session.commit()
            
            # Login as first user and try to use second user's email
            auth_client.login()
            
            response = client.post('/profile/update', json={
                'email': 'test2@example.com'
            })
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert 'already in use' in data['message']

    def test_update_profile_name_and_email(self, client, auth_client, app):
        """Test profile update with both name and email."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            response = client.post('/profile/update', json={
                'firstName': 'John',
                'lastName': 'Doe',
                'email': 'johndoe@example.com'
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'successfully' in data['message']
            assert 'name' in data
            assert 'email' in data
            
            # Verify database update
            updated_user = User.query.get(user.id)
            assert updated_user.name == 'John Doe'
            assert updated_user.email == 'johndoe@example.com'

class TestPasswordChange:
    """Test password change functionality."""
    
    def test_change_password_requires_login(self, client):
        """Test that password change requires login."""
        response = client.post('/profile/change-password', json={
            'currentPassword': 'test',
            'newPassword': 'newpassword',
            'confirmPassword': 'newpassword'
        })
        assert response.status_code == 401

    def test_change_password_success(self, client, auth_client, app):
        """Test successful password change."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            response = client.post('/profile/change-password', json={
                'currentPassword': 'Password123!',
                'newPassword': 'newpassword123',
                'confirmPassword': 'newpassword123'
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'successfully' in data['message']
            
            # Verify password was changed
            updated_user = User.query.get(user.id)
            assert updated_user.check_password('newpassword123')

    def test_change_password_wrong_current(self, client, auth_client):
        """Test password change with wrong current password."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/change-password', json={
            'currentPassword': 'wrongpassword',
            'newPassword': 'newpassword123',
            'confirmPassword': 'newpassword123'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'incorrect' in data['message']

    def test_change_password_mismatch(self, client, auth_client):
        """Test password change with mismatched new passwords."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/change-password', json={
            'currentPassword': 'Password123!',
            'newPassword': 'newpassword123',
            'confirmPassword': 'differentpassword'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'do not match' in data['message']

    def test_change_password_too_short(self, client, auth_client):
        """Test password change with too short password."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/change-password', json={
            'currentPassword': 'Password123!',
            'newPassword': 'short',
            'confirmPassword': 'short'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert '8 characters' in data['message']

    def test_change_password_missing_fields(self, client, auth_client):
        """Test password change with missing fields."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/change-password', json={
            'currentPassword': 'Password123!',
            'newPassword': '',
            'confirmPassword': 'newpassword123'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

class TestAccountDeletion:
    """Test account deletion functionality."""
    
    def test_delete_account_requires_login(self, client):
        """Test that account deletion requires login."""
        response = client.post('/profile/delete-account', json={'confirmation': 'DELETE'})
        assert response.status_code == 401

    def test_delete_account_success(self, client, auth_client):
        """Test successful account deletion request."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/delete-account', json={
            'confirmation1': 'DELETE ACCOUNT',
            'confirmation2': 'PERMANENTLY DELETE'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'permanently deleted' in data['message']
        assert data.get('logout') is True

    def test_delete_account_wrong_confirmation(self, client, auth_client):
        """Test account deletion with wrong confirmation."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/delete-account', json={
            'confirmation1': 'WRONG',
            'confirmation2': 'PERMANENTLY DELETE'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid first confirmation' in data['message']

    def test_delete_account_no_confirmation(self, client, auth_client):
        """Test account deletion without confirmation."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/delete-account', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

class TestProfilePageTemplate:
    """Test profile page template elements."""
    
    def test_profile_statistics_elements(self, client, auth_client):
        """Test that profile statistics elements are present."""
        auth_client.create_user()
        auth_client.login()
        response = client.get('/profile/')
        assert response.status_code == 200
        assert b'Total Transactions' in response.data
        assert b'Categories Created' in response.data
        assert b'Accounts Managed' in response.data
        assert b'Days Active' in response.data

    def test_profile_forms_present(self, client, auth_client):
        """Test that profile forms are present."""
        auth_client.create_user()
        auth_client.login()
        response = client.get('/profile/')
        assert response.status_code == 200
        assert b'id="profileForm"' in response.data
        assert b'id="passwordForm"' in response.data

    def test_delete_modal_present(self, client, auth_client):
        """Test that delete account modal is present."""
        auth_client.create_user()
        auth_client.login()
        response = client.get('/profile/')
        assert response.status_code == 200
        assert b'deleteAccountModal' in response.data
        assert b'Delete Account' in response.data

    def test_javascript_includes(self, client, auth_client):
        """Test that profile JavaScript is included."""
        auth_client.create_user()
        auth_client.login()
        response = client.get('/profile/')
        assert response.status_code == 200
        assert b'profile.js' in response.data

class TestDataBackupRestore:
    """Test data backup and restore functionality."""
    
    def test_export_data_requires_login(self, client):
        """Test that data export requires login."""
        response = client.get('/profile/export-data')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_export_data_success(self, client, auth_client, app):
        """Test successful data export."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            # Create test data
            account = Account(name='Test Account', user_id=user.id, balance=1000.0)
            db.session.add(account)
            db.session.commit()
            
            category = Category(name='Test Category', type='expense', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=100.0,
                description='Test Transaction',
                account_id=account.id,
                category_id=category.id,
                user_id=user.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Test export
            response = client.get('/profile/export-data')
            assert response.status_code == 200
            assert response.mimetype == 'application/json'
            assert 'attachment' in response.headers.get('Content-Disposition', '')

    def test_restore_data_requires_login(self, client):
        """Test that data restore requires login."""
        response = client.post('/profile/restore-data')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_restore_data_no_file(self, client, auth_client):
        """Test restore data with no file."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/restore-data', data={})
        assert response.status_code == 302  # Redirect to profile page

    def test_restore_data_invalid_json(self, client, auth_client, app):
        """Test restore data with invalid JSON file."""
        with app.app_context():
            auth_client.create_user()
            auth_client.login()
            
            # Create invalid JSON data
            invalid_json = b'{"invalid": json content'
            
            response = client.post('/profile/restore-data', data={
                'backup_file': (io.BytesIO(invalid_json), 'test.json')
            })
            assert response.status_code == 302  # Redirect to profile page

    def test_backup_and_restore_cycle(self, client, auth_client, app):
        """Test complete backup and restore cycle."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            # Create test data
            account = Account(name='Test Account', user_id=user.id, balance=1000.0)
            db.session.add(account)
            db.session.commit()
            
            category = Category(name='Test Category', type='expense', user_id=user.id)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=-50.0,
                description='Test Transaction',
                account_id=account.id,
                category_id=category.id,
                user_id=user.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Get backup data
            from app.profile import get_user_backup_data
            backup_data = get_user_backup_data(user.id)
            
            # Verify backup data structure
            assert 'export_info' in backup_data
            assert 'accounts' in backup_data
            assert 'categories' in backup_data
            assert 'transactions' in backup_data
            assert 'statistics' in backup_data
            
            # Verify data content
            assert len(backup_data['accounts']) == 1
            assert len(backup_data['categories']) == 1
            assert len(backup_data['transactions']) == 1
            assert backup_data['accounts'][0]['name'] == 'Test Account'
            assert backup_data['categories'][0]['name'] == 'Test Category'
            assert backup_data['transactions'][0]['amount'] == -50.0

    def test_validate_backup_data(self, app):
        """Test backup data validation."""
        with app.app_context():
            from app.profile import validate_backup_data
            
            # Valid backup data
            valid_data = {
                'export_info': {},
                'accounts': [],
                'categories': [],
                'transactions': []
            }
            assert validate_backup_data(valid_data) is True
            
            # Invalid backup data (missing keys)
            invalid_data = {
                'export_info': {},
                'accounts': []
            }
            assert validate_backup_data(invalid_data) is False

class TestDataDeletion:
    """Test data deletion functionality."""
    
    def test_delete_all_data_requires_login(self, client):
        """Test that data deletion requires login."""
        response = client.post('/profile/delete-all-data', json={
            'confirmation1': 'DELETE ALL DATA',
            'confirmation2': 'CONFIRM DELETE'
        })
        assert response.status_code == 401

    def test_delete_all_data_success(self, client, auth_client, app):
        """Test successful data deletion."""
        with app.app_context():
            user = auth_client.create_user()
            auth_client.login()
            
            # Create some test data
            from app.models import Account, Category, Transaction
            
            account = Account(name='Test Account', user_id=user.id, balance=1000.0)
            category = Category(name='Test Category', type='expense', user_id=user.id)
            db.session.add(account)
            db.session.add(category)
            db.session.commit()
            
            transaction = Transaction(
                amount=100.0,
                description='Test Transaction',
                account_id=account.id,
                category_id=category.id,
                user_id=user.id
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Verify data exists
            assert Transaction.query.filter_by(user_id=user.id).count() == 1
            assert Account.query.filter_by(user_id=user.id).count() == 1
            assert Category.query.filter_by(user_id=user.id).count() == 1
            
            # Delete all data
            response = client.post('/profile/delete-all-data', json={
                'confirmation1': 'DELETE ALL DATA',
                'confirmation2': 'CONFIRM DELETE'
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'permanently deleted' in data['message']
            
            # Verify data is deleted but user remains
            assert Transaction.query.filter_by(user_id=user.id).count() == 0
            assert Account.query.filter_by(user_id=user.id).count() == 0
            assert Category.query.filter_by(user_id=user.id).count() == 0
            assert User.query.filter_by(id=user.id).count() == 1  # User should still exist

    def test_delete_all_data_wrong_first_confirmation(self, client, auth_client):
        """Test data deletion with wrong first confirmation."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/delete-all-data', json={
            'confirmation1': 'WRONG',
            'confirmation2': 'CONFIRM DELETE'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid first confirmation' in data['message']

    def test_delete_all_data_wrong_second_confirmation(self, client, auth_client):
        """Test data deletion with wrong second confirmation."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/delete-all-data', json={
            'confirmation1': 'DELETE ALL DATA',
            'confirmation2': 'WRONG'
        })
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Invalid second confirmation' in data['message']

    def test_delete_all_data_no_confirmation(self, client, auth_client):
        """Test data deletion without confirmation."""
        auth_client.create_user()
        auth_client.login()
        
        response = client.post('/profile/delete-all-data', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False

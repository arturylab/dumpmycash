import pytest
from flask import url_for
from app.models import User


class TestDashboardAccess:
    """Test that dashboard endpoints require authentication."""
    
    def test_home_requires_login(self, client):
        """Test that home endpoint redirects to login when not authenticated."""
        response = client.get('/home')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_account_requires_login(self, client):
        """Test that account endpoint redirects to login when not authenticated."""
        response = client.get('/account')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_transactions_requires_login(self, client):
        """Test that transactions endpoint redirects to login when not authenticated."""
        response = client.get('/transactions')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_categories_requires_login(self, client):
        """Test that categories endpoint redirects to login when not authenticated."""
        response = client.get('/categories')
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_profile_requires_login(self, client):
        """Test that profile endpoint redirects to login when not authenticated."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.location
    

class TestDashboardAuthenticated:
    """Test dashboard endpoints when user is authenticated."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        """Create and login a user for each test in this class."""
        self.user = auth_client.create_user(
            username="dashboarduser",
            email="dashboard@example.com", 
            password="Password123!"
        )
        auth_client.login(email="dashboard@example.com", password="Password123!")
    
    def test_home_authenticated_access(self, client):
        """Test that authenticated user can access home page."""
        response = client.get('/home', follow_redirects=True)
        assert response.status_code == 200
        assert b"Home" in response.data
        assert b"DumpMyMoney" in response.data
    
    def test_account_authenticated_access(self, client):
        """Test that authenticated user can access account page."""
        response = client.get('/account', follow_redirects=True)
        assert response.status_code == 200
        assert b"Account" in response.data
        assert b"DumpMyMoney" in response.data
    
    def test_transactions_authenticated_access(self, client):
        """Test that authenticated user can access transactions page."""
        response = client.get('/transactions', follow_redirects=True)
        assert response.status_code == 200
        assert b"Transactions" in response.data
        assert b"DumpMyMoney" in response.data
    
    def test_categories_authenticated_access(self, client):
        """Test that authenticated user can access categories page."""
        response = client.get('/categories', follow_redirects=True)
        assert response.status_code == 200
        assert b"Categories" in response.data
        assert b"DumpMyMoney" in response.data
    
    def test_profile_authenticated_access(self, client):
        """Test that authenticated user can access profile page."""
        response = client.get('/profile')
        assert response.status_code == 200
        assert b"Profile" in response.data
        assert b"DumpMyMoney" in response.data


class TestDashboardNavigation:
    """Test navigation and layout in dashboard pages."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        """Create and login a user for each test in this class."""
        self.user = auth_client.create_user(
            username="navuser",
            email="nav@example.com", 
            password="Password123!"
        )
        auth_client.login(email="nav@example.com", password="Password123!")
    
    def test_navigation_present_in_home(self, client):
        """Test that navigation is present in home page."""
        response = client.get('/home', follow_redirects=True)
        assert response.status_code == 200
        assert b"nav-link" in response.data
        assert b"Home" in response.data
        assert b"Account" in response.data
        assert b"Transactions" in response.data
    
    def test_navigation_present_in_account(self, client):
        """Test that navigation is present in account page."""
        response = client.get('/account', follow_redirects=True)
        assert response.status_code == 200
        assert b"nav-link" in response.data
        assert b"Home" in response.data
        assert b"Account" in response.data
        assert b"Transactions" in response.data
    
    def test_active_navigation_home(self, client):
        """Test that home navigation link is active on home page."""
        response = client.get('/home', follow_redirects=True)
        assert response.status_code == 200
        # Check for active class or state in navigation
        assert b"active" in response.data or b"current" in response.data
    
    def test_base_template_extends(self, client):
        """Test that dashboard pages extend from base template."""
        response = client.get('/home', follow_redirects=True)
        assert response.status_code == 200
        # Check for base template elements
        assert b"DumpMyMoney" in response.data
        assert b"navbar" in response.data or b"nav" in response.data
        assert b"footer" in response.data
    
    def test_user_dropdown_present(self, client):
        """Test that user dropdown is present in dashboard pages."""
        response = client.get('/home', follow_redirects=True)
        assert response.status_code == 200
        # Check for user dropdown elements
        assert b"navuser" in response.data or b"nav@example.com" in response.data
        assert b"dropdown" in response.data or b"user-menu" in response.data


class TestDashboardContent:
    """Test specific content in dashboard pages."""
    
    @pytest.fixture(autouse=True)  
    def setup_user(self, auth_client):
        """Create and login a user for each test in this class."""
        self.user = auth_client.create_user(
            username="contentuser",
            email="content@example.com", 
            password="Password123!"
        )
        auth_client.login(email="content@example.com", password="Password123!")
    
    def test_home_page_content(self, client):
        """Test that home page contains expected content."""
        response = client.get('/home', follow_redirects=True)
        assert response.status_code == 200
        assert b"Welcome" in response.data or b"Dashboard" in response.data
        # Check for page-specific content
        assert b"home" in response.data.lower()
    
    def test_account_page_content(self, client):
        """Test that account page contains expected content."""
        response = client.get('/account', follow_redirects=True)
        assert response.status_code == 200
        # Check for account-specific content
        assert b"account" in response.data.lower()
    
    def test_transactions_page_content(self, client):
        """Test that transactions page contains expected content."""
        response = client.get('/transactions', follow_redirects=True)
        assert response.status_code == 200
        # Check for transactions-specific content
        assert b"transaction" in response.data.lower()
    
    def test_categories_page_content(self, client):
        """Test that categories page contains expected content."""
        response = client.get('/categories', follow_redirects=True)
        assert response.status_code == 200
        # Check for categories-specific content
        assert b"categor" in response.data.lower()
    
    def test_profile_page_content(self, client):
        """Test that profile page contains expected content."""
        response = client.get('/profile')
        assert response.status_code == 200
        # Check for profile-specific content
        assert b"profile" in response.data.lower()
        # Should show user information
        assert b"contentuser" in response.data or b"content@example.com" in response.data


class TestDashboardSecurity:
    """Test security aspects of dashboard endpoints."""
    
    def test_csrf_protection_enabled(self, client, auth_client):
        """Test that CSRF protection is enabled for dashboard endpoints."""
        # Create and login user
        auth_client.create_user(
            username="csrfuser",
            email="csrf@example.com", 
            password="Password123!"
        )
        auth_client.login(email="csrf@example.com", password="Password123!")
        
        # All GET requests should work (CSRF not required for GET)
        response = client.get('/home', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that CSRF token is present in forms (if any forms exist)
        if b"<form" in response.data:
            assert b"csrf_token" in response.data or b"_token" in response.data
    
    def test_session_persistence(self, client, auth_client):
        """Test that user session persists across dashboard requests."""
        # Create and login user
        user = auth_client.create_user(
            username="sessionuser",
            email="session@example.com", 
            password="Password123!"
        )
        auth_client.login(email="session@example.com", password="Password123!")
        
        # Make multiple requests to verify session persistence
        response1 = client.get('/home', follow_redirects=True)
        assert response1.status_code == 200
        
        response2 = client.get('/account', follow_redirects=True)
        assert response2.status_code == 200
        
        response3 = client.get('/profile')
        assert response3.status_code == 200
        
        # All should contain user info, confirming session is maintained
        assert b"sessionuser" in response3.data or b"session@example.com" in response3.data
    
    def test_logout_clears_session(self, client, auth_client):
        """Test that logout properly clears session and redirects dashboard access."""
        # Create and login user
        auth_client.create_user(
            username="logoutuser",
            email="logout@example.com", 
            password="Password123!"
        )
        auth_client.login(email="logout@example.com", password="Password123!")
        
        # Verify access works
        response = client.get('/home', follow_redirects=True)
        assert response.status_code == 200
        
        # Logout
        auth_client.logout()
        
        # Verify access is now blocked
        response = client.get('/home')
        assert response.status_code == 302
        assert '/login' in response.location
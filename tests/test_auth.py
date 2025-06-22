import pytest
from flask import g, session, get_flashed_messages
from app.models import User
from app.models import db

# Registration Tests

def test_register_get(client):
    """Test that the registration page loads correctly."""
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Sign Up" in response.data

def test_register_post_success(client, app, auth_client):
    """Test successful user registration."""
    response = auth_client.register(username="newuser", email="new@example.com", password="Password123!")
    
    assert response.status_code == 200
    assert b"Login successful!" not in response.data
    assert b"Registration successful! You can now log in." in response.data

    with app.app_context():
        user = User.query.filter_by(email="new@example.com").first()
        assert user is not None
        assert user.username == "newuser"

def test_register_post_existing_email(client, app, auth_client):
    """Test registration fails with an existing email."""
    auth_client.create_user(username="testuser1", email="existing@example.com", password="Password123!")

    response = auth_client.register(username="newuser", email="existing@example.com", password="Password456!")
    
    assert response.status_code == 200
    assert b"Email already registered." in response.data
    
    with app.app_context():
        user_count = User.query.filter_by(email="existing@example.com").count()
        assert user_count == 1

def test_register_post_existing_username(client, app, auth_client):
    """Test registration fails with an existing username."""
    auth_client.create_user(username="existinguser", email="user1@example.com", password="Password123!")

    response = auth_client.register(username="existinguser", email="newemail@example.com", password="Password456!")
    
    assert response.status_code == 200
    assert b"Username already taken." in response.data

def test_register_password_complexity(client, auth_client):
    """Test registration fails with passwords that don't meet complexity requirements."""
    response = auth_client.register(username="complexuser", email="complex@example.com", password="short")
    assert response.status_code == 200
    assert b"Password must be at least 8 characters long." in response.data

    response = auth_client.register(username="complexuser2", email="complex2@example.com", password="NoNumberOrSymbol")
    assert response.status_code == 200
    assert b"Password must contain at least one digit." in response.data

# Login Tests

def test_login_get(client):
    """Test that the login page loads correctly."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Log in" in response.data

def test_login_success(client, app, auth_client):
    """Test successful user login."""
    auth_client.create_user(username="loginuser", email="login@example.com", password="Password123!")
    
    response = auth_client.login(email="login@example.com", password="Password123!")
    
    assert response.status_code == 200
    assert b"Login successful!" in response.data
    assert b"DumpMyMoney" in response.data

    with client:
        client.get('/')
        assert session.get('user_id') is not None
        user = User.query.get(session['user_id'])
        assert user.email == "login@example.com"
        assert g.user is not None
        assert g.user.email == "login@example.com"

def test_login_invalid_email(client, auth_client):
    """Test login fails with non-existent email."""
    response = auth_client.login(email="notauser@example.com", password="Password123!")
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    with client:
        assert session.get('user_id') is None

def test_login_incorrect_password(client, auth_client):
    """Test login fails with incorrect password."""
    auth_client.create_user(email="userpass@example.com", password="CorrectPassword123!")
    response = auth_client.login(email="userpass@example.com", password="WrongPassword123!")
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    with client:
        assert session.get('user_id') is None

def test_logout(client, auth_client):
    """Test logout functionality."""
    auth_client.create_user(email="logout@example.com", password="Password123!")
    auth_client.login(email="logout@example.com", password="Password123!")

    with client:
        # Make a request to populate the session and g.user
        client.get('/')
        assert session.get('user_id') is not None
        
        response = auth_client.logout()
        assert response.status_code == 200
        assert b"You have been logged out." in response.data
        assert session.get('user_id') is None
        
        # Verify access to protected routes is denied after logout
        account_response = client.get('/home', follow_redirects=True)
        assert b"Log in" in account_response.data
        assert b"You need to be logged in to view this page." in account_response.data

# Username Availability Tests

def test_check_username_available(client):
    """Test /check_username endpoint with an available username."""
    response = client.post('/check_username', json={'username': 'newuniqueuser'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['available'] is True
    assert "Username is available!" in json_data['message']

def test_check_username_taken(client, auth_client):
    """Test /check_username endpoint with a taken username."""
    auth_client.create_user(username="takenuser", email="taken@example.com")
    response = client.post('/check_username', json={'username': 'takenuser'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['available'] is False
    assert "Username already taken." in json_data['message']

def test_check_username_invalid_chars(client):
    """Test /check_username endpoint with invalid characters."""
    response = client.post('/check_username', json={'username': 'user@name'})
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['available'] is False
    assert "Username can only contain letters and numbers." in json_data['message']

# Email Availability Tests

def test_check_email_available(client):
    """Test /check_email endpoint with an available email."""
    response = client.post('/check_email', json={'email': 'available@example.com'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['available'] is True
    assert "Email is available!" in json_data['message']

def test_check_email_taken(client, auth_client):
    """Test /check_email endpoint with an already registered email."""
    auth_client.create_user(email='taken@example.com', username='takenuser', password='Password123!')
    
    response = client.post('/check_email', json={'email': 'taken@example.com'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['available'] is False
    assert "Email already registered." in json_data['message']

def test_check_email_invalid_format(client):
    """Test /check_email endpoint with invalid email formats."""
    invalid_emails = [
        'invalid-email',  # Missing @ symbol
        'invalid@',       # Missing domain
        'user@domain',    # Missing TLD
        'user@.com',      # Missing domain name
        'user@domain.c',  # TLD too short
        '',               # Empty email
    ]
    
    for email in invalid_emails:
        response = client.post('/check_email', json={'email': email})
        json_data = response.get_json()
        assert json_data['available'] is False
        
        if email == '':
            assert response.status_code == 400
            assert "Email cannot be empty." in json_data['message']
        else:
            assert response.status_code == 200
            assert "Invalid email format." in json_data['message']
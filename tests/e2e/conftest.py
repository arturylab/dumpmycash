import pytest
import sys
import os
import threading
import time
import requests
import socket
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from werkzeug.serving import make_server

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from app.models import db as _db
from app.models import User
from app.config import TestConfig


class TestConfigSelenium(TestConfig):
    """Configuration for Selenium tests with a different database"""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_selenium.db'
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
    TESTING = True


@pytest.fixture(scope='session')
def selenium_app():
    """Create and configure a new app instance for each test session."""
    flask_app = create_app(TestConfigSelenium)

    with flask_app.app_context():
        _db.create_all()

    yield flask_app

    with flask_app.app_context():
        _db.drop_all()


def wait_for_server(url, timeout=30):
    """Wait for server to be ready by making HTTP requests."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code < 500:  # Server is responding
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
    return False


def find_free_port():
    """Find a free port to use for the test server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        port = s.getsockname()[1]
    return port


@pytest.fixture(scope='session')
def live_server_flask(selenium_app):
    """Start a live Flask server for Selenium tests."""
    port = find_free_port()
    
    # Create a Werkzeug server
    server = make_server('127.0.0.1', port, selenium_app, threaded=True)
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Wait for the server to start
    server_url = f"http://127.0.0.1:{port}"
    if not wait_for_server(server_url):
        server.shutdown()
        raise RuntimeError("Failed to start test server")
    
    yield server_url
    
    # Cleanup
    server.shutdown()


@pytest.fixture(scope='function')
def selenium_db(selenium_app):
    """Provides the database instance and handles cleanup for each test function."""
    with selenium_app.app_context():
        pass

    yield _db

    with selenium_app.app_context():
        meta = _db.metadata
        for table in reversed(meta.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture(scope='function')
def driver():
    """Create a Chrome WebDriver instance for Selenium tests."""
    # Configure Chrome options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comentado para modo visible
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--disable-gpu")  # Comentado para modo visible
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    # Opciones adicionales para modo visible
    chrome_options.add_argument("--start-maximized")  # Maximizar ventana
    chrome_options.add_experimental_option("detach", True)  # Mantener navegador abierto al finalizar debug
    
    # Use webdriver-manager to get the ChromeDriver
    service = Service(ChromeDriverManager().install())
    
    # Create the WebDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Set implicit wait
    driver.implicitly_wait(10)
    
    yield driver
    
    # Cleanup
    driver.quit()


@pytest.fixture(scope='function')
def driver_headless():
    """Create a Chrome WebDriver instance for Selenium tests in headless mode."""
    # Configure Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    
    # Use webdriver-manager to get the ChromeDriver
    service = Service(ChromeDriverManager().install())
    
    # Create the WebDriver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Set implicit wait
    driver.implicitly_wait(10)
    
    yield driver
    
    # Cleanup
    driver.quit()


@pytest.fixture
def auth_helper(driver, live_server_flask, selenium_db):
    """Helper class for authentication-related actions in Selenium tests."""
    class AuthHelper:
        def __init__(self, driver, base_url, db_session):
            self.driver = driver
            self.base_url = base_url
            self.db = db_session

        def create_user(self, username="testuser", email="test@example.com", password="Password123!"):
            """Create a user directly in the database."""
            from app import create_app
            app = create_app(TestConfigSelenium)
            with app.app_context():
                user = User(username=username, email=email)
                user.set_password(password)
                self.db.session.add(user)
                self.db.session.commit()
                return user

        def navigate_to_login(self):
            """Navigate to the login page."""
            self.driver.get(f"{self.base_url}/login")
            return self.driver

        def navigate_to_register(self):
            """Navigate to the register page."""
            self.driver.get(f"{self.base_url}/register")
            return self.driver

        def wait_for_page_load(self, timeout=10):
            """Wait for page to load completely."""
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

        def is_logged_in(self):
            """Check if user is logged in by looking for logout button or dashboard elements."""
            try:
                # Look for elements that would indicate a logged-in state
                logout_buttons = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/logout') or contains(text(), 'Logout')]")
                dashboard_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/dashboard') or contains(@href, '/home')]")
                return len(logout_buttons) > 0 or len(dashboard_elements) > 0
            except:
                return False

        def get_flash_messages(self):
            """Get all flash messages from the page."""
            try:
                flash_elements = self.driver.find_elements(By.CSS_SELECTOR, ".alert, .flash-message")
                return [element.text for element in flash_elements]
            except:
                return []

    return AuthHelper(driver, live_server_flask, _db)
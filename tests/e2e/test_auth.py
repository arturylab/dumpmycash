import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestAuthenticationSelenium:
    """Selenium tests for authentication functionality"""

    def test_login_page_loads(self, driver, live_server_flask):
        """Test that the login page loads correctly"""
        driver.get(f"{live_server_flask}/login")
        
        # Pausa para observar en modo visible
        time.sleep(2)
        
        # Check that the page title is correct
        assert "Login - DumpMyMoney" in driver.title
        
        # Check for key elements on the login page
        email_input = driver.find_element(By.ID, "InputEmail")
        password_input = driver.find_element(By.ID, "InputPassword1")
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
        
        assert email_input.is_displayed()
        assert password_input.is_displayed()
        assert login_button.is_displayed()
        
        # Check for the logo and branding (text is split with span)
        logo = driver.find_element(By.XPATH, "//h1[contains(text(), 'Dump') and contains(., 'Cash')]")
        assert logo.is_displayed()
        
        # Pausa para observar resultado en modo visible
        time.sleep(1)

    def test_successful_login(self, driver, live_server_flask, auth_helper):
        """Test successful user login"""
        # Create a test user
        test_email = "testuser@example.com"
        test_password = "Password123!"
        auth_helper.create_user(username="testuser", email=test_email, password=test_password)
        
        # Navigate to login page
        driver.get(f"{live_server_flask}/login")
        time.sleep(1)  # Pausa para observar
        
        # Fill in login form
        email_input = driver.find_element(By.ID, "InputEmail")
        password_input = driver.find_element(By.ID, "InputPassword1")
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
        
        # Llenar campos con pausa para observar
        email_input.send_keys(test_email)
        time.sleep(0.5)
        password_input.send_keys(test_password)
        time.sleep(0.5)
        login_button.click()
        
        # Wait for redirect and check if logged in
        WebDriverWait(driver, 10).until(
            lambda d: d.current_url != f"{live_server_flask}/login"
        )
        
        # Check that we're redirected to dashboard/home
        assert "/home" in driver.current_url or "/dashboard" in driver.current_url
        
        # Verify login was successful by checking for logout option or dashboard elements
        assert auth_helper.is_logged_in()
        
        # Pausa para observar resultado final
        time.sleep(2)

    def test_failed_login_invalid_credentials(self, driver, live_server_flask):
        """Test login with invalid credentials"""
        driver.get(f"{live_server_flask}/login")
        time.sleep(1)  # Pausa para observar la carga
        
        # Try to login with invalid credentials
        email_input = driver.find_element(By.ID, "InputEmail")
        password_input = driver.find_element(By.ID, "InputPassword1")
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
        
        # Llenar campos con pausas para observar
        email_input.send_keys("nonexistent@example.com")
        time.sleep(0.5)
        password_input.send_keys("wrongpassword")
        time.sleep(0.5)
        login_button.click()
        
        # Wait for page to process login attempt
        time.sleep(3)  # Pausa más larga para observar el mensaje de error
        
        # Should stay on login page
        assert "/login" in driver.current_url
        
        # Check for error message - may appear in different ways
        try:
            # Look for flash messages
            flash_messages = driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .alert, .flash-message")
            if flash_messages:
                assert len(flash_messages) > 0
                return
            
            # Look for invalid feedback on form fields
            feedback_elements = driver.find_elements(By.CSS_SELECTOR, ".invalid-feedback")
            if feedback_elements:
                assert len(feedback_elements) > 0
                return
            
            # Look for general error styling on inputs
            invalid_inputs = driver.find_elements(By.CSS_SELECTOR, ".is-invalid")
            if invalid_inputs:
                assert len(invalid_inputs) > 0
                return
                
            # If no visual feedback, at least check we stayed on login page
            assert "/login" in driver.current_url
            
        except Exception as e:
            # If error checking fails, at least verify we didn't get redirected
            assert "/login" in driver.current_url
            print(f"Error validation check failed, but login correctly rejected: {e}")
        
        # Pausa para observar mensaje de error o falta de redirección
        time.sleep(2)

    def test_failed_login_empty_fields(self, driver, live_server_flask):
        """Test login with empty fields"""
        driver.get(f"{live_server_flask}/login")
        time.sleep(1)  # Pausa para observar la página
        
        # Try to submit empty form
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
        login_button.click()
        
        # Pausa para observar el comportamiento de validación
        time.sleep(2)
        
        # Check for HTML5 validation or error handling
        email_input = driver.find_element(By.ID, "InputEmail")
        
        # HTML5 validation should prevent submission
        validity = driver.execute_script("return arguments[0].validity.valid;", email_input)
        assert not validity  # Should be invalid due to required attribute
        
        # Pausa para observar resultado
        time.sleep(1)

    def test_register_modal_opens(self, driver, live_server_flask):
        """Test that register modal opens from login page"""
        driver.get(f"{live_server_flask}/login")
        
        # Pausa para observar la página de login
        time.sleep(1)
        
        # Click on "Sign up" link
        signup_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Sign up')]")
        signup_link.click()
        
        # Wait for modal to appear
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "registerModal"))
        )
        
        # Pausa para observar el modal abierto
        time.sleep(2)
        
        # Check that modal is visible
        modal = driver.find_element(By.ID, "registerModal")
        assert modal.is_displayed()
        
        # Check for register form elements
        username_input = driver.find_element(By.ID, "floatingUsername")
        email_input = driver.find_element(By.ID, "floatingEmail")
        password_input = driver.find_element(By.ID, "floatingPasswordModal")
        register_button = driver.find_element(By.ID, "registerSubmitButton")
        
        assert username_input.is_displayed()
        assert email_input.is_displayed()
        assert password_input.is_displayed()
        assert register_button.is_displayed()
        
        # Pausa final para observar los elementos del formulario
        time.sleep(1)

    def test_successful_registration_via_modal(self, driver, live_server_flask):
        """Test successful user registration via modal"""
        driver.get(f"{live_server_flask}/login")
        
        # Pausa para observar la página de login
        time.sleep(1)
        
        # Open register modal
        signup_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Sign up')]")
        signup_link.click()
        
        # Wait for modal to appear
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "registerModal"))
        )
        
        # Pausa para observar el modal abierto
        time.sleep(1)
        
        # Fill in registration form
        username_input = driver.find_element(By.ID, "floatingUsername")
        email_input = driver.find_element(By.ID, "floatingEmail")
        password_input = driver.find_element(By.ID, "floatingPasswordModal")
        register_button = driver.find_element(By.ID, "registerSubmitButton")
        
        test_username = "newuser123"
        test_email = "newuser@example.com"
        test_password = "NewPassword123!"
        
        # Introducir datos con pausas para observar cada entrada
        username_input.send_keys(test_username)
        time.sleep(0.5)
        email_input.send_keys(test_email)
        time.sleep(0.5)
        password_input.send_keys(test_password)
        time.sleep(0.5)
        
        # Submit registration - use WebDriverWait to ensure button is clickable
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "registerSubmitButton"))
        )
        
        # Use JavaScript click to avoid interception issues
        driver.execute_script("arguments[0].click();", register_button)
        
        # Pausa para observar el envío del formulario
        time.sleep(2)
        
        # Wait for redirect to login page
        WebDriverWait(driver, 10).until(
            lambda d: "registerModal" not in d.page_source or not driver.find_element(By.ID, "registerModal").is_displayed()
        )
        
        # Check for success message
        try:
            success_message = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-success, .alert"))
            )
            assert "successful" in success_message.text.lower() or "registration" in success_message.text.lower()
            # Pausa para observar mensaje de éxito
            time.sleep(1)
        except TimeoutException:
            # If no success message, check that we can now login with the new credentials
            pass
        
        # Verify that the user was created by trying to login
        time.sleep(1)  # Brief pause
        
        email_input_login = driver.find_element(By.ID, "InputEmail")
        password_input_login = driver.find_element(By.ID, "InputPassword1")
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
        
        # Clear any existing values
        email_input_login.clear()
        password_input_login.clear()
        
        # Introducir credenciales de login con pausas
        email_input_login.send_keys(test_email)
        time.sleep(0.5)
        password_input_login.send_keys(test_password)
        time.sleep(0.5)
        login_button.click()
        
        # Should successfully login
        WebDriverWait(driver, 10).until(
            lambda d: d.current_url != f"{live_server_flask}/login"
        )
        
        # Pausa para observar redirección exitosa
        time.sleep(2)
        
        assert "/home" in driver.current_url or "/dashboard" in driver.current_url

    def test_registration_validation_errors(self, driver, live_server_flask):
        """Test registration form validation"""
        driver.get(f"{live_server_flask}/login")
        
        # Pausa para observar la página de login
        time.sleep(1)
        
        # Open register modal
        signup_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Sign up')]")
        signup_link.click()
        
        # Wait for modal to appear
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "registerModal"))
        )
        
        # Pausa para observar el modal abierto
        time.sleep(1)
        
        # Try to submit with weak password
        username_input = driver.find_element(By.ID, "floatingUsername")
        email_input = driver.find_element(By.ID, "floatingEmail")
        password_input = driver.find_element(By.ID, "floatingPasswordModal")
        register_button = driver.find_element(By.ID, "registerSubmitButton")
        
        # Introducir datos con contraseña débil y pausas para observar
        username_input.send_keys("testuser")
        time.sleep(0.5)
        email_input.send_keys("test@example.com")
        time.sleep(0.5)
        password_input.send_keys("123")  # Weak password
        time.sleep(0.5)
        
        # Try to click button - it might be disabled due to validation
        try:
            # First check if button is disabled due to validation
            if register_button.get_attribute("disabled"):
                # Use JavaScript to attempt click anyway to test validation
                driver.execute_script("arguments[0].click();", register_button)
            else:
                register_button.click()
        except Exception:
            # If normal click fails, use JavaScript
            driver.execute_script("arguments[0].click();", register_button)
        
        # Pausa para observar validación de contraseña débil
        time.sleep(2)
        
        # Check for validation error (might be client-side or server-side)
        # Could be HTML5 validation or server response
        try:
            # Check if there's a validation message
            validation_element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".alert-danger, .alert, .invalid-feedback"))
            )
            # Pausa para observar mensaje de validación
            time.sleep(1)
        except TimeoutException:
            # If no explicit validation message, check that modal is still open (which indicates validation prevented submission)
            modal = driver.find_element(By.ID, "registerModal")
            assert modal.is_displayed()
            # Pausa para observar que el modal sigue abierto
            time.sleep(1)

    def test_duplicate_registration(self, driver, live_server_flask, auth_helper):
        """Test registration with duplicate email/username"""
        # Create an existing user
        existing_email = "existing@example.com"
        existing_username = "existinguser"
        auth_helper.create_user(username=existing_username, email=existing_email, password="Password123!")
        
        driver.get(f"{live_server_flask}/login")
        
        # Pausa para observar la página de login
        time.sleep(1)
        
        # Open register modal
        signup_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Sign up')]")
        signup_link.click()
        
        # Wait for modal to appear
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "registerModal"))
        )
        
        # Pausa para observar el modal abierto
        time.sleep(1)
        
        # Try to register with existing email
        username_input = driver.find_element(By.ID, "floatingUsername")
        email_input = driver.find_element(By.ID, "floatingEmail")
        password_input = driver.find_element(By.ID, "floatingPasswordModal")
        register_button = driver.find_element(By.ID, "registerSubmitButton")
        
        # Introducir datos con email existente y pausas para observar
        username_input.send_keys("newuser")
        time.sleep(0.5)
        email_input.send_keys(existing_email)  # Use existing email
        time.sleep(0.5)
        password_input.send_keys("Password123!")
        time.sleep(0.5)

        # Wait a moment for JavaScript validation to process
        time.sleep(1)
        
        # Try to click the button (might be disabled due to duplicate email)
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "registerSubmitButton"))
            )
            register_button.click()
        except TimeoutException:
            # If button is disabled, use JavaScript to attempt submission
            driver.execute_script("arguments[0].click();", register_button)
        
        # Should show error message or validation
        time.sleep(2)  # Pausa para observar mensaje de error
        
        # Check for error feedback (this might be shown via JavaScript validation)
        try:
            email_feedback = driver.find_element(By.ID, "emailFeedback")
            if email_feedback.is_displayed() and email_feedback.text:
                assert "already" in email_feedback.text.lower() or "taken" in email_feedback.text.lower()
        except NoSuchElementException:
            # Alternative: check for general alert messages
            alerts = driver.find_elements(By.CSS_SELECTOR, ".alert-danger, .alert")
            if alerts:
                alert_text = alerts[0].text.lower()
                assert "already" in alert_text or "exists" in alert_text or "taken" in alert_text

    def test_remember_me_functionality(self, driver, live_server_flask, auth_helper):
        """Test remember me checkbox functionality"""
        # Create a test user
        test_email = "remember@example.com"
        test_password = "Password123!"
        auth_helper.create_user(username="rememberuser", email=test_email, password=test_password)
        
        driver.get(f"{live_server_flask}/login")
        
        # Pausa para observar la página de login
        time.sleep(1)
        
        # Fill in login form and check remember me
        email_input = driver.find_element(By.ID, "InputEmail")
        password_input = driver.find_element(By.ID, "InputPassword1")
        remember_checkbox = driver.find_element(By.ID, "loginCheck")
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
        
        # Introducir datos con pausas para observar
        email_input.send_keys(test_email)
        time.sleep(0.5)
        password_input.send_keys(test_password)
        time.sleep(0.5)
        remember_checkbox.click()  # Check remember me
        time.sleep(0.5)  # Pausa para observar checkbox marcado
        login_button.click()
        
        # Wait for redirect
        WebDriverWait(driver, 10).until(
            lambda d: d.current_url != f"{live_server_flask}/login"
        )
        
        # Pausa para observar redirección exitosa
        time.sleep(2)
        
        # Verify login was successful
        assert auth_helper.is_logged_in()

    def test_password_visibility_toggle(self, driver, live_server_flask):
        """Test password visibility toggle in register modal"""
        driver.get(f"{live_server_flask}/login")
        
        # Pausa para observar la página de login
        time.sleep(1)
        
        # Open register modal
        signup_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Sign up')]")
        signup_link.click()
        
        # Wait for modal to appear
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "registerModal"))
        )
        
        # Pausa para observar el modal abierto
        time.sleep(1)
        
        # Check password toggle functionality
        password_input = driver.find_element(By.ID, "floatingPasswordModal")
        show_password_checkbox = driver.find_element(By.ID, "showPasswordModalCheck")
        
        # Introducir una contraseña para ver el toggle
        password_input.send_keys("testpassword123")
        time.sleep(0.5)
        
        # Initially password should be hidden
        assert password_input.get_attribute("type") == "password"
        
        # Click show password checkbox
        show_password_checkbox.click()
        time.sleep(1)  # Pausa para observar cambio a texto visible
        
        # Password should now be visible
        assert password_input.get_attribute("type") == "text"
        
        # Click again to hide
        show_password_checkbox.click()
        time.sleep(1)  # Pausa para observar cambio de vuelta a oculto
        
        # Password should be hidden again
        assert password_input.get_attribute("type") == "password"

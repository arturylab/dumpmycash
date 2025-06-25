/**
 * Login page functionality
 * Handles client-side logic for the login form
 */
document.addEventListener('DOMContentLoaded', function () {
  // Login form elements
  const loginForm = document.querySelector('form[action*="login"]');
  const emailInput = document.getElementById('InputEmail');
  const passwordInput = document.getElementById('InputPassword1');
  const rememberCheckbox = document.getElementById('loginCheck');

  // Focus on email input if it's empty
  if (emailInput && !emailInput.value.trim()) {
    emailInput.focus();
  }

  // Basic form validation
  if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
      const email = emailInput?.value.trim();
      const password = passwordInput?.value;

      if (!email || !password) {
        event.preventDefault();
        
        // Show validation messages
        if (!email && emailInput) {
          emailInput.classList.add('is-invalid');
        }
        if (!password && passwordInput) {
          passwordInput.classList.add('is-invalid');
        }
        
        return false;
      }

      // Clear any previous validation states
      if (emailInput) emailInput.classList.remove('is-invalid');
      if (passwordInput) passwordInput.classList.remove('is-invalid');
    });
  }

  // Clear validation states on input
  if (emailInput) {
    emailInput.addEventListener('input', function() {
      this.classList.remove('is-invalid');
    });
  }

  if (passwordInput) {
    passwordInput.addEventListener('input', function() {
      this.classList.remove('is-invalid');
    });
  }

  // Handle Enter key on form fields
  [emailInput, passwordInput].forEach(input => {
    if (input) {
      input.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
          const submitButton = loginForm?.querySelector('button[type="submit"]');
          if (submitButton) {
            submitButton.click();
          }
        }
      });
    }
  });
});
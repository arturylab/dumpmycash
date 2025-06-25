/**
 * Registration form validation and modal handling
 * Provides real-time validation for username, email, and password fields
 */
document.addEventListener('DOMContentLoaded', function () {
  // Configuration constants
  const CONFIG = {
    debounceDelays: {
      username: 500,
      email: 500,
      password: 300
    },
    minLength: {
      username: 3,
      email: 3,
      password: 8
    },
    passwordPattern: {
      letter: /[a-zA-Z]/,
      digit: /\d/,
      special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]/
    }
  };

  // DOM elements
  const elements = {
    modal: document.getElementById('registerModal'),
    passwordToggle: document.getElementById('showPasswordModalCheck'),
    passwordInput: document.getElementById('floatingPasswordModal'),
    usernameInput: document.getElementById('floatingUsername'),
    emailInput: document.getElementById('floatingEmail'),
    usernameFeedback: document.getElementById('usernameFeedback'),
    emailFeedback: document.getElementById('emailFeedback'),
    passwordFeedback: document.getElementById('passwordFeedback'),
    submitButton: document.getElementById('registerSubmitButton')
  };

  // Validation state
  const validationState = {
    username: false,
    email: false,
    password: false
  };

  // Initialize modal
  let modalInstance;
  if (elements.modal) {
    modalInstance = new bootstrap.Modal(elements.modal);
    if (window.openRegisterModal === true) {
      modalInstance.show();
    }
  }

  // Initialize password toggle
  if (elements.passwordToggle && elements.passwordInput) {
    elements.passwordToggle.addEventListener('change', function () {
      elements.passwordInput.type = this.checked ? 'text' : 'password';
    });
  }

  /**
   * Validates password complexity based on predefined rules
   * @param {string} password - The password to validate
   * @returns {object} Validation result with isValid flag and feedback messages
   */
  function validatePasswordComplexity(password) {
    const feedbackMessages = [];
    
    if (password.length < CONFIG.minLength.password) {
      feedbackMessages.push("At least 8 characters");
    }
    if (!CONFIG.passwordPattern.letter.test(password)) {
      feedbackMessages.push("At least one letter (a-z, A-Z)");
    }
    if (!CONFIG.passwordPattern.digit.test(password)) {
      feedbackMessages.push("At least one number (0-9)");
    }
    if (!CONFIG.passwordPattern.special.test(password)) {
      feedbackMessages.push("At least one special character (e.g., !@#$)");
    }
    
    return {
      isValid: feedbackMessages.length === 0,
      feedbackMessages
    };
  }

  /**
   * Updates password field UI with validation feedback
   */
  function updatePasswordFeedback() {
    if (!elements.passwordInput || !elements.passwordFeedback) return;

    const password = elements.passwordInput.value;
    elements.passwordInput.classList.remove('is-invalid', 'is-valid');
    
    if (!password) {
      elements.passwordFeedback.textContent = '';
      elements.passwordFeedback.className = 'form-text';
      validationState.password = false;
      updateSubmitButtonState();
      return;
    }

    const validation = validatePasswordComplexity(password);
    validationState.password = validation.isValid;

    if (validation.isValid) {
      elements.passwordInput.classList.add('is-valid');
      elements.passwordFeedback.textContent = 'Password strength: Good';
      elements.passwordFeedback.className = 'form-text text-success';
    } else {
      elements.passwordInput.classList.add('is-invalid');
      elements.passwordFeedback.innerHTML = `Password must contain:<ul>${
        validation.feedbackMessages.map(msg => `<li>${msg}</li>`).join('')
      }</ul>`;
      elements.passwordFeedback.className = 'form-text text-danger';
    }
    
    updateSubmitButtonState();
  }

  /**
   * Updates the submit button state based on field validation
   */
  function updateSubmitButtonState() {
    if (!elements.submitButton) return;

    const isFormValid = Object.values(validationState).every(Boolean) &&
                       elements.usernameInput?.value.trim() &&
                       elements.emailInput?.value.trim() &&
                       elements.passwordInput?.value;

    elements.submitButton.disabled = !isFormValid;
  }

  /**
   * Updates field validation state and UI classes
   * @param {string} fieldName - Name of the field being validated
   * @param {HTMLElement} inputElement - Input element
   * @param {HTMLElement} feedbackElement - Feedback element
   * @param {boolean} isValid - Whether the field is valid
   * @param {string} message - Feedback message
   */
  function updateFieldValidation(fieldName, inputElement, feedbackElement, isValid, message) {
    validationState[fieldName] = isValid;
    
    inputElement.classList.remove('is-invalid', 'is-valid');
    feedbackElement.className = 'form-text';
    
    if (isValid) {
      inputElement.classList.add('is-valid');
      feedbackElement.classList.add('text-success');
    } else {
      inputElement.classList.add('is-invalid');
      feedbackElement.classList.add('text-danger');
    }
    
    feedbackElement.textContent = message;
    updateSubmitButtonState();
  }

  /**
   * Checks field availability via API
   * @param {HTMLElement} inputElement - Input element
   * @param {HTMLElement} feedbackElement - Feedback element
   * @param {string} url - API endpoint
   * @param {string} fieldName - Field name ('username' or 'email')
   * @param {string} value - Field value
   */
  async function checkFieldAvailability(inputElement, feedbackElement, url, fieldName, value) {
    // Reset validation state
    validationState[fieldName] = false;
    inputElement.classList.remove('is-invalid', 'is-valid');
    feedbackElement.textContent = '';
    feedbackElement.className = 'form-text';

    // Validate minimum length
    if (value.length > 0 && value.length < CONFIG.minLength[fieldName]) {
      const capitalizedFieldName = fieldName.charAt(0).toUpperCase() + fieldName.slice(1);
      updateFieldValidation(
        fieldName, 
        inputElement, 
        feedbackElement, 
        false, 
        `${capitalizedFieldName} must be at least ${CONFIG.minLength[fieldName]} characters`
      );
      return;
    }

    // Skip validation for empty fields
    if (!value) {
      updateSubmitButtonState();
      return;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': window.csrfToken || ''
        },
        body: JSON.stringify({ [fieldName]: value })
      });
      
      const data = await response.json();
      const capitalizedFieldName = fieldName.charAt(0).toUpperCase() + fieldName.slice(1);

      if (response.ok && data.available) {
        updateFieldValidation(
          fieldName, 
          inputElement, 
          feedbackElement, 
          true, 
          data.message || `${capitalizedFieldName} is available!`
        );
      } else {
        updateFieldValidation(
          fieldName, 
          inputElement, 
          feedbackElement, 
          false, 
          data.message || `${capitalizedFieldName} is not available or invalid`
        );
      }
    } catch (error) {
      console.error(`Error checking ${fieldName} availability:`, error);
      updateFieldValidation(
        fieldName, 
        inputElement, 
        feedbackElement, 
        false, 
        'Could not verify. Check connection or try again'
      );
    }
  }

  /**
   * Creates a debounced version of a function
   * @param {Function} func - Function to debounce
   * @param {number} delay - Delay in milliseconds
   * @returns {Function} Debounced function
   */
  function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
  }

  // Set up event listeners
  if (elements.usernameInput && elements.usernameFeedback) {
    elements.usernameInput.addEventListener('input', debounce(function() {
      checkFieldAvailability(
        elements.usernameInput, 
        elements.usernameFeedback, 
        '/check_username', 
        'username', 
        this.value.trim()
      );
    }, CONFIG.debounceDelays.username));
  }

  if (elements.emailInput && elements.emailFeedback) {
    elements.emailInput.addEventListener('input', debounce(function() {
      checkFieldAvailability(
        elements.emailInput, 
        elements.emailFeedback, 
        '/check_email', 
        'email', 
        this.value.trim()
      );
    }, CONFIG.debounceDelays.email));
  }

  if (elements.passwordInput && elements.passwordFeedback) {
    elements.passwordInput.addEventListener('input', debounce(
      updatePasswordFeedback, 
      CONFIG.debounceDelays.password
    ));
  }
  
  // Initialize button state
  updateSubmitButtonState();
});
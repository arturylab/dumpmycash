document.addEventListener('DOMContentLoaded', function () {
  const registerModalElement = document.getElementById('registerModal');
  let registerModalInstance;

  if (registerModalElement) {
    registerModalInstance = new bootstrap.Modal(registerModalElement);
    if (window.openRegisterModal === true) {
      registerModalInstance.show();
    }
  }

  // Modal alerts are now handled by base.js - no need for custom handling

  const showPasswordCheckboxModal = document.getElementById('showPasswordModalCheck');
  const passwordInputModal = document.getElementById('floatingPasswordModal');

  if (showPasswordCheckboxModal && passwordInputModal) {
    showPasswordCheckboxModal.addEventListener('change', function () {
      passwordInputModal.type = this.checked ? 'text' : 'password';
    });
  }

  const usernameInput = document.getElementById('floatingUsername');
  const emailInput = document.getElementById('floatingEmail');
  const passwordForValidation = document.getElementById('floatingPasswordModal'); 
  
  const usernameFeedback = document.getElementById('usernameFeedback');
  const emailFeedback = document.getElementById('emailFeedback');
  const passwordFeedback = document.getElementById('passwordFeedback');

  const registerSubmitButton = document.getElementById('registerSubmitButton');

  let isUsernamePotentiallyValid = false; 
  let isEmailPotentiallyValid = false;    
  let isPasswordPotentiallyValid = false;

  /**
   * Validates password complexity based on predefined rules.
   * @param {string} password - The password string to validate.
   * @returns {object} An object containing `isValid` (boolean) and `feedbackMessages` (array of strings).
   */
  function validatePasswordComplexity(password) {
    const feedbackMessages = [];
    let isValid = true;

    if (password.length < 8) {
      feedbackMessages.push("At least 8 characters.");
      isValid = false;
    }
    if (!/[a-zA-Z]/.test(password)) {
      feedbackMessages.push("At least one letter (a-z, A-Z).");
      isValid = false;
    }
    if (!/\d/.test(password)) {
      feedbackMessages.push("At least one number (0-9).");
      isValid = false;
    }
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]/.test(password)) {
      feedbackMessages.push("At least one special character (e.g., !@#$).");
      isValid = false;
    }
    
    return { isValid, feedbackMessages };
  }

  /**
   * Updates the UI with password complexity feedback.
   */
  function updatePasswordFeedback() {
    if (!passwordForValidation || !passwordFeedback) return;

    const password = passwordForValidation.value;
    passwordForValidation.classList.remove('is-invalid', 'is-valid');
    
    if (password.length === 0) {
        passwordFeedback.textContent = '';
        passwordFeedback.className = 'form-text';
        isPasswordPotentiallyValid = false;
        updateSubmitButtonState();
        return;
    }

    const complexity = validatePasswordComplexity(password);
    isPasswordPotentiallyValid = complexity.isValid;

    if (complexity.isValid) {
      passwordForValidation.classList.add('is-valid');
      passwordFeedback.textContent = 'Password strength: Good';
      passwordFeedback.className = 'form-text text-success';
    } else {
      passwordForValidation.classList.add('is-invalid');
      passwordFeedback.innerHTML = 'Password must contain:<ul>' + 
                                   complexity.feedbackMessages.map(msg => `<li>${msg}</li>`).join('') + 
                                   '</ul>';
      passwordFeedback.className = 'form-text text-danger';
    }
    updateSubmitButtonState();
  }

  /**
   * Updates the enabled/disabled state of the register submit button
   * based on the validity of the input fields.
   */
  function updateSubmitButtonState() {
    if (registerSubmitButton && usernameInput && emailInput && passwordForValidation) {
      const usernameFilled = usernameInput.value.trim().length > 0;
      const emailFilled = emailInput.value.trim().length > 0;
      const passwordFilled = passwordForValidation.value.length > 0;

      const usernameCheckOk = usernameInput.value.trim().length < 3 || isUsernamePotentiallyValid;
      const emailCheckOk = emailInput.value.trim().length < 3 || isEmailPotentiallyValid;
      
      registerSubmitButton.disabled = !(
          usernameFilled && emailFilled && passwordFilled &&
          usernameCheckOk && emailCheckOk && isPasswordPotentiallyValid
      );
    }
  }

  /**
   * Checks the availability of a username or email via an API call.
   * @param {HTMLElement} inputElement - The input HTML element.
   * @param {HTMLElement} feedbackElement - The HTML element for displaying feedback.
   * @param {string} url - The API endpoint URL.
   * @param {string} fieldName - The name of the field being checked ('username' or 'email').
   * @param {string} value - The value of the field.
   */
  async function checkAvailability(inputElement, feedbackElement, url, fieldName, value) {
    inputElement.classList.remove('is-invalid', 'is-valid');
    feedbackElement.textContent = '';
    feedbackElement.className = 'form-text'; 

    if (fieldName === 'username') isUsernamePotentiallyValid = false;
    if (fieldName === 'email') isEmailPotentiallyValid = false;

    if (value.length > 0 && value.length < 3) {
      inputElement.classList.add('is-invalid');
      feedbackElement.textContent = `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} must be at least 3 characters.`;
      feedbackElement.classList.add('text-danger');
      updateSubmitButtonState();
      return;
    }
    if (value.length === 0) { 
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

      if (response.ok && data.available) {
        inputElement.classList.remove('is-invalid');
        inputElement.classList.add('is-valid');
        feedbackElement.textContent = data.message || `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} is available!`;
        feedbackElement.classList.add('text-success');
        if (fieldName === 'username') isUsernamePotentiallyValid = true;
        if (fieldName === 'email') isEmailPotentiallyValid = true;
      } else {
        inputElement.classList.remove('is-valid');
        inputElement.classList.add('is-invalid');
        feedbackElement.textContent = data.message || `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} is not available or invalid.`;
        feedbackElement.classList.add('text-danger');
        if (fieldName === 'username') isUsernamePotentiallyValid = false;
        if (fieldName === 'email') isEmailPotentiallyValid = false;
      }
    } catch (error) {
      console.error('Error checking availability:', error);
      inputElement.classList.add('is-invalid');
      feedbackElement.textContent = 'Could not verify. Check connection or try again.';
      feedbackElement.classList.add('text-danger');
      if (fieldName === 'username') isUsernamePotentiallyValid = false;
      if (fieldName === 'email') isEmailPotentiallyValid = false;
    }
    updateSubmitButtonState();
  }

  /**
   * Debounces a function call.
   * @param {Function} func - The function to debounce.
   * @param {number} delay - The debounce delay in milliseconds.
   * @returns {Function} The debounced function.
   */
  function debounce(func, delay) {
    let timeout;
    return function(...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), delay);
    };
  }

  if (usernameInput && usernameFeedback) {
    usernameInput.addEventListener('input', debounce(function() {
      checkAvailability(usernameInput, usernameFeedback, '/check_username', 'username', this.value.trim());
    }, 500));
  }

  if (emailInput && emailFeedback) {
    emailInput.addEventListener('input', debounce(function() {
      checkAvailability(emailInput, emailFeedback, '/check_email', 'email', this.value.trim());
    }, 500));
  }

  if (passwordForValidation && passwordFeedback) {
    passwordForValidation.addEventListener('input', debounce(function() {
        updatePasswordFeedback();
    }, 300));
  }
  
  updateSubmitButtonState();
});
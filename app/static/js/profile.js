// Profile page functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeProfilePage();
});

function initializeProfilePage() {
    setupPasswordToggle();
    setupFormSubmissions();
    setupDeleteDataModal();
    setupDeleteAccountModal();
    setupRestoreDataModal();
    loadUserStatistics();
    showFlashMessages();
}

function setupPasswordToggle() {
    // Toggle password visibility for all password fields
    const toggleButtons = [
        { button: 'toggleCurrentPassword', input: 'currentPassword' },
        { button: 'toggleNewPassword', input: 'newPassword' },
        { button: 'toggleConfirmPassword', input: 'confirmPassword' }
    ];

    toggleButtons.forEach(({ button, input }) => {
        const toggleBtn = document.getElementById(button);
        const passwordInput = document.getElementById(input);
        
        if (toggleBtn && passwordInput) {
            toggleBtn.addEventListener('click', function() {
                const icon = this.querySelector('i');
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                } else {
                    passwordInput.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                }
            });
        }
    });
}

function setupFormSubmissions() {
    // Profile form submission
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleProfileUpdate();
        });
    }

    // Password form submission
    const passwordForm = document.getElementById('passwordForm');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handlePasswordChange();
        });
    }
}

function handleProfileUpdate() {
    const firstName = document.getElementById('firstName').value.trim();
    const lastName = document.getElementById('lastName').value.trim();
    const email = document.getElementById('email').value.trim();

    // Basic validation
    if (!firstName && !lastName && !email) {
        showFlashMessage('Please provide at least one field to update.', 'warning');
        return;
    }

    // Email validation
    if (email && !isValidEmail(email)) {
        showFlashMessage('Please enter a valid email address.', 'error');
        return;
    }

    // Send data to the server
    fetch('/profile/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrf_token]').value
        },
        body: JSON.stringify({
            firstName: firstName,
            lastName: lastName,
            email: email
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showFlashMessage(data.message, 'success');
            
            // Update the display name in the header if name was updated
            if (data.name) {
                const displayNameElement = document.getElementById('displayName');
                if (displayNameElement) {
                    displayNameElement.textContent = data.name;
                }
            }
            
            // Update the email display if email was updated
            if (data.email) {
                // Update the email input value
                document.getElementById('email').value = data.email;
                
                // Update email display in header if it exists
                const emailDisplay = document.querySelector('.card-body .text-muted');
                if (emailDisplay && emailDisplay.textContent.includes('@')) {
                    emailDisplay.textContent = data.email;
                }
            }
        } else {
            showFlashMessage(data.message || 'Error updating profile', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showFlashMessage('Error updating profile', 'error');
    });
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function handlePasswordChange() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
        showFlashMessage('Please fill in all password fields.', 'error');
        return;
    }

    if (newPassword.length < 8) {
        showFlashMessage('New password must be at least 8 characters long.', 'error');
        return;
    }

    if (newPassword !== confirmPassword) {
        showFlashMessage('New passwords do not match.', 'error');
        return;
    }

    // Send data to the server
    fetch('/profile/change-password', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrf_token]').value
        },
        body: JSON.stringify({
            currentPassword: currentPassword,
            newPassword: newPassword,
            confirmPassword: confirmPassword
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showFlashMessage(data.message, 'success');
            // Clear password fields on success
            document.getElementById('currentPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
        } else {
            showFlashMessage(data.message || 'Error changing password', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showFlashMessage('Error changing password', 'error');
    });
}

function setupDeleteAccountModal() {
    // First step validation
    const deleteInput1 = document.getElementById('deleteAccountConfirmation1');
    const step1Button = document.getElementById('deleteAccountStep1Btn');
    const step1Div = document.getElementById('deleteAccountStep1');
    const step2Div = document.getElementById('deleteAccountStep2');
    const backButton = document.getElementById('deleteAccountBackBtn');

    if (deleteInput1 && step1Button) {
        deleteInput1.addEventListener('input', function() {
            step1Button.disabled = this.value !== 'DELETE ACCOUNT';
        });

        step1Button.addEventListener('click', function() {
            if (deleteInput1.value === 'DELETE ACCOUNT') {
                // Move to step 2
                step1Div.style.display = 'none';
                step2Div.style.display = 'block';
                
                // Hide footer
                const footer = document.getElementById('deleteAccountFooter');
                if (footer) footer.style.display = 'none';
            }
        });
    }

    // Second step validation
    const deleteInput2 = document.getElementById('deleteAccountConfirmation2');
    const confirmButton = document.getElementById('confirmDeleteAccountBtn');

    if (deleteInput2 && confirmButton) {
        deleteInput2.addEventListener('input', function() {
            confirmButton.disabled = this.value !== 'PERMANENTLY DELETE';
        });

        confirmButton.addEventListener('click', function() {
            if (deleteInput2.value === 'PERMANENTLY DELETE') {
                // Send deletion request to the server
                fetch('/profile/delete-account', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrf_token]').value
                    },
                    body: JSON.stringify({
                        confirmation1: deleteInput1.value,
                        confirmation2: deleteInput2.value
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showFlashMessage(data.message, 'success');
                        
                        // If logout is required, redirect after a delay
                        if (data.logout) {
                            setTimeout(() => {
                                window.location.href = '/auth/login';
                            }, 2000);
                        }
                    } else {
                        showFlashMessage(data.message || 'Error deleting account', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showFlashMessage('Error deleting account', 'error');
                });
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteAccountModal'));
                modal.hide();
            }
        });
    }

    // Back button functionality
    if (backButton) {
        backButton.addEventListener('click', function() {
            // Reset to step 1
            step2Div.style.display = 'none';
            step1Div.style.display = 'block';
            
            // Show footer
            const footer = document.getElementById('deleteAccountFooter');
            if (footer) footer.style.display = 'block';
            
            // Clear step 2 input
            if (deleteInput2) {
                deleteInput2.value = '';
                confirmButton.disabled = true;
            }
        });
    }

    // Reset when modal is closed
    document.getElementById('deleteAccountModal').addEventListener('hidden.bs.modal', function() {
        // Reset both steps
        if (deleteInput1) deleteInput1.value = '';
        if (deleteInput2) deleteInput2.value = '';
        if (step1Button) step1Button.disabled = true;
        if (confirmButton) confirmButton.disabled = true;
        
        // Reset to step 1
        if (step1Div) step1Div.style.display = 'block';
        if (step2Div) step2Div.style.display = 'none';
        
        // Show footer
        const footer = document.getElementById('deleteAccountFooter');
        if (footer) footer.style.display = 'block';
    });
}

function setupDeleteDataModal() {
    // First step validation
    const deleteInput1 = document.getElementById('deleteDataConfirmation1');
    const step1Button = document.getElementById('deleteDataStep1Btn');
    const step1Div = document.getElementById('deleteDataStep1');
    const step2Div = document.getElementById('deleteDataStep2');
    const backButton = document.getElementById('deleteDataBackBtn');

    if (deleteInput1 && step1Button) {
        deleteInput1.addEventListener('input', function() {
            step1Button.disabled = this.value !== 'DELETE ALL DATA';
        });

        step1Button.addEventListener('click', function() {
            if (deleteInput1.value === 'DELETE ALL DATA') {
                // Move to step 2
                step1Div.style.display = 'none';
                step2Div.style.display = 'block';
                
                // Hide footer
                const footer = document.getElementById('deleteDataFooter');
                if (footer) footer.style.display = 'none';
            }
        });
    }

    // Second step validation
    const deleteInput2 = document.getElementById('deleteDataConfirmation2');
    const confirmButton = document.getElementById('confirmDeleteDataBtn');

    if (deleteInput2 && confirmButton) {
        deleteInput2.addEventListener('input', function() {
            confirmButton.disabled = this.value !== 'CONFIRM DELETE';
        });

        confirmButton.addEventListener('click', function() {
            if (deleteInput2.value === 'CONFIRM DELETE') {
                // Send deletion request to the server
                fetch('/profile/delete-all-data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrf_token]').value
                    },
                    body: JSON.stringify({
                        confirmation1: deleteInput1.value,
                        confirmation2: deleteInput2.value
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showFlashMessage(data.message, 'success');
                        
                        // Reload statistics to show zeros
                        setTimeout(() => {
                            loadUserStatistics();
                        }, 1000);
                    } else {
                        showFlashMessage(data.message || 'Error deleting data', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showFlashMessage('Error deleting data', 'error');
                });
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('deleteDataModal'));
                modal.hide();
            }
        });
    }

    // Back button functionality
    if (backButton) {
        backButton.addEventListener('click', function() {
            // Reset to step 1
            step2Div.style.display = 'none';
            step1Div.style.display = 'block';
            
            // Show footer
            const footer = document.getElementById('deleteDataFooter');
            if (footer) footer.style.display = 'block';
            
            // Clear step 2 input
            if (deleteInput2) {
                deleteInput2.value = '';
                confirmButton.disabled = true;
            }
        });
    }

    // Reset when modal is closed
    document.getElementById('deleteDataModal').addEventListener('hidden.bs.modal', function() {
        // Reset both steps
        if (deleteInput1) deleteInput1.value = '';
        if (deleteInput2) deleteInput2.value = '';
        if (step1Button) step1Button.disabled = true;
        if (confirmButton) confirmButton.disabled = true;
        
        // Reset to step 1
        if (step1Div) step1Div.style.display = 'block';
        if (step2Div) step2Div.style.display = 'none';
        
        // Show footer
        const footer = document.getElementById('deleteDataFooter');
        if (footer) footer.style.display = 'block';
    });
}

function setupRestoreDataModal() {
    const confirmCheckbox = document.getElementById('confirmRestore');
    const restoreBtn = document.getElementById('restoreBtn');
    const backupFileInput = document.getElementById('backupFile');

    if (confirmCheckbox && restoreBtn) {
        // Enable/disable restore button based on checkbox and file selection
        const updateRestoreButton = () => {
            const fileSelected = backupFileInput && backupFileInput.files.length > 0;
            const confirmed = confirmCheckbox.checked;
            restoreBtn.disabled = !(fileSelected && confirmed);
        };

        confirmCheckbox.addEventListener('change', updateRestoreButton);
        
        if (backupFileInput) {
            backupFileInput.addEventListener('change', function() {
                updateRestoreButton();
                
                // Validate file type
                if (this.files.length > 0) {
                    const file = this.files[0];
                    if (!file.name.toLowerCase().endsWith('.json')) {
                        showFlashMessage('Please select a JSON file', 'error');
                        this.value = '';
                        updateRestoreButton();
                    }
                }
            });
        }

        // Reset when modal is closed
        document.getElementById('restoreDataModal').addEventListener('hidden.bs.modal', function() {
            confirmCheckbox.checked = false;
            if (backupFileInput) backupFileInput.value = '';
            restoreBtn.disabled = true;
        });
    }
}

function showFlashMessage(message, type) {
    const flashContainer = document.getElementById('flash-container');
    if (!flashContainer) return;

    // Remove existing flash messages
    flashContainer.innerHTML = '';

    // Create flash message element
    const flashDiv = document.createElement('div');
    flashDiv.className = `alert alert-${getBootstrapAlertType(type)} alert-dismissible fade show flash-message`;
    flashDiv.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;

    flashDiv.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas ${getFlashIcon(type)} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    flashContainer.appendChild(flashDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (flashDiv.parentNode) {
            const alert = new bootstrap.Alert(flashDiv);
            alert.close();
        }
    }, 5000);
}

function getBootstrapAlertType(type) {
    const typeMap = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    return typeMap[type] || 'info';
}

function getFlashIcon(type) {
    const iconMap = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    return iconMap[type] || 'fa-info-circle';
}

function showFlashMessages() {
    // Check for existing flash messages from the server
    const existingAlerts = document.querySelectorAll('.alert:not(.flash-message)');
    existingAlerts.forEach(alert => {
        // Move server flash messages to the fixed position
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        `;
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                const bootstrapAlert = new bootstrap.Alert(alert);
                bootstrapAlert.close();
            }
        }, 5000);
    });
}

function loadUserStatistics() {
    // Load user statistics from API
    fetch('/profile/api/stats')
    .then(response => response.json())
    .then(data => {
        // Update statistics in the UI
        const totalTransactions = document.getElementById('totalTransactions');
        const categoriesCreated = document.getElementById('categoriesCreated');
        const accountsManaged = document.getElementById('accountsManaged');
        const daysActive = document.getElementById('daysActive');

        if (totalTransactions) totalTransactions.textContent = data.total_transactions || 0;
        if (categoriesCreated) categoriesCreated.textContent = data.categories_created || 0;
        if (accountsManaged) accountsManaged.textContent = data.accounts_managed || 0;
        if (daysActive) daysActive.textContent = data.days_active || 0;
    })
    .catch(error => {
        console.error('Error loading user statistics:', error);
        // Keep the server-rendered values if API fails
    });
}

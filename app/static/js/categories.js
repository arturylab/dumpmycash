document.addEventListener('DOMContentLoaded', function() {
    // CSRF token for API requests
    const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
    
    // Debug: Check if CSRF token is available
    if (!csrfToken) {
        console.warn('CSRF token not found in meta tag');
    } else {
        console.log('CSRF token loaded successfully');
    }
    
    // Elements
    const addCategoryModal = document.getElementById('addCategoryModal');
    const editCategoryModal = document.getElementById('editCategoryModal');
    const deleteCategoryModal = document.getElementById('deleteCategoryModal');
    
    const addCategoryForm = document.getElementById('addCategoryForm');
    const editCategoryForm = document.getElementById('editCategoryForm');
    
    const saveAddCategoryBtn = document.getElementById('saveAddCategory');
    const saveEditCategoryBtn = document.getElementById('saveEditCategory');
    const deleteCategoryBtn = document.getElementById('deleteCategoryBtn');
    const confirmDeleteCategoryBtn = document.getElementById('confirmDeleteCategory');
    
    // Current category ID for editing/deleting
    let currentCategoryId = null;
    
    // Emoji categories for picker
    const emojiCategories = {
        finance: ['💰', '💸', '💳', '💵', '💶', '💷', '💎', '🏦', '🏧', '💹', '💱', '💲'],
        food: ['🍕', '🍔', '🍟', '🌭', '🍿', '🥗', '🍜', '🍱', '🍣', '🍤', '🍛', '🍝', '🍖', '🥩', '🍗', '🥞', '🧀', '🥖', '🥨', '🍞', '🍽️'],
        transport: ['🚗', '🚕', '🚙', '🚌', '🚎', '🏎️', '🚓', '🚑', '🚒', '🚐', '🛻', '🚚', '🚛', '🚜', '🚲', '🛵', '🏍️', '✈️', '🚁', '⛵'],
        shopping: ['🛒', '🛍️', '👕', '👔', '👗', '👠', '👟', '👜', '💄', '👓', '⌚', '💍', '🎁', '🧸', '📱', '💻'],
        home: ['🏠', '🏡', '🏘️', '🏰', '🏗️', '🔨', '🔧', '🧽', '🧹', '🛏️', '🛋️', '🚪', '🪑', '🚽', '🚿', '💡','🐶', '🐱'],
        health: ['🏥', '💊', '🩺', '💉', '🧬', '🔬', '🏃', '🤸', '🧘', '💆', '🛀', '🧴', '🪥', '🧻'],
        entertainment: ['🎬', '🎮', '🎵', '🎸', '🎯', '🎲', '🃏', '🎭', '🎪', '🎨', '📚', '📖', '📺', '📻', '🎧'],
        travel: ['🧳', '🗺️', '🏖️', '🏔️', '🗻', '🏕️', '⛺', '🎒', '📷', '🗽', '🗼', '🏛️', '⛩️', '🕌', '⛪'],
        general: ['📄', '📊', '📈', '📉', '⭐', '❤️', '💛', '💚', '💙', '💜', '🖤', '🤍', '💔', '❗', '❓', '⚡', '🔥', '💧']
    };
    
    // Initialize emoji pickers
    function initializeEmojiPicker(gridId, inputId) {
        const grid = document.getElementById(gridId);
        grid.innerHTML = '';
        
        // Create organized categories
        const categoryLabels = {
            finance: 'Finance & Money',
            food: 'Food & Dining',
            transport: 'Transportation',
            shopping: 'Shopping',
            home: 'Home & Utilities',
            health: 'Health & Fitness',
            entertainment: 'Entertainment',
            travel: 'Travel',
            general: 'General'
        };
        
        let content = '';
        
        Object.keys(emojiCategories).forEach(category => {
            content += `<div class="mb-3">
                <div class="fw-bold text-secondary mb-1" style="font-size: 0.75rem;">${categoryLabels[category]}</div>
                <div class="row g-1">`;
            
            emojiCategories[category].forEach(emoji => {
                content += `<div class="col-auto">
                    <button type="button" class="btn btn-sm btn-outline-light emoji-btn" 
                            data-emoji="${emoji}" data-target="${inputId}" 
                            style="width: 30px; height: 30px; padding: 2px; font-size: 14px; border: 1px solid #dee2e6;"
                            onmouseover="this.style.backgroundColor='#f8f9fa'; this.style.borderColor='#007bff';"
                            onmouseout="this.style.backgroundColor=''; this.style.borderColor='#dee2e6';"
                            title="${emoji}">${emoji}</button>
                </div>`;
            });
            
            content += '</div></div>';
        });
        
        grid.innerHTML = content;
    }
    
    // Initialize both emoji pickers
    initializeEmojiPicker('addEmojiGrid', 'addCategoryEmoji');
    initializeEmojiPicker('editEmojiGrid', 'editCategoryEmoji');
    
    // Handle emoji selection
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('emoji-btn')) {
            const emoji = e.target.getAttribute('data-emoji');
            const targetInputId = e.target.getAttribute('data-target');
            const targetInput = document.getElementById(targetInputId);
            
            if (targetInput) {
                targetInput.value = emoji;
                
                // Close the dropdown
                const dropdown = e.target.closest('.dropdown-menu');
                if (dropdown) {
                    const button = dropdown.previousElementSibling;
                    if (button) {
                        const dropdownInstance = bootstrap.Dropdown.getInstance(button);
                        if (dropdownInstance) {
                            dropdownInstance.hide();
                        }
                    }
                }
            }
        }
    });
    
    // Utility functions
    function showSpinner(button) {
        const spinner = button.querySelector('.spinner-border');
        if (spinner) spinner.classList.remove('d-none');
        button.disabled = true;
    }
    
    function hideSpinner(button) {
        const spinner = button.querySelector('.spinner-border');
        if (spinner) spinner.classList.add('d-none');
        button.disabled = false;
    }
    
    function showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        field.classList.add('is-invalid');
        if (feedback) feedback.textContent = message;
    }
    
    function clearFieldErrors(form) {
        const fields = form.querySelectorAll('.form-control, .form-select');
        fields.forEach(field => {
            field.classList.remove('is-invalid');
            const feedback = field.parentNode.querySelector('.invalid-feedback');
            if (feedback) feedback.textContent = '';
        });
    }
    
    function showAlert(message, type = 'success') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Insert at the top of the main content
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
    
    // Event listeners for modal triggers
    document.addEventListener('click', function(e) {
        // Handle time filter selection
        if (e.target.hasAttribute('data-filter')) {
            e.preventDefault();
            const filter = e.target.getAttribute('data-filter');
            
            // Update active state
            document.querySelectorAll('#timeFilterDropdown .dropdown-item').forEach(item => {
                item.classList.remove('active');
            });
            e.target.classList.add('active');
            
            // Update button text
            const filterNames = {
                'today': 'Today',
                'week': 'This Week',
                'month': 'This Month',
                'quarter': 'This Quarter',
                'year': 'This Year',
                'all': 'All Time'
            };
            
            document.getElementById('currentFilter').textContent = filterNames[filter];
            
            // Reload page with new filter
            const url = new URL(window.location);
            url.searchParams.set('filter', filter);
            window.location.href = url.toString();
            
            return;
        }
        
        // Handle edit category buttons
        if (e.target.hasAttribute('data-action') && e.target.getAttribute('data-action') === 'edit') {
            const categoryId = e.target.getAttribute('data-category-id');
            const categoryName = e.target.getAttribute('data-category-name');
            const categoryType = e.target.getAttribute('data-category-type');
            const categoryEmoji = e.target.getAttribute('data-category-emoji');
            
            // Populate edit form
            document.getElementById('editCategoryId').value = categoryId;
            document.getElementById('editCategoryName').value = categoryName;
            document.getElementById('editCategoryType').value = categoryType;
            document.getElementById('editCategoryEmoji').value = categoryEmoji;
            
            currentCategoryId = categoryId;
        }
    });
    
    // Add category form submission
    saveAddCategoryBtn.addEventListener('click', function() {
        // Prevent multiple submissions
        if (saveAddCategoryBtn.disabled) {
            return;
        }
        
        clearFieldErrors(addCategoryForm);
        
        const formData = new FormData(addCategoryForm);
        
        const data = {
            name: formData.get('name').trim(),
            type: formData.get('type'),
            unicode_emoji: formData.get('unicode_emoji').trim() || (formData.get('type') === 'income' ? '💰' : '💸')
        };
        
        // Basic validation
        if (!data.name) {
            showFieldError('addCategoryName', 'Category name is required');
            return;
        }
        
        if (!data.type) {
            showFieldError('addCategoryType', 'Category type is required');
            return;
        }
        
        showSpinner(saveAddCategoryBtn);
        
        fetch('/categories/api/categories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response headers:', [...response.headers.entries()]);
            if (!response.ok) {
                return response.text().then(text => {
                    console.error('Error response body:', text);
                    throw new Error(`HTTP ${response.status}: ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            hideSpinner(saveAddCategoryBtn);
            
            if (data.success) {
                showAlert('Category created successfully!', 'success');
                bootstrap.Modal.getInstance(addCategoryModal).hide();
                addCategoryForm.reset();
                location.reload(); // Reload to show new category
            } else {
                showAlert(data.error || 'Error creating category', 'danger');
            }
        })
        .catch(error => {
            hideSpinner(saveAddCategoryBtn);
            console.error('Fetch error:', error);
            showAlert('Error creating category: ' + error.message, 'danger');
        });
    });
    
    // Edit category form submission
    saveEditCategoryBtn.addEventListener('click', function() {
        // Prevent multiple submissions
        if (saveEditCategoryBtn.disabled) {
            return;
        }
        
        clearFieldErrors(editCategoryForm);
        
        const formData = new FormData(editCategoryForm);
        const data = {
            name: formData.get('name').trim(),
            type: formData.get('type'),
            unicode_emoji: formData.get('unicode_emoji').trim() || (formData.get('type') === 'income' ? '💰' : '💸')
        };
        
        // Basic validation
        if (!data.name) {
            showFieldError('editCategoryName', 'Category name is required');
            return;
        }
        
        showSpinner(saveEditCategoryBtn);
        
        fetch(`/categories/api/categories/${currentCategoryId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            hideSpinner(saveEditCategoryBtn);
            
            if (data.success) {
                showAlert('Category updated successfully!', 'success');
                bootstrap.Modal.getInstance(editCategoryModal).hide();
                location.reload(); // Reload to show updated category
            } else {
                showAlert(data.error || 'Error updating category', 'danger');
            }
        })
        .catch(error => {
            hideSpinner(saveEditCategoryBtn);
            showAlert('Error updating category: ' + error.message, 'danger');
        });
    });
    
    // Delete category button
    deleteCategoryBtn.addEventListener('click', function() {
        const categoryName = document.getElementById('editCategoryName').value;
        document.getElementById('deleteCategoryName').textContent = categoryName;
        
        bootstrap.Modal.getInstance(editCategoryModal).hide();
        new bootstrap.Modal(deleteCategoryModal).show();
    });
    
    // Confirm delete category
    confirmDeleteCategoryBtn.addEventListener('click', function() {
        // Prevent multiple submissions
        if (confirmDeleteCategoryBtn.disabled) {
            return;
        }
        
        showSpinner(confirmDeleteCategoryBtn);
        
        fetch(`/categories/api/categories/${currentCategoryId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            hideSpinner(confirmDeleteCategoryBtn);
            
            if (data.success) {
                showAlert('Category deleted successfully!', 'success');
                bootstrap.Modal.getInstance(deleteCategoryModal).hide();
                location.reload(); // Reload to remove deleted category
            } else {
                showAlert(data.error || 'Error deleting category', 'danger');
            }
        })
        .catch(error => {
            hideSpinner(confirmDeleteCategoryBtn);
            showAlert('Error deleting category: ' + error.message, 'danger');
        });
    });
    
    // Reset Add Category form when modal is shown
    addCategoryModal.addEventListener('show.bs.modal', function () {
        // Clear any previous errors first
        clearFieldErrors(addCategoryForm);
        
        // Reset the form
        addCategoryForm.reset();
        
        // Reset modal title
        document.getElementById('addCategoryModalLabel').textContent = 'Add Category';
        
        // Reset emoji placeholder
        document.getElementById('addCategoryEmoji').placeholder = '💵';
    });
});

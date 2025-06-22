// Transactions JavaScript functionality
class TransactionManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAjaxDefaults();
    }

    setupAjaxDefaults() {
        // Setup CSRF token for AJAX requests
        const csrfToken = document.querySelector('meta[name=csrf-token]');
        if (csrfToken) {
            fetch.defaults = {
                headers: {
                    'X-CSRFToken': csrfToken.getAttribute('content')
                }
            };
        }
    }

    setupEventListeners() {
        // Filter form auto-submit
        this.setupFilterForm();
        
        // Time filter dropdown
        this.setupTimeFilter();
        
        // Quick actions
        this.setupQuickActions();
        
        // Bulk operations
        this.setupBulkOperations();
    }

    setupFilterForm() {
        const filterForm = document.querySelector('#filterCollapse form');
        if (filterForm) {
            // Remove auto-submit functionality - users must click Apply Filters button
            // The form will only submit when the user clicks the submit button
            console.log('Filter form setup completed - manual submission only');
        }
    }

    setupTimeFilter() {
        // Handle time filter dropdown
        const timeFilterDropdown = document.querySelector('#timeFilterDropdown');
        if (timeFilterDropdown) {
            timeFilterDropdown.addEventListener('click', (e) => {
                if (e.target.matches('a[data-filter]')) {
                    e.preventDefault();
                    e.stopPropagation(); // Prevent dropdown from closing immediately
                    
                    const filter = e.target.getAttribute('data-filter');
                    
                    // Handle custom date range filter
                    if (filter === 'custom') {
                        this.showCustomDateRangeModal();
                        return;
                    }
                    
                    // Update URL with new filter while preserving other filters
                    const url = new URL(window.location);
                    url.searchParams.set('filter', filter);
                    
                    // Remove any legacy date_range parameter when using new time filter
                    url.searchParams.delete('date_range');
                    // Remove custom date parameters when using predefined filters
                    url.searchParams.delete('start_date');
                    url.searchParams.delete('end_date');
                    
                    // Remove page parameter to go back to first page
                    url.searchParams.delete('page');
                    
                    // Redirect to new URL
                    window.location.href = url.toString();
                }
            });
        }
        
        // Setup custom date range modal
        this.setupCustomDateRangeModal();
    }

    setupQuickActions() {
        // Delete buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="delete-transaction"]') || 
                e.target.closest('[data-action="delete-transaction"]')) {
                
                const button = e.target.matches('[data-action="delete-transaction"]') ? 
                              e.target : e.target.closest('[data-action="delete-transaction"]');
                
                this.deleteTransaction(button.getAttribute('data-transaction-id'));
            }
            
            // Transfer warning buttons
            if (e.target.matches('[data-action="show-transfer-warning"]') || 
                e.target.closest('[data-action="show-transfer-warning"]')) {
                
                showTransferWarning();
            }
            
            // View transfer buttons
            if (e.target.matches('[data-action="view-transfer"]') || 
                e.target.closest('[data-action="view-transfer"]')) {
                
                const button = e.target.matches('[data-action="view-transfer"]') ? 
                              e.target : e.target.closest('[data-action="view-transfer"]');
                
                const transferId = button.getAttribute('data-transfer-id');
                if (transferId) {
                    viewTransferFromTransaction(transferId);
                }
            }
        });
    }

    setupBulkOperations() {
        const selectAllCheckbox = document.querySelector('#selectAll');
        const transactionCheckboxes = document.querySelectorAll('.transaction-checkbox');
        const bulkActionsBtn = document.querySelector('#bulkActionsBtn');

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                transactionCheckboxes.forEach(checkbox => {
                    checkbox.checked = e.target.checked;
                });
                this.updateBulkActionsVisibility();
            });
        }

        transactionCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkActionsVisibility();
                
                // Update select all checkbox state
                if (selectAllCheckbox) {
                    const checkedCount = document.querySelectorAll('.transaction-checkbox:checked').length;
                    selectAllCheckbox.checked = checkedCount === transactionCheckboxes.length;
                    selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < transactionCheckboxes.length;
                }
            });
        });
    }

    updateBulkActionsVisibility() {
        const checkedBoxes = document.querySelectorAll('.transaction-checkbox:checked');
        const bulkActionsBtn = document.querySelector('#bulkActionsBtn');
        
        if (bulkActionsBtn) {
            bulkActionsBtn.style.display = checkedBoxes.length > 0 ? 'block' : 'none';
            bulkActionsBtn.textContent = `Actions (${checkedBoxes.length} selected)`;
        }
    }

    async deleteTransaction(transactionId) {
        if (!confirm('Are you sure you want to delete this transaction? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/transactions/api/transactions/${transactionId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (response.ok) {
                this.showNotification('Transaction deleted successfully', 'success');
                // Reload the page or remove the row
                location.reload();
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to delete transaction', 'error');
            }
        } catch (error) {
            console.error('Error deleting transaction:', error);
            this.showNotification('An error occurred while deleting the transaction', 'error');
        }
    }

    async bulkDeleteTransactions() {
        const selectedIds = Array.from(document.querySelectorAll('.transaction-checkbox:checked'))
                                .map(checkbox => checkbox.value);

        if (selectedIds.length === 0) {
            this.showNotification('No transactions selected', 'warning');
            return;
        }

        if (!confirm(`Are you sure you want to delete ${selectedIds.length} transactions? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch('/transactions/api/transactions/bulk', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    operation: 'delete',
                    transaction_ids: selectedIds
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.showNotification(result.message, 'success');
                location.reload();
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to delete transactions', 'error');
            }
        } catch (error) {
            console.error('Error deleting transactions:', error);
            this.showNotification('An error occurred while deleting transactions', 'error');
        }
    }

    async loadTransactionStatistics() {
        try {
            const dateRange = document.querySelector('[name="date_range"]')?.value || 'last_30_days';
            const response = await fetch(`/transactions/api/statistics?date_range=${dateRange}`);
            
            if (response.ok) {
                const stats = await response.json();
                this.updateStatisticsDisplay(stats);
            }
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    updateStatisticsDisplay(stats) {
        // Update statistics cards if they exist
        const totalIncomeEl = document.querySelector('#totalIncome');
        const totalExpensesEl = document.querySelector('#totalExpenses');
        const netIncomeEl = document.querySelector('#netIncome');

        if (totalIncomeEl) totalIncomeEl.textContent = `$${stats.summary.total_income.toFixed(2)}`;
        if (totalExpensesEl) totalExpensesEl.textContent = `$${stats.summary.total_expenses.toFixed(2)}`;
        if (netIncomeEl) netIncomeEl.textContent = `$${stats.summary.net_income.toFixed(2)}`;
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name=csrf-token]');
        return token ? token.getAttribute('content') : '';
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    showCustomDateRangeModal() {
        const modal = document.getElementById('customDateRangeModal');
        if (modal) {
            // Set default dates if they exist in URL
            const urlParams = new URLSearchParams(window.location.search);
            const startDate = urlParams.get('start_date');
            const endDate = urlParams.get('end_date');
            
            if (startDate) {
                const startDateInput = document.getElementById('startDate');
                if (startDateInput) {
                    startDateInput.value = startDate;
                }
            }
            if (endDate) {
                const endDateInput = document.getElementById('endDate');
                if (endDateInput) {
                    endDateInput.value = endDate;
                }
            }
            
            // Check if Bootstrap is available
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();
            } else {
                // Fallback: show modal manually
                modal.style.display = 'block';
                modal.classList.add('show');
                modal.setAttribute('aria-hidden', 'false');
                
                // Add backdrop
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                backdrop.id = 'customModalBackdrop';
                document.body.appendChild(backdrop);
                
                // Add close functionality
                const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"], .btn-secondary');
                closeButtons.forEach(btn => {
                    btn.addEventListener('click', () => {
                        modal.style.display = 'none';
                        modal.classList.remove('show');
                        modal.setAttribute('aria-hidden', 'true');
                        const existingBackdrop = document.getElementById('customModalBackdrop');
                        if (existingBackdrop) {
                            existingBackdrop.remove();
                        }
                    });
                });
            }
        } else {
            console.error('Custom date range modal not found');
            // Only show notification if we're on the transactions page
            if (window.location.pathname.includes('/transactions')) {
                this.showNotification('Error: Date range selector not available', 'error');
            }
        }
    }
    
    setupCustomDateRangeModal() {
        const applyButton = document.getElementById('applyCustomDateRange');
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        
        // Only log error if we're on the transactions page
        const isTransactionsPage = window.location.pathname.includes('/transactions');
        
        if (applyButton && startDateInput && endDateInput) {
            applyButton.addEventListener('click', () => {
                const startDate = startDateInput.value;
                const endDate = endDateInput.value;
                
                if (!startDate || !endDate) {
                    this.showNotification('Please select both start and end dates', 'warning');
                    return;
                }
                
                if (new Date(startDate) > new Date(endDate)) {
                    this.showNotification('Start date must be before or equal to end date', 'warning');
                    return;
                }
                
                // Update URL with custom date range
                const url = new URL(window.location);
                url.searchParams.set('filter', 'custom');
                url.searchParams.set('start_date', startDate);
                url.searchParams.set('end_date', endDate);
                
                // Remove any legacy date_range parameter
                url.searchParams.delete('date_range');
                // Remove page parameter to go back to first page
                url.searchParams.delete('page');
                
                // Close modal and redirect
                const modal = document.getElementById('customDateRangeModal');
                if (modal) {
                    // Try Bootstrap modal first
                    if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                        const bootstrapModal = bootstrap.Modal.getInstance(modal);
                        if (bootstrapModal) {
                            bootstrapModal.hide();
                        }
                    } else {
                        // Fallback: hide manually
                        modal.style.display = 'none';
                        modal.classList.remove('show');
                        modal.setAttribute('aria-hidden', 'true');
                        const existingBackdrop = document.getElementById('customModalBackdrop');
                        if (existingBackdrop) {
                            existingBackdrop.remove();
                        }
                    }
                }
                
                window.location.href = url.toString();
            });
            
            // Set max date to today for both inputs
            const today = new Date().toISOString().split('T')[0];
            startDateInput.setAttribute('max', today);
            endDateInput.setAttribute('max', today);
            
            // Update end date min when start date changes
            startDateInput.addEventListener('change', () => {
                if (startDateInput.value) {
                    endDateInput.setAttribute('min', startDateInput.value);
                }
            });
        } else if (isTransactionsPage) {
            console.warn('Custom date range modal elements not found:', {
                applyButton: !!applyButton,
                startDateInput: !!startDateInput,
                endDateInput: !!endDateInput
            });
        }
    }
}

// Transaction form validation and enhancement
class TransactionForm {
    constructor() {
        this.form = document.querySelector('form[action*="transactions"]');
        if (this.form) {
            this.init();
        }
    }

    init() {
        this.setupValidation();
        this.setupCategoryTypeIndicator();
        this.setupAmountFormatting();
    }

    setupValidation() {
        this.form.addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
            }
        });
    }

    setupCategoryTypeIndicator() {
        const categorySelect = document.querySelector('#category_id');
        const amountInput = document.querySelector('#amount');

        if (categorySelect && amountInput) {
            categorySelect.addEventListener('change', (e) => {
                const selectedOption = e.target.options[e.target.selectedIndex];
                const optgroup = selectedOption.parentElement;
                
                amountInput.classList.remove('text-success', 'text-danger');
                
                if (optgroup && optgroup.label === 'Income') {
                    amountInput.classList.add('text-success');
                } else if (optgroup && optgroup.label === 'Expenses') {
                    amountInput.classList.add('text-danger');
                }
            });

            // Trigger on page load
            categorySelect.dispatchEvent(new Event('change'));
        }
    }

    setupAmountFormatting() {
        const amountInput = document.querySelector('#amount');
        
        if (amountInput) {
            amountInput.addEventListener('blur', (e) => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value)) {
                    e.target.value = value.toFixed(2);
                }
            });
        }
    }

    validateForm() {
        const requiredFields = this.form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'This field is required');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });

        // Validate amount
        const amountInput = document.querySelector('#amount');
        if (amountInput) {
            const amount = parseFloat(amountInput.value);
            if (isNaN(amount) || amount <= 0) {
                this.showFieldError(amountInput, 'Amount must be a positive number');
                isValid = false;
            }
        }

        return isValid;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TransactionManager();
    new TransactionForm();
});

// Export for potential external use
window.TransactionManager = TransactionManager;
window.TransactionForm = TransactionForm;

// Global functions for transaction operations
function deleteTransaction(button) {
    const transactionId = button.getAttribute('data-transaction-id');
    if (confirm('Are you sure you want to delete this transaction? This action cannot be undone.')) {
        // Create and submit a form for deletion
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/transactions/${transactionId}/delete`;
        
        // Add CSRF token
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrf_token';
        // Get CSRF token from meta tag
        const csrfToken = document.querySelector('meta[name=csrf-token]');
        csrfInput.value = csrfToken ? csrfToken.getAttribute('content') : '';
        form.appendChild(csrfInput);
        
        document.body.appendChild(form);
        form.submit();
    }
}

function viewTransferFromTransaction(transferId) {
    // Redirect to account page with transfer details
    window.location.href = `/account/?show_transfer=${transferId}`;
}

function showTransferWarning() {
    alert('Transfer transactions cannot be viewed, edited or deleted directly. Please use the "View Transfer Details" button (🔄) to see the complete transfer information, or use the "Reverse Transfer" option from the Recent Quick Transfers section in the Account Overview page.');
}

// Make functions available globally
window.deleteTransaction = deleteTransaction;
window.viewTransferFromTransaction = viewTransferFromTransaction;
window.showTransferWarning = showTransferWarning;

// Initialize TransactionManager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    new TransactionManager();
});

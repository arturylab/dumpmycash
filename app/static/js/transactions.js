// Transactions JavaScript functionality
class TransactionManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupAjaxDefaults();
        this.setupModal();
        // Initialize modal instance once
        this.modalInstance = new bootstrap.Modal(document.getElementById('transactionModal'));
        
        // Check URL parameters to auto-open modal
        this.checkAndOpenModal();
        
        // Restore scroll position if available
        this.restoreScrollPosition();
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
        
        // Clear filters button
        this.setupClearFiltersButton();
        
        // Time filter dropdown
        this.setupTimeFilter();
        
        // Quick actions
        this.setupQuickActions();
        
        // Transaction row clicks
        this.setupTransactionRowClicks();
    }

    setupFilterForm() {
        // Find the filter form (now always visible)
        const filterForm = document.querySelector('#filterForm');
        if (filterForm) {
            this.setupAutoSubmitFilters(filterForm);
        }
        
        // Setup Clear Filters button to preserve current time filter
        this.setupClearFiltersButton();
    }

    setupAutoSubmitFilters(form) {
        // Auto-submit form when filters change
        const filterInputs = form.querySelectorAll('select, input[type="text"]');
        
        filterInputs.forEach(input => {
            let timeout;
            
            if (input.tagName === 'SELECT') {
                // For dropdowns, submit immediately on change
                input.addEventListener('change', () => {
                    // Special handling for time filter when "custom" is selected
                    if (input.id === 'timeFilter' && input.value === 'custom') {
                        // Show custom date range modal instead of submitting
                        const customModal = new bootstrap.Modal(document.getElementById('customDateRangeModal'));
                        customModal.show();
                        return;
                    }
                    this.submitFilterForm(form);
                });
            } else if (input.type === 'text') {
                // For text inputs, debounce to avoid too many requests
                input.addEventListener('input', () => {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        this.submitFilterForm(form);
                    }, 800); // Wait 800ms after user stops typing
                });
            }
        });
        
        console.log('Auto-submit filters setup completed');
    }

    submitFilterForm(form) {
        // Store current scroll position
        const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
        sessionStorage.setItem('transactionScrollPosition', scrollPosition);
        
        // Get current form data
        const formData = new FormData(form);
        const url = new URL(window.location);
        
        // Clear existing filter parameters
        url.searchParams.delete('category_id');
        url.searchParams.delete('account_id');
        url.searchParams.delete('search');
        url.searchParams.delete('filter');
        url.searchParams.delete('start_date');
        url.searchParams.delete('end_date');
        url.searchParams.delete('page'); // Reset to first page
        
        // Add form data to URL
        for (let [key, value] of formData.entries()) {
            if (value && key !== 'csrf_token') {
                if (key === 'time_filter') {
                    // Map time_filter to filter parameter
                    url.searchParams.set('filter', value);
                } else {
                    url.searchParams.set(key, value);
                }
            }
        }
        
        // Navigate to new URL
        window.location.href = url.toString();
    }

    restoreScrollPosition() {
        // Restore scroll position if available
        const savedScrollPosition = sessionStorage.getItem('transactionScrollPosition');
        if (savedScrollPosition) {
            // Use setTimeout to ensure the page is fully loaded before scrolling
            setTimeout(() => {
                window.scrollTo(0, parseInt(savedScrollPosition));
                // Clear the stored position after using it
                sessionStorage.removeItem('transactionScrollPosition');
            }, 100);
        }
    }

    setupClearFiltersButton() {
        const clearButton = document.querySelector('#clearFiltersBtn');
        if (clearButton) {
            clearButton.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Store current scroll position before clearing filters
                const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
                sessionStorage.setItem('transactionScrollPosition', scrollPosition);
                
                const url = new URL(window.location);
                
                // Preserve only the time filter and date range, clear everything else
                const currentFilter = url.searchParams.get('filter');
                const currentStartDate = url.searchParams.get('start_date');
                const currentEndDate = url.searchParams.get('end_date');
                
                // Create clean URL with only preserved parameters
                const cleanUrl = new URL(url.origin + url.pathname);
                
                if (currentFilter && currentFilter !== 'month') { // month is default, no need to preserve
                    cleanUrl.searchParams.set('filter', currentFilter);
                }
                if (currentStartDate) {
                    cleanUrl.searchParams.set('start_date', currentStartDate);
                }
                if (currentEndDate) {
                    cleanUrl.searchParams.set('end_date', currentEndDate);
                }
                
                // Navigate to clean URL
                window.location.href = cleanUrl.toString();
            });
        }
    }

    setupTimeFilter() {
        // Handle custom date range modal
        const applyCustomBtn = document.querySelector('#applyCustomDateRange');
        if (applyCustomBtn) {
            applyCustomBtn.addEventListener('click', () => {
                const startDate = document.querySelector('#startDate').value;
                const endDate = document.querySelector('#endDate').value;
                
                if (startDate && endDate) {
                    // Store current scroll position before applying custom date range
                    const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
                    sessionStorage.setItem('transactionScrollPosition', scrollPosition);
                    
                    const url = new URL(window.location);
                    url.searchParams.set('filter', 'custom');
                    url.searchParams.set('start_date', startDate);
                    url.searchParams.set('end_date', endDate);
                    url.searchParams.delete('page'); // Reset to first page
                    
                    window.location.href = url.toString();
                }
            });
        }
    }

    setupQuickActions() {
        // Already handled by time filter
    }

    setupTransactionRowClicks() {
        const transactionRows = document.querySelectorAll('.transaction-row');
        transactionRows.forEach(row => {
            row.addEventListener('click', (e) => {
                e.preventDefault();
                const transactionId = row.getAttribute('data-transaction-id');
                const isTransfer = row.getAttribute('data-is-transfer') === 'true';
                
                if (isTransfer) {
                    // Show warning for transfer transactions
                    alert('Transfer transactions cannot be edited directly. Please use the Account page to manage transfers.');
                } else {
                    // Open edit modal for regular transactions
                    this.openEditModal(transactionId);
                }
            });
        });
    }

    setupModal() {
        const modal = document.getElementById('transactionModal');
        const form = document.getElementById('transactionForm');
        const saveBtn = document.getElementById('saveTransactionBtn');
        const deleteBtn = document.getElementById('deleteTransactionBtn');

        // Save transaction button
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveTransaction();
            });
        }

        // Delete transaction button
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                this.showDeleteConfirmationModal();
            });
        }

        // Reset form when modal is hidden
        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => {
                this.resetForm();
                // Force cleanup of any bootstrap modal backdrop
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => backdrop.remove());
                // Remove modal-open class from body if it's stuck
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            });
        }
        
        // Delete confirmation button
        const confirmDeleteBtn = document.getElementById('confirmDeleteTransaction');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => {
                this.confirmDeleteTransaction();
            });
        }
    }

    openAddModal() {
        const modalTitle = document.getElementById('transactionModalLabel');
        const deleteBtn = document.getElementById('deleteTransactionBtn');
        
        modalTitle.textContent = 'Add Transaction';
        deleteBtn.style.display = 'none';
        this.resetForm();
        
        // Set current date/time
        const now = new Date();
        // Format as YYYY-MM-DDTHH:MM in local time
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const dateString = `${year}-${month}-${day}T${hours}:${minutes}`;
        document.getElementById('date').value = dateString;
        
        this.modalInstance.show();
    }

    async openEditModal(transactionId) {
        try {
            const response = await fetch(`/transactions/api/transactions/${transactionId}`);
            if (!response.ok) throw new Error('Failed to fetch transaction');
            
            const transaction = await response.json();
            
            const modalTitle = document.getElementById('transactionModalLabel');
            const deleteBtn = document.getElementById('deleteTransactionBtn');
            
            modalTitle.textContent = 'Edit Transaction';
            deleteBtn.style.display = 'inline-block';
            
            // Reset form first to clear any previous data
            this.resetForm();
            
            // Populate form with all transaction data
            document.getElementById('transactionId').value = transaction.id;
            document.getElementById('amount').value = transaction.amount;
            document.getElementById('description').value = transaction.description || '';
            
            // Set account and category immediately
            document.getElementById('modal_account_id').value = transaction.account.id;
            document.getElementById('modal_category_id').value = transaction.category.id;
            
            // Format date for datetime-local input (local time, not UTC)
            const date = new Date(transaction.date);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const dateString = `${year}-${month}-${day}T${hours}:${minutes}`;
            document.getElementById('date').value = dateString;
            
            // Show modal first, then set dropdown values
            this.modalInstance.show();
            
            // Wait a bit for modal to be fully visible, then verify and ensure dropdown values are set
            setTimeout(() => {
                // Verify account dropdown is correctly set
                const accountSelect = document.getElementById('modal_account_id');
                if (accountSelect.value !== transaction.account.id.toString()) {
                    console.log('Re-setting modal_account_id to:', transaction.account.id);
                    accountSelect.value = transaction.account.id;
                }
                console.log('Account select value:', accountSelect.value);
                
                // Verify category dropdown is correctly set
                const categorySelect = document.getElementById('modal_category_id');
                if (categorySelect.value !== transaction.category.id.toString()) {
                    console.log('Re-setting modal_category_id to:', transaction.category.id);
                    categorySelect.value = transaction.category.id;
                }
                console.log('Category select value:', categorySelect.value);
                
                // Trigger change events to ensure proper selection
                accountSelect.dispatchEvent(new Event('change'));
                categorySelect.dispatchEvent(new Event('change'));
                
                // Final verification that the select values are correctly set
                console.log('Final form values verification:', {
                    accountSelected: accountSelect.value,
                    categorySelected: categorySelect.value,
                    amountValue: document.getElementById('amount').value,
                    descriptionValue: document.getElementById('description').value,
                    expectedAccount: transaction.account.id,
                    expectedCategory: transaction.category.id
                });
            }, 100); // Small delay to ensure modal is fully rendered
            
        } catch (error) {
            console.error('Error loading transaction:', error);
            alert('Error loading transaction details');
        }
    }

    async saveTransaction() {
        const form = document.getElementById('transactionForm');
        const formData = new FormData(form);
        const transactionId = document.getElementById('transactionId').value;
        
        try {
            let url, method;
            if (transactionId) {
                // Update existing transaction
                url = `/transactions/api/transactions/${transactionId}`;
                method = 'PUT';
            } else {
                // Create new transaction
                url = '/transactions/api/transactions';
                method = 'POST';
            }

            // Convert FormData to JSON
            const data = {};
            for (let [key, value] of formData.entries()) {
                if (key !== 'csrf_token' && key !== 'transaction_id') {
                    data[key] = value;
                }
            }

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': formData.get('csrf_token')
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save transaction');
            }

            // Close modal first
            this.modalInstance.hide();
            
            // Redirect to success page which will show flash message and then redirect back
            const operation = transactionId ? 'update' : 'create';
            window.location.href = `/transactions/success/${operation}`;

        } catch (error) {
            console.error('Error saving transaction:', error);
            
            // Close modal and redirect to error page
            this.modalInstance.hide();
            const errorMessage = encodeURIComponent(error.message);
            window.location.href = `/transactions/error/save?message=${errorMessage}`;
        }
    }

    async deleteTransaction() {
        const transactionId = document.getElementById('transactionId').value;
        if (!transactionId) return;

        if (!confirm('Are you sure you want to delete this transaction? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/transactions/api/transactions/${transactionId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to delete transaction');
            }

            // Close modal and refresh page
            this.modalInstance.hide();
            window.location.reload();

        } catch (error) {
            console.error('Error deleting transaction:', error);
            alert(`Error deleting transaction: ${error.message}`);
        }
    }

    showDeleteConfirmationModal() {
        const transactionId = document.getElementById('transactionId').value;
        if (!transactionId) return;

        // Get current transaction data from the form
        const amount = document.getElementById('amount').value;
        const description = document.getElementById('description').value || 'No description';
        const accountSelect = document.getElementById('modal_account_id');
        const categorySelect = document.getElementById('modal_category_id');
        const date = document.getElementById('date').value;

        // Get selected account and category names
        const accountName = accountSelect.options[accountSelect.selectedIndex]?.text || 'Unknown Account';
        const categoryName = categorySelect.options[categorySelect.selectedIndex]?.text || 'Unknown Category';

        // Format date for display
        let formattedDate = 'Unknown Date';
        if (date) {
            try {
                const dateObj = new Date(date);
                formattedDate = dateObj.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (e) {
                formattedDate = date;
            }
        }

        // Populate delete confirmation modal
        document.getElementById('deleteTransactionAmount').textContent = `$${parseFloat(amount || 0).toFixed(2)}`;
        document.getElementById('deleteTransactionDescription').textContent = description;
        document.getElementById('deleteTransactionAccount').textContent = accountName;
        document.getElementById('deleteTransactionCategory').textContent = categoryName;
        document.getElementById('deleteTransactionDate').textContent = formattedDate;

        // Store transaction ID for deletion
        document.getElementById('confirmDeleteTransaction').setAttribute('data-transaction-id', transactionId);

        // Close the transaction modal first
        this.modalInstance.hide();

        // Show delete confirmation modal after a short delay
        setTimeout(() => {
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteTransactionModal'));
            deleteModal.show();
        }, 300);
    }

    async confirmDeleteTransaction() {
        const confirmBtn = document.getElementById('confirmDeleteTransaction');
        const transactionId = confirmBtn.getAttribute('data-transaction-id');
        
        if (!transactionId) return;

        // Show loading state
        const spinner = confirmBtn.querySelector('.spinner-border');
        const originalHTML = confirmBtn.innerHTML;
        confirmBtn.disabled = true;
        spinner.classList.remove('d-none');

        try {
            const response = await fetch(`/transactions/api/transactions/${transactionId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to delete transaction');
            }

            // Close delete modal
            const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteTransactionModal'));
            if (deleteModal) {
                deleteModal.hide();
            }

            // Redirect to success page which will show flash message and then redirect back
            window.location.href = '/transactions/success/delete';

        } catch (error) {
            console.error('Error deleting transaction:', error);
            
            // Close modal and redirect to error page
            const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteTransactionModal'));
            if (deleteModal) {
                deleteModal.hide();
            }
            
            const errorMessage = encodeURIComponent(error.message);
            window.location.href = `/transactions/error/delete?message=${errorMessage}`;
        } finally {
            // Reset button state
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = originalHTML;
        }
    }

    resetForm() {
        const form = document.getElementById('transactionForm');
        form.reset();
        document.getElementById('transactionId').value = '';
    }

    applyTimeFilter(filter) {
        // Store current scroll position before applying time filter
        const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
        sessionStorage.setItem('transactionScrollPosition', scrollPosition);
        
        const url = new URL(window.location);
        url.searchParams.set('filter', filter);
        url.searchParams.delete('start_date');
        url.searchParams.delete('end_date');
        url.searchParams.delete('page'); // Reset to first page
        
        window.location.href = url.toString();
    }

    checkAndOpenModal() {
        const urlParams = new URLSearchParams(window.location.search);
        const openModal = urlParams.get('openModal');
        
        if (openModal === 'addTransaction') {
            // Wait a bit for the page to fully load, then open the modal
            setTimeout(() => {
                this.openAddModal();
                // Clean up the URL parameter
                const url = new URL(window.location);
                url.searchParams.delete('openModal');
                window.history.replaceState({}, '', url.toString());
            }, 500);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const transactionManager = new TransactionManager();
});

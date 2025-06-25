/**
 * Transaction Management JavaScript Module
 * 
 * Handles all transaction-related frontend functionality including:
 * - Transaction filtering and search
 * - Modal operations for add/edit/delete
 * - Form validation and submission
 * - AJAX operations with proper error handling
 * - URL state management and scroll position restoration
 * 
 * @class TransactionManager
 */
class TransactionManager {
    constructor() {
        this.modalInstance = null;
        this.init();
    }

    /**
     * Initialize the transaction manager
     */
    init() {
        this.setupEventListeners();
        this.setupAjaxDefaults();
        this.setupModal();
        this.initializeModal();
        this.checkAndOpenModal();
        this.restoreScrollPosition();
    }

    /**
     * Initialize modal instance
     */
    initializeModal() {
        const modalElement = document.getElementById('transactionModal');
        if (modalElement) {
            this.modalInstance = new bootstrap.Modal(modalElement);
        }
    }

    /**
     * Setup CSRF token for AJAX requests
     */
    setupAjaxDefaults() {
        const csrfToken = document.querySelector('meta[name=csrf-token]');
        if (csrfToken) {
            this.csrfToken = csrfToken.getAttribute('content');
        }
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        this.setupFilterForm();
        this.setupClearFiltersButton();
        this.setupTimeFilter();
        this.setupTransactionRowClicks();
    }

    /**
     * Setup filter form with auto-submission
     */
    setupFilterForm() {
        const filterForm = document.querySelector('#filterForm');
        if (filterForm) {
            this.setupAutoSubmitFilters(filterForm);
        }
    }

    /**
     * Setup auto-submit functionality for filter inputs
     * @param {HTMLFormElement} form - The filter form element
     */
    setupAutoSubmitFilters(form) {
        const filterInputs = form.querySelectorAll('select, input[type="text"]');
        
        filterInputs.forEach(input => {
            let timeout;
            
            if (input.tagName === 'SELECT') {
                input.addEventListener('change', () => {
                    // Special handling for custom time filter
                    if (input.id === 'timeFilter' && input.value === 'custom') {
                        this.showCustomDateRangeModal();
                        return;
                    }
                    this.submitFilterForm(form);
                });
            } else if (input.type === 'text') {
                // Debounce text inputs to avoid excessive requests
                input.addEventListener('input', () => {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        this.submitFilterForm(form);
                    }, 800);
                });
            }
        });
    }

    /**
     * Submit filter form and update URL
     * @param {HTMLFormElement} form - The filter form element
     */
    submitFilterForm(form) {
        this.saveScrollPosition();
        
        const formData = new FormData(form);
        const url = new URL(window.location);
        
        // Clear existing filter parameters
        this.clearFilterParams(url);
        
        // Add form data to URL
        for (let [key, value] of formData.entries()) {
            if (value && key !== 'csrf_token') {
                if (key === 'time_filter') {
                    url.searchParams.set('filter', value);
                } else {
                    url.searchParams.set(key, value);
                }
            }
        }
        
        window.location.href = url.toString();
    }

    /**
     * Clear filter parameters from URL
     * @param {URL} url - The URL object to modify
     */
    clearFilterParams(url) {
        const paramsToRemove = ['category_id', 'account_id', 'search', 'filter', 'start_date', 'end_date', 'page'];
        paramsToRemove.forEach(param => url.searchParams.delete(param));
    }

    /**
     * Save current scroll position to session storage
     */
    saveScrollPosition() {
        const scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
        sessionStorage.setItem('transactionScrollPosition', scrollPosition);
    }

    /**
     * Restore scroll position from session storage
     */
    restoreScrollPosition() {
        const savedScrollPosition = sessionStorage.getItem('transactionScrollPosition');
        if (savedScrollPosition) {
            setTimeout(() => {
                window.scrollTo(0, parseInt(savedScrollPosition));
                sessionStorage.removeItem('transactionScrollPosition');
            }, 100);
        }
    }

    /**
     * Setup clear filters button
     */
    setupClearFiltersButton() {
        const clearButton = document.querySelector('#clearFiltersBtn');
        if (clearButton) {
            clearButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.clearFilters();
            });
        }
    }

    /**
     * Clear all filters including time filter and date range
     */
    clearFilters() {
        this.saveScrollPosition();
        
        const url = new URL(window.location);
        
        // Create clean URL with only the base path - remove all filter parameters
        const cleanUrl = new URL(url.origin + url.pathname);
        
        window.location.href = cleanUrl.toString();
    }

    /**
     * Setup time filter functionality
     */
    setupTimeFilter() {
        const applyCustomBtn = document.querySelector('#applyCustomDateRange');
        if (applyCustomBtn) {
            applyCustomBtn.addEventListener('click', () => {
                this.applyCustomDateRange();
            });
        }
    }

    /**
     * Show custom date range modal
     */
    showCustomDateRangeModal() {
        const customModal = new bootstrap.Modal(document.getElementById('customDateRangeModal'));
        customModal.show();
    }

    /**
     * Apply custom date range filter
     */
    applyCustomDateRange() {
        const startDate = document.querySelector('#startDate').value;
        const endDate = document.querySelector('#endDate').value;
        
        if (startDate && endDate) {
            this.saveScrollPosition();
            
            const url = new URL(window.location);
            url.searchParams.set('filter', 'custom');
            url.searchParams.set('start_date', startDate);
            url.searchParams.set('end_date', endDate);
            url.searchParams.delete('page');
            
            window.location.href = url.toString();
        }
    }

    /**
     * Setup transaction row click handlers
     */
    setupTransactionRowClicks() {
        const transactionRows = document.querySelectorAll('.transaction-row');
        transactionRows.forEach(row => {
            row.addEventListener('click', (e) => {
                e.preventDefault();
                const transactionId = row.getAttribute('data-transaction-id');
                const isTransfer = row.getAttribute('data-is-transfer') === 'true';
                
                if (isTransfer) {
                    this.showTransferWarning();
                } else {
                    this.openEditModal(transactionId);
                }
            });
        });
    }

    /**
     * Show warning for transfer transactions
     */
    showTransferWarning() {
        alert('Transfer transactions cannot be edited directly. Please use the Account page to manage transfers.');
    }

    /**
     * Setup modal event listeners
     */
    setupModal() {
        const modal = document.getElementById('transactionModal');
        const form = document.getElementById('transactionForm');
        const saveBtn = document.getElementById('saveTransactionBtn');
        const deleteBtn = document.getElementById('deleteTransactionBtn');
        const confirmDeleteBtn = document.getElementById('confirmDeleteTransaction');

        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveTransaction());
        }

        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => this.showDeleteConfirmationModal());
        }

        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => this.confirmDeleteTransaction());
        }

        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => this.handleModalHidden());
        }
    }

    /**
     * Handle modal hidden event
     */
    handleModalHidden() {
        this.resetForm();
        this.cleanupModalBackdrop();
    }

    /**
     * Clean up modal backdrop and body classes
     */
    cleanupModalBackdrop() {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }

    /**
     * Open modal for adding new transaction
     */
    openAddModal() {
        const modalTitle = document.getElementById('transactionModalLabel');
        const deleteBtn = document.getElementById('deleteTransactionBtn');
        
        modalTitle.textContent = 'Add Transaction';
        deleteBtn.style.display = 'none';
        this.resetForm();
        this.setCurrentDateTime();
        
        if (this.modalInstance) {
            this.modalInstance.show();
        }
    }

    /**
     * Set current date and time in the form
     */
    setCurrentDateTime() {
        const now = new Date();
        const dateString = this.formatDateTimeLocal(now);
        document.getElementById('date').value = dateString;
    }

    /**
     * Format date for datetime-local input
     * @param {Date} date - Date object to format
     * @returns {string} Formatted date string
     */
    formatDateTimeLocal(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    /**
     * Open modal for editing existing transaction
     * @param {number} transactionId - ID of transaction to edit
     */
    async openEditModal(transactionId) {
        try {
            const transaction = await this.fetchTransaction(transactionId);
            this.populateEditModal(transaction);
        } catch (error) {
            console.error('Error loading transaction:', error);
            alert('Error loading transaction details');
        }
    }

    /**
     * Fetch transaction data from API
     * @param {number} transactionId - Transaction ID
     * @returns {Promise<Object>} Transaction data
     */
    async fetchTransaction(transactionId) {
        const response = await fetch(`/transactions/api/transactions/${transactionId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch transaction');
        }
        return await response.json();
    }

    /**
     * Populate modal with transaction data for editing
     * @param {Object} transaction - Transaction data
     */
    populateEditModal(transaction) {
        const modalTitle = document.getElementById('transactionModalLabel');
        const deleteBtn = document.getElementById('deleteTransactionBtn');
        
        modalTitle.textContent = 'Edit Transaction';
        deleteBtn.style.display = 'inline-block';
        
        this.resetForm();
        this.fillTransactionForm(transaction);
        
        if (this.modalInstance) {
            this.modalInstance.show();
        }
        
        // Ensure dropdowns are properly set after modal is visible
        setTimeout(() => this.verifyFormValues(transaction), 100);
    }

    /**
     * Fill form with transaction data
     * @param {Object} transaction - Transaction data
     */
    fillTransactionForm(transaction) {
        document.getElementById('transactionId').value = transaction.id;
        document.getElementById('amount').value = transaction.amount;
        document.getElementById('description').value = transaction.description || '';
        document.getElementById('modal_account_id').value = transaction.account.id;
        document.getElementById('modal_category_id').value = transaction.category.id;
        
        // Format date for datetime-local input
        const date = new Date(transaction.date);
        const dateString = this.formatDateTimeLocal(date);
        document.getElementById('date').value = dateString;
    }

    /**
     * Verify and ensure form values are correctly set
     * @param {Object} transaction - Expected transaction data
     */
    verifyFormValues(transaction) {
        const accountSelect = document.getElementById('modal_account_id');
        const categorySelect = document.getElementById('modal_category_id');
        
        // Re-set values if they didn't stick
        if (accountSelect.value !== transaction.account.id.toString()) {
            accountSelect.value = transaction.account.id;
        }
        
        if (categorySelect.value !== transaction.category.id.toString()) {
            categorySelect.value = transaction.category.id;
        }
        
        // Trigger change events
        accountSelect.dispatchEvent(new Event('change'));
        categorySelect.dispatchEvent(new Event('change'));
    }

    /**
     * Save transaction (create or update)
     */
    async saveTransaction() {
        const form = document.getElementById('transactionForm');
        const formData = new FormData(form);
        const transactionId = document.getElementById('transactionId').value;
        
        try {
            const { url, method } = this.getTransactionEndpoint(transactionId);
            const data = this.convertFormDataToJson(formData);
            
            const response = await this.submitTransactionData(url, method, data, formData);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to save transaction');
            }

            this.handleTransactionSaveSuccess(transactionId);

        } catch (error) {
            this.handleTransactionSaveError(error);
        }
    }

    /**
     * Get transaction endpoint URL and method
     * @param {string} transactionId - Transaction ID (empty for new transaction)
     * @returns {Object} Object with url and method
     */
    getTransactionEndpoint(transactionId) {
        if (transactionId) {
            return {
                url: `/transactions/api/transactions/${transactionId}`,
                method: 'PUT'
            };
        } else {
            return {
                url: '/transactions/api/transactions',
                method: 'POST'
            };
        }
    }

    /**
     * Convert FormData to JSON object
     * @param {FormData} formData - Form data to convert
     * @returns {Object} JSON object
     */
    convertFormDataToJson(formData) {
        const data = {};
        for (let [key, value] of formData.entries()) {
            if (key !== 'csrf_token' && key !== 'transaction_id') {
                data[key] = value;
            }
        }
        return data;
    }

    /**
     * Submit transaction data to API
     * @param {string} url - API endpoint URL
     * @param {string} method - HTTP method
     * @param {Object} data - Transaction data
     * @param {FormData} formData - Original form data (for CSRF token)
     * @returns {Promise<Response>} Fetch response
     */
    async submitTransactionData(url, method, data, formData) {
        return await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': formData.get('csrf_token')
            },
            body: JSON.stringify(data)
        });
    }

    /**
     * Handle successful transaction save
     * @param {string} transactionId - Transaction ID (empty for new transaction)
     */
    handleTransactionSaveSuccess(transactionId) {
        if (this.modalInstance) {
            this.modalInstance.hide();
        }
        
        const operation = transactionId ? 'update' : 'create';
        window.location.href = `/transactions/success/${operation}`;
    }

    /**
     * Handle transaction save error
     * @param {Error} error - Error object
     */
    handleTransactionSaveError(error) {
        console.error('Error saving transaction:', error);
        
        if (this.modalInstance) {
            this.modalInstance.hide();
        }
        
        const errorMessage = encodeURIComponent(error.message);
        window.location.href = `/transactions/error/save?message=${errorMessage}`;
    }

    /**
     * Delete transaction (legacy method - kept for compatibility)
     * @deprecated Use showDeleteConfirmationModal instead
     */
    async deleteTransaction() {
        const transactionId = document.getElementById('transactionId').value;
        if (!transactionId) return;

        if (!confirm('Are you sure you want to delete this transaction? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await this.performDeleteTransaction(transactionId);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to delete transaction');
            }

            if (this.modalInstance) {
                this.modalInstance.hide();
            }
            window.location.reload();

        } catch (error) {
            console.error('Error deleting transaction:', error);
            alert(`Error deleting transaction: ${error.message}`);
        }
    }

    /**
     * Show delete confirmation modal with transaction details
     */
    showDeleteConfirmationModal() {
        const transactionId = document.getElementById('transactionId').value;
        if (!transactionId) return;

        const transactionData = this.getTransactionDataFromForm();
        this.populateDeleteModal(transactionData);
        this.setDeleteModalTransactionId(transactionId);
        
        if (this.modalInstance) {
            this.modalInstance.hide();
        }
        
        setTimeout(() => this.showDeleteModal(), 300);
    }

    /**
     * Get transaction data from form
     * @returns {Object} Transaction data from form
     */
    getTransactionDataFromForm() {
        const amount = document.getElementById('amount').value;
        const description = document.getElementById('description').value || 'No description';
        const accountSelect = document.getElementById('modal_account_id');
        const categorySelect = document.getElementById('modal_category_id');
        const date = document.getElementById('date').value;

        return {
            amount,
            description,
            accountName: accountSelect.options[accountSelect.selectedIndex]?.text || 'Unknown Account',
            categoryName: categorySelect.options[categorySelect.selectedIndex]?.text || 'Unknown Category',
            formattedDate: this.formatDateForDisplay(date)
        };
    }

    /**
     * Format date for display in delete modal
     * @param {string} dateValue - Date string from form
     * @returns {string} Formatted date string
     */
    formatDateForDisplay(dateValue) {
        if (!dateValue) return 'Unknown Date';
        
        try {
            const dateObj = new Date(dateValue);
            return dateObj.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateValue;
        }
    }

    /**
     * Populate delete confirmation modal with transaction data
     * @param {Object} transactionData - Transaction data to display
     */
    populateDeleteModal(transactionData) {
        document.getElementById('deleteTransactionAmount').textContent = 
            `$${parseFloat(transactionData.amount || 0).toFixed(2)}`;
        document.getElementById('deleteTransactionDescription').textContent = transactionData.description;
        document.getElementById('deleteTransactionAccount').textContent = transactionData.accountName;
        document.getElementById('deleteTransactionCategory').textContent = transactionData.categoryName;
        document.getElementById('deleteTransactionDate').textContent = transactionData.formattedDate;
    }

    /**
     * Set transaction ID for deletion
     * @param {string} transactionId - Transaction ID
     */
    setDeleteModalTransactionId(transactionId) {
        document.getElementById('confirmDeleteTransaction').setAttribute('data-transaction-id', transactionId);
    }

    /**
     * Show delete confirmation modal
     */
    showDeleteModal() {
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteTransactionModal'));
        deleteModal.show();
    }

    /**
     * Confirm and execute transaction deletion
     */
    async confirmDeleteTransaction() {
        const confirmBtn = document.getElementById('confirmDeleteTransaction');
        const transactionId = confirmBtn.getAttribute('data-transaction-id');
        
        if (!transactionId) return;

        this.setDeleteButtonLoading(confirmBtn, true);

        try {
            const response = await this.performDeleteTransaction(transactionId);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to delete transaction');
            }

            this.hideDeleteModal();
            window.location.href = '/transactions/success/delete';

        } catch (error) {
            console.error('Error deleting transaction:', error);
            this.hideDeleteModal();
            
            const errorMessage = encodeURIComponent(error.message);
            window.location.href = `/transactions/error/delete?message=${errorMessage}`;
        } finally {
            this.setDeleteButtonLoading(confirmBtn, false);
        }
    }

    /**
     * Perform the actual transaction deletion API call
     * @param {string} transactionId - Transaction ID to delete
     * @returns {Promise<Response>} Fetch response
     */
    async performDeleteTransaction(transactionId) {
        return await fetch(`/transactions/api/transactions/${transactionId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            }
        });
    }

    /**
     * Set loading state for delete button
     * @param {HTMLElement} button - Delete button element
     * @param {boolean} isLoading - Whether to show loading state
     */
    setDeleteButtonLoading(button, isLoading) {
        const spinner = button.querySelector('.spinner-border');
        
        if (isLoading) {
            button.disabled = true;
            if (spinner) spinner.classList.remove('d-none');
        } else {
            button.disabled = false;
            if (spinner) spinner.classList.add('d-none');
        }
    }

    /**
     * Hide delete confirmation modal
     */
    hideDeleteModal() {
        const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteTransactionModal'));
        if (deleteModal) {
            deleteModal.hide();
        }
    }

    /**
     * Reset transaction form
     */
    resetForm() {
        const form = document.getElementById('transactionForm');
        if (form) {
            form.reset();
            document.getElementById('transactionId').value = '';
        }
    }

    /**
     * Apply time filter and navigate to filtered view
     * @param {string} filter - Time filter value
     */
    applyTimeFilter(filter) {
        this.saveScrollPosition();
        
        const url = new URL(window.location);
        url.searchParams.set('filter', filter);
        url.searchParams.delete('start_date');
        url.searchParams.delete('end_date');
        url.searchParams.delete('page');
        
        window.location.href = url.toString();
    }

    /**
     * Check URL parameters and auto-open modal if requested
     */
    checkAndOpenModal() {
        const urlParams = new URLSearchParams(window.location.search);
        const openModal = urlParams.get('openModal');
        
        if (openModal === 'addTransaction') {
            setTimeout(() => {
                this.openAddModal();
                this.cleanupUrlParameter('openModal');
            }, 500);
        }
    }

    /**
     * Clean up URL parameter after use
     * @param {string} paramName - Parameter name to remove
     */
    cleanupUrlParameter(paramName) {
        const url = new URL(window.location);
        url.searchParams.delete(paramName);
        window.history.replaceState({}, '', url.toString());
    }
}

// Initialize transaction manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new TransactionManager();
});

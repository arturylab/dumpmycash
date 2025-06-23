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
        
        // Transaction row clicks
        this.setupTransactionRowClicks();
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
                if (e.target.classList.contains('dropdown-item')) {
                    e.preventDefault();
                    
                    const filter = e.target.getAttribute('data-filter');
                    const filterText = e.target.textContent;
                    
                    if (filter === 'custom') {
                        // Show custom date range modal
                        const customModal = new bootstrap.Modal(document.getElementById('customDateRangeModal'));
                        customModal.show();
                    } else {
                        // Apply the filter immediately
                        this.applyTimeFilter(filter, filterText);
                    }
                }
            });
        }

        // Handle custom date range modal
        const applyCustomBtn = document.querySelector('#applyCustomDateRange');
        if (applyCustomBtn) {
            applyCustomBtn.addEventListener('click', () => {
                const startDate = document.querySelector('#startDate').value;
                const endDate = document.querySelector('#endDate').value;
                
                if (startDate && endDate) {
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
        const addBtn = document.getElementById('addTransactionBtn');
        const addBtnEmpty = document.getElementById('addTransactionBtnEmpty');

        // Add transaction buttons
        if (addBtn) {
            addBtn.addEventListener('click', () => {
                this.openAddModal();
            });
        }
        
        if (addBtnEmpty) {
            addBtnEmpty.addEventListener('click', () => {
                this.openAddModal();
            });
        }

        // Save transaction button
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.saveTransaction();
            });
        }

        // Delete transaction button
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                if (confirm('Are you sure you want to delete this transaction?')) {
                    this.deleteTransaction();
                }
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

            // Close modal and refresh page
            this.modalInstance.hide();
            window.location.reload();

        } catch (error) {
            console.error('Error saving transaction:', error);
            alert(`Error saving transaction: ${error.message}`);
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

    resetForm() {
        const form = document.getElementById('transactionForm');
        form.reset();
        document.getElementById('transactionId').value = '';
    }

    applyTimeFilter(filter, filterText) {
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

/**
 * Category Management JavaScript Module
 * 
 * Handles all category-related frontend functionality including:
 * - Category CRUD operations (Create, Read, Update, Delete)
 * - Modal management for add/edit/delete operations
 * - Emoji picker functionality
 * - Time filtering for category statistics
 * - Top expenses chart rendering
 * - Form validation and error handling
 * 
 * @class CategoryManager
 */
class CategoryManager {
    constructor() {
        this.csrfToken = null;
        this.currentCategoryId = null;
        this.topExpensesChart = null;
        
        this.init();
    }

    /**
     * Initialize the category manager
     */
    init() {
        this.setupCSRFToken();
        this.initializeEmojiPickers();
        this.setupEventListeners();
        this.initializeTopExpensesChart();
    }

    /**
     * Setup CSRF token for API requests
     */
    setupCSRFToken() {
        const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');
        
        if (!csrfToken) {
            console.warn('CSRF token not found in meta tag');
        } else {
            this.csrfToken = csrfToken;
        }
    }

    /**
     * Get DOM elements for category management
     */
    getElements() {
        return {
            addCategoryModal: document.getElementById('addCategoryModal'),
            editCategoryModal: document.getElementById('editCategoryModal'),
            deleteCategoryModal: document.getElementById('deleteCategoryModal'),
            
            addCategoryForm: document.getElementById('addCategoryForm'),
            editCategoryForm: document.getElementById('editCategoryForm'),
            
            saveAddCategoryBtn: document.getElementById('saveAddCategory'),
            saveEditCategoryBtn: document.getElementById('saveEditCategory'),
            deleteCategoryBtn: document.getElementById('deleteCategoryBtn'),
            confirmDeleteCategoryBtn: document.getElementById('confirmDeleteCategory')
        };
    }

    /**
     * Emoji categories for picker functionality
     */
    getEmojiCategories() {
        return {
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
    }

    /**
     * Get emoji category labels for display
     */
    getEmojiCategoryLabels() {
        return {
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
    }

    /**
     * Initialize emoji pickers for both add and edit modals
     */
    initializeEmojiPickers() {
        this.initializeEmojiPicker('addEmojiGrid', 'addCategoryEmoji');
        this.initializeEmojiPicker('editEmojiGrid', 'editCategoryEmoji');
    }

    /**
     * Initialize a single emoji picker
     * @param {string} gridId - ID of the emoji grid container
     * @param {string} inputId - ID of the target input field
     */
    initializeEmojiPicker(gridId, inputId) {
        const grid = document.getElementById(gridId);
        if (!grid) return;
        
        grid.innerHTML = '';
        
        const emojiCategories = this.getEmojiCategories();
        const categoryLabels = this.getEmojiCategoryLabels();
        
        let content = '';
        
        Object.keys(emojiCategories).forEach(category => {
            content += `<div class="mb-3">
                <div class="fw-bold text-secondary mb-1" style="font-size: 0.75rem;">${categoryLabels[category]}</div>
                <div class="row g-1">`;
            
            emojiCategories[category].forEach(emoji => {
                content += `<div class="col-auto">
                    <button type="button" class="btn btn-sm btn-outline-secondary emoji-btn" 
                            data-emoji="${emoji}" data-target="${inputId}" 
                            style="width: 2.5rem; height: 2.5rem; padding: 0.25rem;">
                        ${emoji}
                    </button>
                </div>`;
            });
            
            content += '</div></div>';
        });
        
        grid.innerHTML = content;
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        this.setupEmojiSelection();
        this.setupModalEventListeners();
        this.setupFormSubmissions();
        this.setupTimeFilterSelection();
        this.setupCategoryActionButtons();
    }

    /**
     * Setup emoji selection functionality
     */
    setupEmojiSelection() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('emoji-btn')) {
                const emoji = e.target.getAttribute('data-emoji');
                const targetInputId = e.target.getAttribute('data-target');
                const targetInput = document.getElementById(targetInputId);
                
                if (targetInput) {
                    targetInput.value = emoji;
                    
                    // Close the dropdown
                    const dropdown = bootstrap.Dropdown.getInstance(e.target.closest('.dropdown').querySelector('[data-bs-toggle="dropdown"]'));
                    if (dropdown) {
                        dropdown.hide();
                    }
                }
            }
        });
    }

    /**
     * Setup modal event listeners
     */
    setupModalEventListeners() {
        const elements = this.getElements();
        
        // Reset Add Category form when modal is shown
        if (elements.addCategoryModal) {
            elements.addCategoryModal.addEventListener('show.bs.modal', () => {
                this.clearFieldErrors(elements.addCategoryForm);
                elements.addCategoryForm.reset();
                document.getElementById('addCategoryModalLabel').textContent = 'Add Category';
                document.getElementById('addCategoryEmoji').placeholder = '💵';
            });
        }
        
        // Clean up Edit Category form when modal is hidden
        if (elements.editCategoryModal) {
            elements.editCategoryModal.addEventListener('hidden.bs.modal', () => {
                elements.editCategoryForm.reset();
                this.currentCategoryId = null;
                this.clearFieldErrors(elements.editCategoryForm);
            });
        }
    }

    /**
     * Setup form submission handlers
     */
    setupFormSubmissions() {
        const elements = this.getElements();
        
        // Add category form submission
        if (elements.saveAddCategoryBtn) {
            elements.saveAddCategoryBtn.addEventListener('click', () => {
                this.handleAddCategory();
            });
        }
        
        // Edit category form submission
        if (elements.saveEditCategoryBtn) {
            elements.saveEditCategoryBtn.addEventListener('click', () => {
                this.handleEditCategory();
            });
        }
        
        // Delete category button
        if (elements.deleteCategoryBtn) {
            elements.deleteCategoryBtn.addEventListener('click', () => {
                this.handleDeleteCategoryRequest();
            });
        }
        
        // Confirm delete category
        if (elements.confirmDeleteCategoryBtn) {
            elements.confirmDeleteCategoryBtn.addEventListener('click', () => {
                this.handleConfirmDeleteCategory();
            });
        }
    }

    /**
     * Setup time filter selection
     */
    setupTimeFilterSelection() {
        document.addEventListener('click', (e) => {
            if (e.target.hasAttribute('data-filter')) {
                e.preventDefault();
                const filter = e.target.getAttribute('data-filter');
                
                if (filter === 'custom') {
                    this.showCustomDateRangeModal();
                    return;
                }
                
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
                    'custom': 'Custom Range',
                    'all': 'All Time'
                };
                
                const currentFilterElement = document.getElementById('currentFilter');
                if (currentFilterElement) {
                    currentFilterElement.textContent = filterNames[filter];
                }
                
                // Update chart immediately before page reload
                this.loadTopExpensesChart(filter);
                
                // Reload page with new filter
                const url = new URL(window.location);
                url.searchParams.set('filter', filter);
                // Remove custom date params when switching to non-custom filter
                if (filter !== 'custom') {
                    url.searchParams.delete('start_date');
                    url.searchParams.delete('end_date');
                }
                window.location.href = url.toString();
            }
        });
        
        // Setup custom date range modal
        const applyCustomBtn = document.querySelector('#applyCustomDateRange');
        if (applyCustomBtn) {
            applyCustomBtn.addEventListener('click', () => {
                this.applyCustomDateRange();
            });
        }
    }

    /**
     * Setup category action buttons (edit)
     */
    setupCategoryActionButtons() {
        document.addEventListener('click', (e) => {
            // Handle edit category buttons - check both button and icon clicks
            let editButton = null;
            if (e.target.hasAttribute('data-action') && e.target.getAttribute('data-action') === 'edit') {
                editButton = e.target;
            } else if (e.target.closest('[data-action="edit"]')) {
                editButton = e.target.closest('[data-action="edit"]');
            }
            
            if (editButton) {
                const categoryId = editButton.getAttribute('data-category-id');
                const categoryName = editButton.getAttribute('data-category-name');
                const categoryType = editButton.getAttribute('data-category-type');
                const categoryEmoji = editButton.getAttribute('data-category-emoji');
                
                this.populateEditForm(categoryId, categoryName, categoryType, categoryEmoji);
            }
        });
    }

    /**
     * Populate edit form with category data
     */
    populateEditForm(categoryId, categoryName, categoryType, categoryEmoji) {
        const elements = this.getElements();
        
        // Clear any previous errors first
        this.clearFieldErrors(elements.editCategoryForm);
        
        // Populate edit form
        document.getElementById('editCategoryId').value = categoryId;
        document.getElementById('editCategoryName').value = categoryName;
        document.getElementById('editCategoryType').value = categoryType;
        document.getElementById('editCategoryEmoji').value = categoryEmoji;
        
        this.currentCategoryId = categoryId;
    }

    /**
     * Handle add category form submission
     */
    async handleAddCategory() {
        const elements = this.getElements();
        
        // Prevent multiple submissions
        if (elements.saveAddCategoryBtn.disabled) {
            return;
        }
        
        this.clearFieldErrors(elements.addCategoryForm);
        
        const formData = new FormData(elements.addCategoryForm);
        
        const data = {
            name: formData.get('name').trim(),
            type: formData.get('type'),
            unicode_emoji: formData.get('unicode_emoji').trim() || (formData.get('type') === 'income' ? '💰' : '💸')
        };
        
        // Basic validation
        if (!data.name) {
            this.showFieldError('addCategoryName', 'Category name is required');
            return;
        }
        
        if (!data.type) {
            this.showFieldError('addCategoryType', 'Category type is required');
            return;
        }
        
        this.showSpinner(elements.saveAddCategoryBtn);
        
        try {
            const response = await fetch('/categories/api/categories', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert(result.message, 'success');
                bootstrap.Modal.getInstance(elements.addCategoryModal).hide();
                
                // Reload page after short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showAlert(result.error, 'danger');
            }
        } catch (error) {
            console.error('Error creating category:', error);
            this.showAlert('Error creating category. Please try again.', 'danger');
        } finally {
            this.hideSpinner(elements.saveAddCategoryBtn);
        }
    }

    /**
     * Handle edit category form submission
     */
    async handleEditCategory() {
        const elements = this.getElements();
        
        // Prevent multiple submissions
        if (elements.saveEditCategoryBtn.disabled) {
            return;
        }
        
        this.clearFieldErrors(elements.editCategoryForm);
        
        const formData = new FormData(elements.editCategoryForm);
        const data = {
            name: formData.get('name').trim(),
            type: formData.get('type'),
            unicode_emoji: formData.get('unicode_emoji').trim() || (formData.get('type') === 'income' ? '💰' : '💸')
        };
        
        // Basic validation
        if (!data.name) {
            this.showFieldError('editCategoryName', 'Category name is required');
            return;
        }
        
        this.showSpinner(elements.saveEditCategoryBtn);
        
        try {
            const response = await fetch(`/categories/api/categories/${this.currentCategoryId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert(result.message, 'success');
                bootstrap.Modal.getInstance(elements.editCategoryModal).hide();
                
                // Reload page after short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showAlert(result.error, 'danger');
            }
        } catch (error) {
            console.error('Error updating category:', error);
            this.showAlert('Error updating category. Please try again.', 'danger');
        } finally {
            this.hideSpinner(elements.saveEditCategoryBtn);
        }
    }

    /**
     * Handle delete category request
     */
    handleDeleteCategoryRequest() {
        const elements = this.getElements();
        const categoryName = document.getElementById('editCategoryName').value;
        document.getElementById('deleteCategoryName').textContent = categoryName;
        
        // Store the current category ID in the confirm delete button
        elements.confirmDeleteCategoryBtn.setAttribute('data-category-id', this.currentCategoryId);
        
        bootstrap.Modal.getInstance(elements.editCategoryModal).hide();
        new bootstrap.Modal(elements.deleteCategoryModal).show();
    }

    /**
     * Handle confirm delete category
     */
    async handleConfirmDeleteCategory() {
        const elements = this.getElements();
        
        // Prevent multiple submissions
        if (elements.confirmDeleteCategoryBtn.disabled) {
            return;
        }
        
        // Get the category ID from the button's data attribute
        const categoryIdToDelete = elements.confirmDeleteCategoryBtn.getAttribute('data-category-id');
        
        if (!categoryIdToDelete) {
            this.showAlert('Category ID not found. Please try again.', 'danger');
            return;
        }
        
        this.showSpinner(elements.confirmDeleteCategoryBtn);
        
        try {
            const response = await fetch(`/categories/api/categories/${categoryIdToDelete}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.csrfToken
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert(result.message, 'success');
                bootstrap.Modal.getInstance(elements.deleteCategoryModal).hide();
                
                // Reload page after short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                this.showAlert(result.error, 'danger');
                bootstrap.Modal.getInstance(elements.deleteCategoryModal).hide();
            }
        } catch (error) {
            console.error('Error deleting category:', error);
            this.showAlert('Error deleting category. Please try again.', 'danger');
            bootstrap.Modal.getInstance(elements.deleteCategoryModal).hide();
        } finally {
            this.hideSpinner(elements.confirmDeleteCategoryBtn);
        }
    }

    /**
     * Initialize Top Expenses Chart
     */
    initializeTopExpensesChart() {
        // Get current filter from URL or default to month
        const urlParams = new URLSearchParams(window.location.search);
        const currentFilter = urlParams.get('filter') || 'month';
        const startDate = urlParams.get('start_date');
        const endDate = urlParams.get('end_date');
        
        this.loadTopExpensesChart(currentFilter, startDate, endDate);
    }

    /**
     * Load top expenses chart with specified filter
     * @param {string} filter - Time filter to apply
     * @param {string} startDate - Start date for custom range
     * @param {string} endDate - End date for custom range
     */
    loadTopExpensesChart(filter = 'month', startDate = null, endDate = null) {
        const canvas = document.getElementById('top-expenses-chart');
        const loadingDiv = document.getElementById('chart-loading');
        const emptyDiv = document.getElementById('chart-empty');
        const chartSubtitle = document.getElementById('chart-subtitle');
        
        if (!canvas) return;
        
        // Show loading state
        if (loadingDiv) loadingDiv.style.display = 'block';
        if (emptyDiv) emptyDiv.classList.add('d-none');
        canvas.style.display = 'none';
        
        // Build API URL with filter parameters - show all categories for pie chart
        let apiUrl = '/categories/api/categories/top-expenses?filter=' + filter + '&show_all=true';
        if (filter === 'custom' && startDate && endDate) {
            apiUrl += `&start_date=${startDate}&end_date=${endDate}`;
        }
        
        // Update chart subtitle based on filter
        if (chartSubtitle) {
            const filterNames = {
                'today': 'Today',
                'week': 'This Week',
                'month': 'Current Month',
                'quarter': 'This Quarter',
                'year': 'This Year',
                'custom': startDate && endDate ? `${startDate} to ${endDate}` : 'Custom Range',
                'all': 'All Time'
            };
            chartSubtitle.textContent = filterNames[filter] || 'Current Month';
        }
        
        // Fetch top expense categories data
        fetch(apiUrl)
            .then(response => response.json())
            .then(data => {
                if (loadingDiv) loadingDiv.style.display = 'none';
                
                if (data.success && data.has_data) {
                    // Transform data to match home.js format
                    const transformedData = {
                        status: 'success',
                        data: {
                            categories: data.chart_data.labels.map((label, index) => ({
                                name: label,
                                amount: data.chart_data.data[index],
                                percentage: ((data.chart_data.data[index] / data.chart_data.data.reduce((a, b) => a + b, 0)) * 100).toFixed(1),
                                formatted_amount: `$${data.chart_data.data[index].toFixed(2)}`,
                                emoji: data.chart_data.emojis[index] || '💸'
                            }))
                        }
                    };
                    
                    this.renderTopExpensesChart(canvas, transformedData);
                    canvas.style.display = 'block';
                } else {
                    if (emptyDiv) emptyDiv.classList.remove('d-none');
                }
            })
            .catch(error => {
                console.error('Error loading chart data:', error);
                if (loadingDiv) loadingDiv.style.display = 'none';
                if (emptyDiv) emptyDiv.classList.remove('d-none');
            });
    }

    /**
     * Render the top expenses chart as doughnut chart (same as home.js)
     */
    renderTopExpensesChart(canvas, data) {
        if (data.status !== 'success' || !data.data.categories.length) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart if it exists
        if (this.topExpensesChart) {
            this.topExpensesChart.destroy();
        }
        
        // Use same colors as home.js (extended to handle more categories)
        const chartColors = [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF',
            // Additional colors for more categories
            '#FF9999', '#87CEEB', '#FFE135', '#5BC0C0',
            '#AA77FF', '#FFA040', '#FF7777', '#D9DDDF'
        ];
        
        this.topExpensesChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.data.categories.map(cat => cat.name),
                datasets: [{
                    data: data.data.categories.map(cat => cat.amount),
                    backgroundColor: chartColors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const category = data.data.categories[context.dataIndex];
                                return `${category.name}: ${category.formatted_amount} (${category.percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Update the category list below the chart (same as home.js)
        this.updateExpenseCategoryList(data.data.categories, chartColors);
    }
    
    /**
     * Update expense category list with percentages (shows ALL categories, not limited)
     * @param {Array} categories - Category data array
     * @param {Array} chartColors - Chart colors array
     */
    updateExpenseCategoryList(categories, chartColors) {
        const listContainer = document.getElementById('expense-category-list');
        if (!listContainer) return;
        
        // Show ALL categories (no limit like home.js)
        const listHTML = categories.map((category, index) => `
            <div class="d-flex justify-content-between align-items-center py-1 border-bottom">
                <div class="d-flex align-items-center">
                    <div class="me-2" style="width: 12px; height: 12px; background-color: ${chartColors[index % chartColors.length]}; border-radius: 50%;"></div>
                    <span class="small">${this.escapeHtml(category.name)}</span>
                </div>
                <div class="text-end">
                    <div class="fw-bold small">${category.formatted_amount}</div>
                    <div class="text-muted" style="font-size: 0.75rem;">${category.percentage}%</div>
                </div>
            </div>
        `).join('');
        
        listContainer.innerHTML = listHTML;
    }
    
    /**
     * Escape HTML to prevent XSS (same as home.js)
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show custom date range modal
     */
    showCustomDateRangeModal() {
        const modal = document.getElementById('customDateRangeModal');
        if (modal) {
            const modalInstance = new bootstrap.Modal(modal);
            modalInstance.show();
        }
    }

    /**
     * Apply custom date range filter
     */
    applyCustomDateRange() {
        const startDate = document.getElementById('customStartDate').value;
        const endDate = document.getElementById('customEndDate').value;
        
        if (!startDate || !endDate) {
            this.showAlert('Please select both start and end dates.', 'warning');
            return;
        }
        
        if (new Date(startDate) > new Date(endDate)) {
            this.showAlert('Start date cannot be after end date.', 'warning');
            return;
        }
        
        // Update the filter button text
        const currentFilterElement = document.getElementById('currentFilter');
        if (currentFilterElement) {
            currentFilterElement.textContent = `Custom Range (${startDate} to ${endDate})`;
        }
        
        // Update chart immediately before page reload
        this.loadTopExpensesChart('custom', startDate, endDate);
        
        // Apply the filter
        const url = new URL(window.location);
        url.searchParams.set('filter', 'custom');
        url.searchParams.set('start_date', startDate);
        url.searchParams.set('end_date', endDate);
        
        // Close modal and redirect
        const modal = document.getElementById('customDateRangeModal');
        if (modal) {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        }
        
        window.location.href = url.toString();
    }

    /**
     * Utility functions
     */
    showSpinner(button) {
        const spinner = button.querySelector('.spinner-border');
        if (spinner) spinner.classList.remove('d-none');
        button.disabled = true;
    }
    
    hideSpinner(button) {
        const spinner = button.querySelector('.spinner-border');
        if (spinner) spinner.classList.add('d-none');
        button.disabled = false;
    }
    
    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (!field) return;
        
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        field.classList.add('is-invalid');
        if (feedback) feedback.textContent = message;
    }
    
    clearFieldErrors(form) {
        if (!form) return;
        
        const fields = form.querySelectorAll('.form-control, .form-select');
        fields.forEach(field => {
            field.classList.remove('is-invalid');
            const feedback = field.parentNode.querySelector('.invalid-feedback');
            if (feedback) feedback.textContent = '';
        });
    }

    /**
     * Show alert message with consistent styling
     */
    showAlert(message, type) {
        // Create alert element with the same styling as base.html
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show shadow-sm`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.style.minWidth = '300px';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Find or create the flash message container like base.html
        let flashContainer = document.querySelector('.position-fixed.top-0.start-50.translate-middle-x');
        if (!flashContainer) {
            // Create the container with the same style as base.html
            flashContainer = document.createElement('div');
            flashContainer.className = 'position-fixed top-0 start-50 translate-middle-x';
            flashContainer.style.zIndex = '1055';
            flashContainer.style.marginTop = '20px';
            document.body.appendChild(flashContainer);
        }
        
        // Insert alert into the flash container
        flashContainer.appendChild(alertDiv);
        
        // Auto-dismiss after 2.5 seconds (same as base.js)
        setTimeout(() => {
            if (alertDiv && alertDiv.classList.contains('show')) {
                alertDiv.classList.remove('show');
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.parentNode.removeChild(alertDiv);
                    }
                }, 150);
            }
        }, 2500);
    }
}

// Initialize category manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new CategoryManager();
});

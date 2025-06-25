/**
 * Home Dashboard JavaScript
 * Handles dashboard interactions, statistics updates, and dynamic content loading
 */

// Configuration constants
const DASHBOARD_CONFIG = {
    refreshInterval: 60000, // 1 minute
    chartColors: [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
        '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
    ],
    maxCategoryDisplay: 5,
    apiEndpoints: {
        stats: '/home/api/stats',
        categoryBreakdown: '/home/api/category-breakdown',
        weeklyExpenses: '/home/api/weekly-expenses'
    },
    navigation: {
        transactions: '/transactions',
        categories: '/categories',
        account: '/account'
    }
};

// Dashboard state management
const dashboardState = {
    charts: {},
    refreshTimer: null,
    isInitialized: false
};

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

// Clean up resources when leaving the page
window.addEventListener('beforeunload', function() {
    cleanupDashboard();
});

/**
 * Initialize the dashboard
 */
function initializeDashboard() {
    if (dashboardState.isInitialized) {
        console.warn('Dashboard already initialized');
        return;
    }
    
    initializeQuickActions();
    initializeCharts();
    loadPeriodStatistics();
    setupAutoRefresh();
    
    dashboardState.isInitialized = true;
}

/**
 * Initialize quick action buttons
 */
function initializeQuickActions() {
    const actionButtons = {
        'add-transaction': () => navigateToPage(`${DASHBOARD_CONFIG.navigation.transactions}?openModal=addTransaction`),
        'manage-categories': () => navigateToPage(DASHBOARD_CONFIG.navigation.categories),
        'generate-report': () => generateMonthlyReport(),
        'add-account': (btn) => {
            const autoModal = btn.dataset.autoModal === 'true';
            const url = autoModal ? 
                `${DASHBOARD_CONFIG.navigation.account}?openModal=addAccount` : 
                DASHBOARD_CONFIG.navigation.account;
            navigateToPage(url);
        }
    };

    Object.entries(actionButtons).forEach(([action, handler]) => {
        const buttons = document.querySelectorAll(`[data-action="${action}"]`);
        buttons.forEach(btn => {
            btn.addEventListener('click', () => handler(btn));
        });
    });
}

/**
 * Navigate to a specific page
 * @param {string} url - The URL to navigate to
 */
function navigateToPage(url) {
    window.location.href = url;
}

/**
 * Update statistics display with new data
 * @param {Object} stats - Statistics data from API
 */
function updateStatisticsDisplay(stats) {
    const updates = [
        { 
            selector: '[data-stat="total-balance"]', 
            value: stats.total_balance,
            formatter: formatCurrency
        },
        { 
            selector: '[data-stat="monthly-net"]', 
            value: stats.period_net,
            formatter: formatCurrency
        }
    ];

    updates.forEach(({ selector, value, formatter }) => {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = formatter(value);
            element.className = value >= 0 ? 'text-success' : 'text-danger';
        }
    });
}

/**
 * Refresh statistics from server
 * @param {number} days - Number of days for period statistics
 */
async function refreshStatistics(days = 30) {
    try {
        const response = await fetch(`${DASHBOARD_CONFIG.apiEndpoints.stats}?days=${days}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            updateStatisticsDisplay(data.data);
        } else {
            console.error('Failed to refresh statistics:', data.message);
        }
    } catch (error) {
        console.error('Error refreshing statistics:', error);
    }
}

/**
 * Load period statistics (weekly and daily)
 */
function loadPeriodStatistics() {
    loadWeeklyStats();
    loadDailyStats();
}

/**
 * Setup automatic refresh for statistics
 */
function setupAutoRefresh() {
    if (dashboardState.refreshTimer) {
        clearInterval(dashboardState.refreshTimer);
    }
    
    dashboardState.refreshTimer = setInterval(refreshAllStats, DASHBOARD_CONFIG.refreshInterval);
}

/**
 * Initialize charts if Chart.js is available
 */
function initializeCharts() {
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded, skipping chart initialization');
        return;
    }
    
    initializeCategoryChart();
    initializeWeeklyExpensesChart();
}

/**
 * Initialize category breakdown chart
 */
async function initializeCategoryChart() {
    const chartContainer = document.getElementById('category-chart');
    if (!chartContainer) return;
    
    try {
        const response = await fetch(`${DASHBOARD_CONFIG.apiEndpoints.categoryBreakdown}?days=30`);
        const data = await response.json();
        
        if (data.status === 'success' && data.data.categories.length > 0) {
            const ctx = chartContainer.getContext('2d');
            
            // Destroy existing chart if it exists
            if (dashboardState.charts.category) {
                dashboardState.charts.category.destroy();
            }
            
            dashboardState.charts.category = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.data.categories.map(cat => cat.name),
                    datasets: [{
                        data: data.data.categories.map(cat => cat.amount),
                        backgroundColor: DASHBOARD_CONFIG.chartColors,
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
            
            updateCategoryList(data.data.categories);
        }
    } catch (error) {
        console.error('Error initializing category chart:', error);
    }
}

/**
 * Update category list with percentages
 * @param {Array} categories - Category data array
 */
function updateCategoryList(categories) {
    const listContainer = document.getElementById('category-list');
    if (!listContainer) return;
    
    const displayCategories = categories.slice(0, DASHBOARD_CONFIG.maxCategoryDisplay);
    
    const listHTML = displayCategories.map((category, index) => `
        <div class="d-flex justify-content-between align-items-center py-1 border-bottom">
            <div class="d-flex align-items-center">
                <div class="me-2" style="width: 12px; height: 12px; background-color: ${DASHBOARD_CONFIG.chartColors[index]}; border-radius: 50%;"></div>
                <span class="small">${escapeHtml(category.name)}</span>
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
 * Initialize weekly expenses chart
 */
async function initializeWeeklyExpensesChart() {
    const chartContainer = document.getElementById('weekly-expenses-chart');
    if (!chartContainer) return;
    
    try {
        const response = await fetch(DASHBOARD_CONFIG.apiEndpoints.weeklyExpenses);
        const data = await response.json();
        
        if (data.status === 'success') {
            const ctx = chartContainer.getContext('2d');
            
            // Destroy existing chart if it exists
            if (dashboardState.charts.weeklyExpenses) {
                dashboardState.charts.weeklyExpenses.destroy();
            }
            
            dashboardState.charts.weeklyExpenses = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.data.map(day => day.day_name),
                    datasets: [{
                        label: 'Expenses',
                        data: data.data.map(day => day.expenses),
                        backgroundColor: 'rgba(220, 53, 69, 0.8)',
                        borderColor: '#dc3545',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value);
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Expenses: ${formatCurrency(context.parsed.y)}`;
                                }
                            }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error initializing weekly expenses chart:', error);
    }
}

/**
 * Load statistics for a specific period
 * @param {number} days - Number of days
 * @param {string} elementId - Element ID to update
 * @param {string} breakdownId - Breakdown element ID
 */
async function loadPeriodStats(days, elementId, breakdownId) {
    try {
        const response = await fetch(`${DASHBOARD_CONFIG.apiEndpoints.stats}?days=${days}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            const { period_net, period_income, period_expenses } = data.data;
            
            updateElementText(elementId, formatCurrency(period_net));
            updateElementClass(elementId, period_net >= 0 ? 'text-success' : 'text-danger');
            
            if (breakdownId) {
                updateElementHTML(breakdownId, `
                    <span class="text-success">+${formatCurrency(period_income)}</span> | 
                    <span class="text-danger">-${formatCurrency(period_expenses)}</span>
                `);
            }
        }
    } catch (error) {
        console.error(`Error loading ${days}-day stats:`, error);
        updateElementText(elementId, '$0.00');
    }
}

/**
 * Load weekly statistics
 */
function loadWeeklyStats() {
    loadPeriodStats(7, 'weekly-balance', 'weekly-breakdown');
}

/**
 * Load daily statistics  
 */
function loadDailyStats() {
    loadPeriodStats(1, 'daily-balance', 'daily-breakdown');
}

/**
 * Refresh all statistics
 */
async function refreshAllStats() {
    await Promise.all([
        refreshStatistics(),
        loadWeeklyStats(),
        loadDailyStats()
    ]);
}

/**
 * Generate monthly report
 */
async function generateMonthlyReport() {
    try {
        showLoadingSpinner();
        
        const currentDate = new Date();
        const month = currentDate.getMonth() + 1;
        const year = currentDate.getFullYear();
        
        const response = await fetch(`${DASHBOARD_CONFIG.apiEndpoints.stats}?days=30`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            const reportContent = generateReportHTML(data.data, month, year);
            
            const reportWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes,resizable=yes');
            if (reportWindow) {
                reportWindow.document.write(reportContent);
                reportWindow.document.close();
                reportWindow.focus();
                showNotification('Monthly report generated successfully', 'success');
            } else {
                throw new Error('Popup window was blocked');
            }
        } else {
            throw new Error(data.message || 'Failed to generate report');
        }
    } catch (error) {
        console.error('Error generating report:', error);
        showNotification(`Failed to generate monthly report: ${error.message}`, 'error');
    } finally {
        hideLoadingSpinner();
    }
}

/**
 * Generate HTML content for monthly report
 * @param {Object} data - Report data
 * @param {number} month - Month number
 * @param {number} year - Year
 * @returns {string} HTML content
 */
function generateReportHTML(data, month, year) {
    const monthName = new Date(year, month - 1).toLocaleString('default', { month: 'long' });
    
    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Monthly Report - ${monthName} ${year}</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; 
                    margin: 20px; 
                    line-height: 1.6;
                    color: #333;
                }
                .header { 
                    text-align: center; 
                    border-bottom: 2px solid #333; 
                    padding-bottom: 20px; 
                    margin-bottom: 30px;
                }
                .section { margin: 30px 0; }
                .stat-grid { 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                    gap: 20px; 
                }
                .stat-card { 
                    border: 1px solid #ddd; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .positive { color: #28a745; font-weight: bold; }
                .negative { color: #dc3545; font-weight: bold; }
                .net { color: #007bff; font-weight: bold; }
                h1, h2 { margin: 0; }
                h3 { color: #666; }
                h4 { margin-bottom: 10px; color: #333; }
                @media print { 
                    body { margin: 0; }
                    .stat-card { break-inside: avoid; }
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Monthly Financial Report</h1>
                <h2>${monthName} ${year}</h2>
                <p>Generated on ${new Date().toLocaleDateString()}</p>
            </div>
            
            <div class="section">
                <h3>Financial Summary</h3>
                <div class="stat-grid">
                    <div class="stat-card">
                        <h4>Total Balance</h4>
                        <p class="${data.total_balance >= 0 ? 'positive' : 'negative'}">${formatCurrency(data.total_balance)}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Monthly Income</h4>
                        <p class="positive">${formatCurrency(data.period_income)}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Monthly Expenses</h4>
                        <p class="negative">${formatCurrency(data.period_expenses)}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Net Income</h4>
                        <p class="${data.period_net >= 0 ? 'net' : 'negative'}">${formatCurrency(data.period_net)}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
    `;
}

/**
 * Utility Functions
 */

/**
 * Update element text content
 * @param {string} elementId - Element ID
 * @param {string} text - Text to set
 */
function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) element.textContent = text;
}

/**
 * Update element class
 * @param {string} elementId - Element ID  
 * @param {string} className - Class name to set
 */
function updateElementClass(elementId, className) {
    const element = document.getElementById(elementId);
    if (element) element.className = className;
}

/**
 * Update element HTML content
 * @param {string} elementId - Element ID
 * @param {string} html - HTML to set
 */
function updateElementHTML(elementId, html) {
    const element = document.getElementById(elementId);
    if (element) element.innerHTML = html;
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show loading spinner
 */
function showLoadingSpinner() {
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) spinner.style.display = 'block';
}

/**
 * Hide loading spinner
 */
function hideLoadingSpinner() {
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) spinner.style.display = 'none';
}

/**
 * Show notification message
 * @param {string} message - Message to show
 * @param {string} type - Type of notification (info, success, error)
 */
function showNotification(message, type = 'info') {
    // Basic implementation - can be enhanced with actual notification system
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // If a more sophisticated notification system exists, integrate here
    if (typeof window.showAlert === 'function') {
        window.showAlert(message, type);
    }
}

/**
 * Clean up dashboard resources
 */
function cleanupDashboard() {
    // Clear refresh timer
    if (dashboardState.refreshTimer) {
        clearInterval(dashboardState.refreshTimer);
        dashboardState.refreshTimer = null;
    }
    
    // Destroy charts to prevent memory leaks
    Object.values(dashboardState.charts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            chart.destroy();
        }
    });
    dashboardState.charts = {};
    
    dashboardState.isInitialized = false;
}

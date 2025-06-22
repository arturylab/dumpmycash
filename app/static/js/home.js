/**
 * Home Dashboard JavaScript
 * Handles dashboard interactions, statistics updates, and dynamic content loading
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

/**
 * Initialize the dashboard
 */
function initializeDashboard() {
    // Initialize quick action buttons
    initializeQuickActions();
    
    // Initialize charts if available
    initializeCharts();
    
    // Set up auto-refresh for recent transactions and statistics
    setInterval(refreshRecentTransactions, 30000); // Refresh every 30 seconds
    setInterval(refreshStatistics, 60000); // Refresh statistics every minute
}

/**
 * Initialize quick action buttons
 */
function initializeQuickActions() {
    // Add Transaction buttons
    const addTransactionBtns = document.querySelectorAll('[data-action="add-transaction"]');
    addTransactionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            window.location.href = '/transactions/new';
        });
    });
    
    // View All Transactions button
    const viewTransactionsBtns = document.querySelectorAll('[data-action="view-transactions"]');
    viewTransactionsBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            window.location.href = '/transactions';
        });
    });
    
    // Manage Categories button
    const manageCategoriesBtns = document.querySelectorAll('[data-action="manage-categories"]');
    manageCategoriesBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            window.location.href = '/categories';
        });
    });
    
    // Generate Report button
    const generateReportBtns = document.querySelectorAll('[data-action="generate-report"]');
    generateReportBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            generateMonthlyReport();
        });
    });
    
    // Add Account button
    const addAccountBtns = document.querySelectorAll('[data-action="add-account"]');
    addAccountBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const autoModal = btn.dataset.autoModal === 'true';
            if (autoModal) {
                // Navigate to account page with parameter to auto-open the modal
                window.location.href = '/account?openModal=addAccount';
            } else {
                window.location.href = '/account';
            }
        });
    });
}

/**
 * Update statistics display with new data
 */
function updateStatisticsDisplay(stats) {
    // Update total balance
    const balanceElement = document.querySelector('[data-stat="total-balance"]');
    if (balanceElement) {
        balanceElement.textContent = formatCurrency(stats.total_balance);
        balanceElement.className = stats.total_balance >= 0 ? 'text-success' : 'text-danger';
    }
    
    // Update monthly income/expenses
    const monthlyElement = document.querySelector('[data-stat="monthly-net"]');
    if (monthlyElement) {
        monthlyElement.textContent = formatCurrency(stats.period_net);
        monthlyElement.className = stats.period_net >= 0 ? 'text-success' : 'text-danger';
    }
}

/**
 * Refresh statistics from server
 */
async function refreshStatistics() {
    try {
        const response = await fetch('/home/api/stats?days=30');
        const data = await response.json();
        
        if (data.status === 'success') {
            updateStatisticsDisplay(data.data);
        }
    } catch (error) {
        console.error('Error refreshing statistics:', error);
    }
}

/**
 * Refresh recent transactions
 */
async function refreshRecentTransactions() {
    try {
        const response = await fetch('/home/api/recent-transactions?limit=10');
        const data = await response.json();
        
        if (data.status === 'success') {
            updateRecentTransactionsList(data.data);
        }
    } catch (error) {
        console.error('Error refreshing recent transactions:', error);
    }
}

/**
 * Update recent transactions list
 */
function updateRecentTransactionsList(transactions) {
    const container = document.querySelector('#recent-transactions-list');
    if (!container) return;
    
    if (transactions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-receipt fa-3x text-muted mb-3"></i>
                <p class="text-muted">No transactions yet. Start by adding your first transaction!</p>
                <button type="button" class="btn btn-primary" data-action="add-transaction">Add First Transaction</button>
            </div>
        `;
        // Re-initialize quick actions for the new button
        initializeQuickActions();
        return;
    }
    
    const transactionItems = transactions.map(transaction => `
        <div class="transaction-item d-flex justify-content-between align-items-center py-2 border-bottom">
            <div class="transaction-info">
                <div class="fw-semibold">${escapeHtml(transaction.description)}</div>
                <small class="text-muted">${transaction.category} • ${transaction.formatted_date}</small>
            </div>
            <div class="transaction-amount">
                <span class="fw-bold ${transaction.transaction_type === 'income' ? 'text-success' : 'text-danger'}">
                    ${transaction.transaction_type === 'income' ? '+' : '-'}${transaction.formatted_amount}
                </span>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = transactionItems;
}

/**
 * Initialize charts if Chart.js is available
 */
function initializeCharts() {
    if (typeof Chart === 'undefined') return;
    
    // Initialize category breakdown chart
    initializeCategoryChart();
    
    // Initialize monthly trend chart
    initializeMonthlyTrendChart();
}

/**
 * Initialize category breakdown chart
 */
async function initializeCategoryChart() {
    const chartContainer = document.getElementById('category-chart');
    if (!chartContainer) return;
    
    try {
        const response = await fetch('/home/api/category-breakdown?days=30');
        const data = await response.json();
        
        if (data.status === 'success' && data.data.categories.length > 0) {
            const ctx = chartContainer.getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.data.categories.map(cat => cat.name),
                    datasets: [{
                        data: data.data.categories.map(cat => cat.amount),
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
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
        }
    } catch (error) {
        console.error('Error initializing category chart:', error);
    }
}

/**
 * Initialize monthly trend chart
 */
async function initializeMonthlyTrendChart() {
    const chartContainer = document.getElementById('monthly-trend-chart');
    if (!chartContainer) return;
    
    try {
        const response = await fetch('/home/api/monthly-trend');
        const data = await response.json();
        
        if (data.status === 'success') {
            const ctx = chartContainer.getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.data.map(month => `${month.month.substring(0, 3)} ${month.year}`),
                    datasets: [{
                        label: 'Income',
                        data: data.data.map(month => month.income),
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Expenses',
                        data: data.data.map(month => month.expenses),
                        borderColor: '#dc3545',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Net',
                        data: data.data.map(month => month.net),
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
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
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
                                }
                            }
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error initializing monthly trend chart:', error);
    }
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
        
        // Fetch monthly data
        const response = await fetch(`/home/api/stats?days=30`);
        const data = await response.json();
        
        if (data.status === 'success') {
            const reportData = data.data;
            const reportContent = generateReportHTML(reportData, month, year);
            
            // Open report in new window
            const reportWindow = window.open('', '_blank');
            reportWindow.document.write(reportContent);
            reportWindow.document.close();
            
            showNotification('Monthly report generated successfully', 'success');
        } else {
            throw new Error(data.message || 'Failed to generate report');
        }
    } catch (error) {
        console.error('Error generating report:', error);
        showNotification('Failed to generate monthly report', 'error');
    } finally {
        hideLoadingSpinner();
    }
}

/**
 * Generate HTML content for monthly report
 */
function generateReportHTML(data, month, year) {
    const monthName = new Date(year, month - 1).toLocaleString('default', { month: 'long' });
    
    return `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Monthly Report - ${monthName} ${year}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
                .section { margin: 20px 0; }
                .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
                .stat-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
                .positive { color: #28a745; }
                .negative { color: #dc3545; }
                .net { color: #007bff; }
                @media print { body { margin: 0; } }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Monthly Financial Report</h1>
                <h2>${monthName} ${year}</h2>
                <p>Generated on ${new Date().toLocaleDateString()}</p>
            </div>
            
            <div class="section">
                <h3>Summary</h3>
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

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showLoadingSpinner() {
    // Implementation depends on your loading spinner setup
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) spinner.style.display = 'block';
}

function hideLoadingSpinner() {
    const spinner = document.querySelector('.loading-spinner');
    if (spinner) spinner.style.display = 'none';
}

function showNotification(message, type = 'info') {
    // Implementation depends on your notification system
    console.log(`${type.toUpperCase()}: ${message}`);
}

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
    
    // Load period statistics
    loadWeeklyStats();
    loadDailyStats();
    
    // Set up auto-refresh for statistics
    setInterval(refreshAllStats, 60000); // Refresh every minute
}

/**
 * Initialize quick action buttons
 */
function initializeQuickActions() {
    // Add Transaction buttons
    const addTransactionBtns = document.querySelectorAll('[data-action="add-transaction"]');
    addTransactionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Navigate to transactions page where the modal can be opened
            window.location.href = '/transactions?openModal=addTransaction';
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
 * Initialize charts if Chart.js is available
 */
function initializeCharts() {
    if (typeof Chart === 'undefined') return;
    
    // Initialize category breakdown chart
    initializeCategoryChart();
    
    // Initialize weekly expenses chart
    initializeWeeklyExpensesChart();
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
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
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
            
            // Update category list with percentages
            updateCategoryList(data.data.categories);
        }
    } catch (error) {
        console.error('Error initializing category chart:', error);
    }
}

/**
 * Update category list with percentages
 */
function updateCategoryList(categories) {
    const listContainer = document.getElementById('category-list');
    if (!listContainer) return;
    
    const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];
    
    const listHTML = categories.slice(0, 5).map((category, index) => `
        <div class="d-flex justify-content-between align-items-center py-1 border-bottom">
            <div class="d-flex align-items-center">
                <div class="me-2" style="width: 12px; height: 12px; background-color: ${colors[index]}; border-radius: 50%;"></div>
                <span class="small">${category.name}</span>
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
        const response = await fetch('/home/api/weekly-expenses');
        const data = await response.json();
        
        if (data.status === 'success') {
            const ctx = chartContainer.getContext('2d');
            new Chart(ctx, {
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
                        legend: {
                            display: false
                        },
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
 * Load weekly statistics
 */
async function loadWeeklyStats() {
    try {
        const response = await fetch('/home/api/stats?days=7');
        const data = await response.json();
        
        if (data.status === 'success') {
            const weeklyNet = data.data.period_net;
            const weeklyIncome = data.data.period_income;
            const weeklyExpenses = data.data.period_expenses;
            
            document.getElementById('weekly-balance').textContent = formatCurrency(weeklyNet);
            document.getElementById('weekly-breakdown').innerHTML = `
                <span class="text-success">+${formatCurrency(weeklyIncome)}</span> | 
                <span class="text-danger">-${formatCurrency(weeklyExpenses)}</span>
            `;
            
            // Update color based on net value
            const weeklyElement = document.getElementById('weekly-balance');
            weeklyElement.className = weeklyNet >= 0 ? 'text-success' : 'text-danger';
        }
    } catch (error) {
        console.error('Error loading weekly stats:', error);
        document.getElementById('weekly-balance').textContent = '$0.00';
    }
}

/**
 * Load daily statistics
 */
async function loadDailyStats() {
    try {
        const response = await fetch('/home/api/stats?days=1');
        const data = await response.json();
        
        if (data.status === 'success') {
            const dailyNet = data.data.period_net;
            const dailyIncome = data.data.period_income;
            const dailyExpenses = data.data.period_expenses;
            
            document.getElementById('daily-balance').textContent = formatCurrency(dailyNet);
            document.getElementById('daily-breakdown').innerHTML = `
                <span class="text-success">+${formatCurrency(dailyIncome)}</span> | 
                <span class="text-danger">-${formatCurrency(dailyExpenses)}</span>
            `;
            
            // Update color based on net value
            const dailyElement = document.getElementById('daily-balance');
            dailyElement.className = dailyNet >= 0 ? 'text-success' : 'text-danger';
        }
    } catch (error) {
        console.error('Error loading daily stats:', error);
        document.getElementById('daily-balance').textContent = '$0.00';
    }
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

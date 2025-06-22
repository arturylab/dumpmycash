/**
 * Base JavaScript functionality for DumpMyMoney application
 * This file contains common JavaScript functions used across the application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert && alert.classList.contains('show')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 2500);
    });

    // Enhanced active navigation link highlighting
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(function(link) {
        // Add hover effects and smooth transitions
        link.addEventListener('mouseenter', function() {
            if (!this.classList.contains('active')) {
                this.style.transition = 'color 0.3s ease';
                this.style.color = '#ffc107'; // Bootstrap warning color for hover
            }
        });
        
        link.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                this.style.color = ''; // Reset to default
            }
        });
    });
});

// Additional base functionality can be added here
// For example: common form validation, AJAX helpers, etc.

/**
 * Format currency with commas and two decimal places
 * @param {number} amount - The amount to format
 * @returns {string} Formatted currency string (e.g., "$1,000.00")
 */
function formatCurrency(amount) {
    if (amount === null || amount === undefined) {
        return "$0.00";
    }
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

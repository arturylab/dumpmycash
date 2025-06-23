document.addEventListener('DOMContentLoaded', function() {
    // Apply account colors from data attributes
    const accountTitles = document.querySelectorAll('.account-title[data-account-color]');
    accountTitles.forEach(title => {
        const color = title.getAttribute('data-account-color');
        if (color && color !== '#000000' && color !== '') {
            // Apply custom color with high specificity
            title.classList.remove('text-muted');
            title.style.setProperty('color', color, 'important');
        } else {
            // Apply muted color if no custom color is set or if it's the default black
            title.classList.add('text-muted');
        }
    });
    
    // Check URL parameters to auto-open modals
    checkAndOpenModal();
    
    // Color dropdown event listeners for Add Account modal
    const colorOptions = document.querySelectorAll('.color-option');
    colorOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const color = this.getAttribute('data-color');
            const name = this.getAttribute('data-name');
            
            // Update hidden input
            document.getElementById('accountColor').value = color;
            
            // Update button display
            document.getElementById('selectedColorDot').style.backgroundColor = color;
            document.getElementById('selectedColorName').textContent = name;
        });
    });
    
    // Color dropdown event listeners for Edit Account modal  
    const editColorOptions = document.querySelectorAll('.edit-color-option');
    editColorOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            const color = this.getAttribute('data-color');
            const name = this.getAttribute('data-name');
            
            // Update hidden input
            document.getElementById('editAccountColor').value = color;
            
            // Update button display
            document.getElementById('editSelectedColorDot').style.backgroundColor = color;
            document.getElementById('editSelectedColorName').textContent = name;
        });
    });
    
    // Edit Account buttons
    document.querySelectorAll('.edit-account-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const id = this.getAttribute('data-id');
            const name = this.getAttribute('data-name');
            const balance = this.getAttribute('data-balance');
            const color = this.getAttribute('data-color') || '#555555';
            editAccount(id, name, balance, color);
        });
    });
    
    // Delete Account buttons
    document.querySelectorAll('.delete-account-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const id = this.getAttribute('data-id');
            const name = this.getAttribute('data-name');
            deleteAccount(id, name);
        });
    });
    
    // Quick Transfer button
    const quickTransferBtn = document.getElementById('quickTransferBtn');
    if (quickTransferBtn) {
        quickTransferBtn.addEventListener('click', function(e) {
            e.preventDefault();
            showTransferModal();
        });
    }
    
    // Load and display pie chart
    loadAccountChart();
    
    // Load recent transfers
    loadRecentTransfers();
    
    // Transfer form handler
    const transferForm = document.querySelector('#transferModal form');
    if (transferForm) {
        transferForm.addEventListener('submit', handleTransferSubmit);
    }
    
    // Reverse Transfer confirmation handler
    const confirmReverseBtn = document.getElementById('confirmReverseTransfer');
    if (confirmReverseBtn) {
        confirmReverseBtn.addEventListener('click', function() {
            const transferId = this.getAttribute('data-transfer-id');
            if (!transferId) return;
            
            // Show loading state
            const spinner = confirmReverseBtn.querySelector('.spinner-border');
            const originalHTML = confirmReverseBtn.innerHTML;
            confirmReverseBtn.disabled = true;
            spinner.classList.remove('d-none');
            
            // Get CSRF token from meta tag
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            
            if (!csrfToken) {
                showAlert('CSRF token not found. Please refresh the page and try again.', 'danger');
                confirmReverseBtn.disabled = false;
                spinner.classList.add('d-none');
                return;
            }
            
            // Create form data with CSRF token
            const formData = new FormData();
            formData.append('csrf_token', csrfToken);
            
            fetch(`/account/transfer/${transferId}/reverse`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showAlert(data.message, 'success');
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('reverseTransferModal'));
                    if (modal) {
                        modal.hide();
                    }
                    
                    // Refresh data
                    loadRecentTransfers();
                    loadAccountChart();
                    
                    // Reload page to update account balances
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showAlert(data.message || 'Error reversing transfer', 'danger');
                }
            })
            .catch(error => {
                console.error('Error reversing transfer:', error);
                showAlert('Error reversing transfer. Please try again.', 'danger');
            })
            .finally(() => {
                // Reset button state
                confirmReverseBtn.disabled = false;
                confirmReverseBtn.innerHTML = originalHTML;
            });
        });
    }
});

function editAccount(id, name, balance, color) {
    document.getElementById('editAccountName').value = name;
    document.getElementById('editAccountBalance').value = balance;
    document.getElementById('editAccountColor').value = color || '#555555';
    
    // Update dropdown display for edit modal
    document.getElementById('editSelectedColorDot').style.backgroundColor = color || '#555555';
    
    // Find the color name
    const colorNames = {
        '#555555': 'Light Black',
        '#36A2EB': 'Blue', 
        '#FFCE56': 'Yellow',
        '#4BC0C0': 'Teal',
        '#9966FF': 'Purple',
        '#FF9F40': 'Orange',
        '#FF6B6B': 'Red',
        '#4ECDC4': 'Mint',
        '#45B7D1': 'Sky Blue',
        '#96CEB4': 'Light Green'
    };
    
    document.getElementById('editSelectedColorName').textContent = colorNames[color] || 'Light Black';
    document.getElementById('editAccountForm').action = '/account/edit/' + id;
    
    var editModal = new bootstrap.Modal(document.getElementById('editAccountModal'));
    editModal.show();
}

function deleteAccount(id, name) {
    document.getElementById('deleteAccountName').textContent = name;
    document.getElementById('deleteAccountForm').action = '/account/delete/' + id;
    
    var deleteModal = new bootstrap.Modal(document.getElementById('deleteAccountModal'));
    deleteModal.show();
}

function showTransferModal() {
    // Populate account dropdowns
    fetch('/account/api/accounts')
        .then(response => response.json())
        .then(accounts => {
            const fromMenu = document.getElementById('fromAccountMenu');
            const toMenu = document.getElementById('toAccountMenu');
            
            // Clear existing options
            fromMenu.innerHTML = '';
            toMenu.innerHTML = '';
            
            // Add account options to both dropdown menus
            accounts.forEach(account => {
                // Create dropdown items for From Account
                const fromItem = document.createElement('li');
                fromItem.innerHTML = `
                    <a class="dropdown-item" href="#" data-account-id="${account.id}" data-account-name="${account.name}" data-account-balance="${account.balance}">
                        ${account.name} 
                        <small class="text-muted">(${formatCurrency(account.balance)})</small>
                    </a>
                `;
                
                // Create dropdown items for To Account
                const toItem = document.createElement('li');
                toItem.innerHTML = `
                    <a class="dropdown-item" href="#" data-account-id="${account.id}" data-account-name="${account.name}" data-account-balance="${account.balance}">
                        ${account.name} 
                        <small class="text-muted" >(${formatCurrency(account.balance)})</small>
                    </a>
                `;
                
                fromMenu.appendChild(fromItem);
                toMenu.appendChild(toItem);
            });
            
            // Add event listeners for Bootstrap dropdown selections
            setupBootstrapTransferListeners();
            
            // Show modal
            var transferModal = new bootstrap.Modal(document.getElementById('transferModal'));
            transferModal.show();
        })
        .catch(error => {
            console.error('Error loading accounts:', error);
            alert('Error loading accounts. Please refresh the page.');
        });
}

function loadAccountChart() {
    const chartCanvas = document.getElementById('accountChart');
    if (!chartCanvas) return;
    
    fetch('/account/api/chart-data')
        .then(response => response.json())
        .then(data => {
            if (data.labels.length === 0) {
                // Show message when no data
                document.getElementById('chartContainer').innerHTML = `
                    <div class="card minimal-card h-100">
                        <div class="card-body text-center py-5">
                            <i class="fas fa-chart-pie fa-3x text-muted mb-3"></i>
                            <h5 class="text-muted">No account data available</h5>
                            <p class="text-muted">Add accounts to see the balance distribution.</p>
                        </div>
                    </div>
                `;
                // Clear account list
                const accountList = document.getElementById('account-list');
                if (accountList) {
                    accountList.innerHTML = '';
                }
                return;
            }
            
            const ctx = chartCanvas.getContext('2d');
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.data,
                        backgroundColor: data.backgroundColor, // Use the actual account colors from API
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
                                    const label = data.labels[context.dataIndex];
                                    const value = context.parsed;
                                    const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${label}: ${formatCurrency(value)} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
            
            // Update account list with percentages using real account colors
            updateAccountList(data, data.backgroundColor);
        })
        .catch(error => {
            console.error('Error loading chart data:', error);
            document.getElementById('chartContainer').style.display = 'none';
        });
}

/**
 * Update account list with percentages (similar to updateCategoryList in home.js)
 */
function updateAccountList(data, colors) {
    const listContainer = document.getElementById('account-list');
    if (!listContainer) return;
    
    // Calculate total and percentages
    const total = data.data.reduce((a, b) => a + b, 0);
    
    const listHTML = data.labels.map((label, index) => {
        const amount = data.data[index];
        const percentage = ((amount / total) * 100).toFixed(1);
        
        return `
            <div class="d-flex justify-content-between align-items-center py-1 border-bottom">
                <div class="d-flex align-items-center">
                    <div class="me-2" style="width: 12px; height: 12px; background-color: ${colors[index]}; border-radius: 50%;"></div>
                    <span class="small">${label}</span>
                </div>
                <div class="text-end">
                    <div class="fw-bold small">${formatCurrency(amount)}</div>
                    <div class="text-muted" style="font-size: 0.75rem;">${percentage}%</div>
                </div>
            </div>
        `;
    }).join('');
    
    listContainer.innerHTML = listHTML;
}

function loadRecentTransfers() {
    const transfersList = document.getElementById('recent-transfers-list');
    if (!transfersList) return;
    
    fetch('/account/api/recent-transfers')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                displayRecentTransfers(data.data.transfers);
            } else {
                showNoTransfersMessage();
            }
        })
        .catch(error => {
            console.error('Error loading recent transfers:', error);
            showNoTransfersMessage();
        });
}

function displayRecentTransfers(transfers) {
    const transfersList = document.getElementById('recent-transfers-list');
    
    if (transfers.length === 0) {
        showNoTransfersMessage();
        return;
    }
    
    const transfersHtml = transfers.map(transfer => `
        <div class="transfer-item d-flex justify-content-between align-items-center py-2 border-bottom">
            <div class="transfer-info">
                <div class="fw-semibold">${transfer.description}</div>
                <small class="text-muted">${transfer.formatted_date}</small>
                <div class="small text-muted">
                    <i class="fas fa-arrow-right me-1"></i>
                    ${transfer.from_account} → ${transfer.to_account}
                </div>
            </div>
            <div class="transfer-amount">
                <span class="fw-bold text-primary">
                    ${transfer.formatted_amount}
                </span>
                <div class="dropdown ms-2" style="display: inline-block;">
                    <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="#" onclick="viewTransferDetails(${transfer.id})">View Details</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="#" onclick="deleteTransfer(${transfer.id})">Reverse Transfer</a></li>
                    </ul>
                </div>
            </div>
        </div>
    `).join('');
    
    transfersList.innerHTML = transfersHtml;
}

function showNoTransfersMessage() {
    const transfersList = document.getElementById('recent-transfers-list');
    transfersList.innerHTML = `
        <div class="text-center py-4">
            <i class="fas fa-exchange-alt fa-3x text-muted mb-3"></i>
            <p class="text-muted">No transfers yet. Use Quick Transfer to move money between accounts!</p>
        </div>
    `;
}

function handleTransferSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.textContent;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        // Check if response is JSON or a redirect
        if (response.headers.get('content-type')?.includes('application/json')) {
            return response.json();
        } else {
            // If it's a redirect, it means the transfer was successful but processed as a regular form
            if (response.redirected || response.status === 302) {
                return { status: 'success', message: 'Transfer completed successfully!' };
            } else {
                throw new Error('Unexpected response type');
            }
        }
    })
    .then(data => {
        if (data.status === 'success') {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('transferModal'));
            modal.hide();
            
            // Reset form
            form.reset();
            
            // Show success message
            showAlert('Transfer completed successfully!', 'success');
            
            // Refresh data
            loadRecentTransfers();
            loadAccountChart();
            
            // Reload page to update account balances
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showAlert(data.message || 'Transfer failed. Please try again.', 'danger');
        }
    })
    .catch(error => {
        console.error('Transfer error:', error);
        showAlert('An error occurred during the transfer. Please try again.', 'danger');
    })
    .finally(() => {
        // Restore button state
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    });
}

function showAlert(message, type) {
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
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }
    }, 2500);
}

function viewTransferDetails(transferId) {
    fetch(`/account/api/transfer/${transferId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert('Transfer not found', 'danger');
                return;
            }
            
            // Create and show transfer details modal
            const modalHtml = `
                <div class="modal fade" id="transferDetailsModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Transfer Details</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row mb-3">
                                    <div class="col-6">
                                        <label class="form-label text-muted">Amount</label>
                                        <div class="h4 text-primary">${data.formatted_amount}</div>
                                    </div>
                                    <div class="col-6">
                                        <label class="form-label text-muted">Date</label>
                                        <div>${data.formatted_date}</div>
                                    </div>
                                </div>
                                <div class="row mb-3">
                                    <div class="col-6">
                                        <label class="form-label text-muted">From Account</label>
                                        <div class="fw-semibold">${data.from_account.name}</div>
                                        <small class="text-muted">Balance: ${formatCurrency(data.from_account.balance)}</small>
                                    </div>
                                    <div class="col-6">
                                        <label class="form-label text-muted">To Account</label>
                                        <div class="fw-semibold">${data.to_account.name}</div>
                                        <small class="text-muted">Balance: ${formatCurrency(data.to_account.balance)}</small>
                                    </div>
                                </div>
                                ${data.description ? `
                                <div class="mb-3">
                                    <label class="form-label text-muted">Description</label>
                                    <div>${data.description}</div>
                                </div>
                                ` : ''}
                                <div class="row">
                                    <div class="col-6">
                                        <label class="form-label text-muted">From Transaction ID</label>
                                        <div class="small">#${data.transactions.from_transaction_id}</div>
                                    </div>
                                    <div class="col-6">
                                        <label class="form-label text-muted">To Transaction ID</label>
                                        <div class="small">#${data.transactions.to_transaction_id}</div>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                <button type="button" class="btn btn-danger" onclick="deleteTransfer(${data.id})">Reverse Transfer</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('transferDetailsModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add modal to DOM and show it
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = new bootstrap.Modal(document.getElementById('transferDetailsModal'));
            modal.show();
            
            // Remove modal from DOM when hidden
            document.getElementById('transferDetailsModal').addEventListener('hidden.bs.modal', function() {
                this.remove();
            });
        })
        .catch(error => {
            console.error('Error loading transfer details:', error);
            showAlert('Error loading transfer details', 'danger');
        });
}

function deleteTransfer(transferId) {
    // Fetch transfer details first
    fetch(`/account/api/transfer/${transferId}`)
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                // Populate modal with transfer details
                document.getElementById('reverseTransferAmount').textContent = data.formatted_amount;
                document.getElementById('reverseTransferFrom').textContent = data.from_account.name;
                document.getElementById('reverseTransferTo').textContent = data.to_account.name;
                document.getElementById('reverseTransferDate').textContent = data.formatted_date;
                document.getElementById('reverseTransferDescription').textContent = data.description || 'No description';
                
                // Store transfer ID for confirmation
                document.getElementById('confirmReverseTransfer').setAttribute('data-transfer-id', transferId);
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('reverseTransferModal'));
                modal.show();
            } else {
                showAlert('Transfer not found', 'danger');
            }
        })
        .catch(error => {
            console.error('Error loading transfer details:', error);
            showAlert('Error loading transfer details', 'danger');
        });
}

function loadTransferSummary() {
    fetch('/account/api/transfer-summary')
        .then(response => response.json())
        .then(data => {
            // Update transfer summary in UI if elements exist
            const totalTransfersElement = document.getElementById('total-transfers');
            const totalAmountElement = document.getElementById('total-transfer-amount');
            const monthlyTransfersElement = document.getElementById('monthly-transfers');
            const monthlyAmountElement = document.getElementById('monthly-transfer-amount');
            
            if (totalTransfersElement) {
                totalTransfersElement.textContent = data.total_transfers;
            }
            if (totalAmountElement) {
                totalAmountElement.textContent = data.formatted_total_amount;
            }
            if (monthlyTransfersElement) {
                monthlyTransfersElement.textContent = data.monthly_transfers;
            }
            if (monthlyAmountElement) {
                monthlyAmountElement.textContent = data.formatted_monthly_amount;
            }
        })
        .catch(error => {
            console.error('Error loading transfer summary:', error);
        });
}

function loadAllTransfers() {
    fetch('/account/api/transfers?per_page=50')
        .then(response => response.json())
        .then(data => {
            const modalHtml = `
                <div class="modal fade" id="allTransfersModal" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">All Transfers</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body" style="max-height: 500px; overflow-y: auto;">
                                ${data.transfers.length === 0 ? 
                                    '<div class="text-center py-4"><p class="text-muted">No transfers found</p></div>' :
                                    data.transfers.map(transfer => `
                                        <div class="transfer-item d-flex justify-content-between align-items-center py-3 border-bottom">
                                            <div class="transfer-info">
                                                <div class="fw-semibold">${transfer.description}</div>
                                                <small class="text-muted">${transfer.formatted_date}</small>
                                                <div class="small text-muted">
                                                    <i class="fas fa-arrow-right me-1"></i>
                                                    ${transfer.from_account.name} → ${transfer.to_account.name}
                                                </div>
                                            </div>
                                            <div class="transfer-amount">
                                                <span class="fw-bold text-primary">${transfer.formatted_amount}</span>
                                                <div class="dropdown ms-2" style="display: inline-block;">
                                                    <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
                                                        <i class="fas fa-ellipsis-v"></i>
                                                    </button>
                                                    <ul class="dropdown-menu">
                                                        <li><a class="dropdown-item" href="#" onclick="viewTransferDetails(${transfer.id})">View Details</a></li>
                                                        <li><hr class="dropdown-divider"></li>
                                                        <li><a class="dropdown-item text-danger" href="#" onclick="deleteTransfer(${transfer.id})">Reverse Transfer</a></li>
                                                    </ul>
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')
                                }
                            </div>
                            <div class="modal-footer">
                                <div class="d-flex justify-content-between w-100">
                                    <small class="text-muted align-self-center">
                                        Showing ${data.transfers.length} of ${data.pagination.total} transfers
                                    </small>
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('allTransfersModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add modal to DOM and show it
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = new bootstrap.Modal(document.getElementById('allTransfersModal'));
            modal.show();
            
            // Remove modal from DOM when hidden
            document.getElementById('allTransfersModal').addEventListener('hidden.bs.modal', function() {
                this.remove();
            });
        })
        .catch(error => {
            console.error('Error loading transfers:', error);
            showAlert('Error loading transfers', 'danger');
        });
}

/**
 * Check URL parameters and auto-open modal if specified
 */
function checkAndOpenModal() {
    const urlParams = new URLSearchParams(window.location.search);
    const openModal = urlParams.get('openModal');
    const showTransfer = urlParams.get('show_transfer');
    
    if (openModal === 'addAccount') {
        // Wait for Bootstrap to be available and DOM to be ready
        const tryOpenModal = () => {
            const modalElement = document.getElementById('addAccountModal');
            if (modalElement && window.bootstrap) {
                try {
                    const addAccountModal = new bootstrap.Modal(modalElement);
                    addAccountModal.show();
                    
                    // Clean up the URL parameter after opening the modal
                    const url = new URL(window.location);
                    url.searchParams.delete('openModal');
                    window.history.replaceState({}, document.title, url.pathname);
                } catch (error) {
                    console.error('Error opening modal:', error);
                }
            } else {
                // If not ready, try again in a short while
                setTimeout(tryOpenModal, 50);
            }
        };
        
        // Start trying to open the modal
        setTimeout(tryOpenModal, 100);
    }
    
    if (showTransfer) {
        // Show transfer details modal for the specified transfer ID
        setTimeout(() => {
            viewTransferDetails(showTransfer);
            
            // Clean up the URL parameter after opening the modal
            const url = new URL(window.location);
            url.searchParams.delete('show_transfer');
            window.history.replaceState({}, document.title, url.pathname);
        }, 500); // Wait a bit longer for the page to fully load
    }
}

/**
 * Setup event listeners for Bootstrap transfer dropdowns
 */
function setupBootstrapTransferListeners() {
    // From Account dropdown listeners
    document.querySelectorAll('#fromAccountMenu .dropdown-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const accountId = this.getAttribute('data-account-id');
            const accountName = this.getAttribute('data-account-name');
            const accountBalance = this.getAttribute('data-account-balance');
            
            // Update hidden input
            document.getElementById('fromAccount').value = accountId;
            
            // Update button text
            document.getElementById('fromAccountText').textContent = `${accountName} (${formatCurrency(parseFloat(accountBalance))})`;
            
            // Update To Account dropdown to exclude selected account
            updateToAccountDropdown(accountId);
        });
    });
    
    // To Account dropdown listeners
    document.querySelectorAll('#toAccountMenu .dropdown-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            const accountId = this.getAttribute('data-account-id');
            const accountName = this.getAttribute('data-account-name');
            const accountBalance = this.getAttribute('data-account-balance');
            
            // Update hidden input
            document.getElementById('toAccount').value = accountId;
            
            // Update button text
            document.getElementById('toAccountText').textContent = `${accountName} (${formatCurrency(parseFloat(accountBalance))})`;
            
            // Update From Account dropdown to exclude selected account
            updateFromAccountDropdown(accountId);
        });
    });
}

/**
 * Update To Account dropdown to exclude selected From Account
 */
function updateToAccountDropdown(excludeId) {
    document.querySelectorAll('#toAccountMenu .dropdown-item').forEach(item => {
        const accountId = item.getAttribute('data-account-id');
        const listItem = item.parentElement;
        
        if (accountId === excludeId) {
            listItem.style.display = 'none';
        } else {
            listItem.style.display = 'block';
        }
    });
}

/**
 * Update From Account dropdown to exclude selected To Account
 */
function updateFromAccountDropdown(excludeId) {
    document.querySelectorAll('#fromAccountMenu .dropdown-item').forEach(item => {
        const accountId = item.getAttribute('data-account-id');
        const listItem = item.parentElement;
        
        if (accountId === excludeId) {
            listItem.style.display = 'none';
        } else {
            listItem.style.display = 'block';
        }
    });
}

/**
 * Setup event listeners for simple transfer select dropdowns
 */
function setupSimpleTransferListeners() {
    const fromSelect = document.getElementById('fromAccount');
    const toSelect = document.getElementById('toAccount');
    
    // Update "To Account" options when "From Account" changes
    fromSelect.addEventListener('change', function() {
        updateSelectOptions(toSelect, this.value);
    });
    
    // Update "From Account" options when "To Account" changes
    toSelect.addEventListener('change', function() {
        updateSelectOptions(fromSelect, this.value);
    });
}

/**
 * Update select options to exclude the selected account from the other dropdown
 */
function updateSelectOptions(selectElement, excludeValue) {
    const options = selectElement.querySelectorAll('option');
    
    options.forEach(option => {
        if (option.value === excludeValue && option.value !== '') {
            option.style.display = 'none';
            option.disabled = true;
        } else {
            option.style.display = 'block';
            option.disabled = false;
        }
    });
}

/**
 * Setup event listeners for transfer account dropdown selections
 */
function setupTransferDropdownListeners() {
    // From Account dropdown listeners
    document.querySelectorAll('.from-account-option').forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            
            const accountId = this.getAttribute('data-id');
            const accountName = this.getAttribute('data-name');
            const accountBalance = this.getAttribute('data-balance');
            const accountColor = this.getAttribute('data-color');
            
            // Update hidden select
            document.getElementById('fromAccount').value = accountId;
            
            // Update visible dropdown button
            document.getElementById('selectedFromAccountDot').style.backgroundColor = accountColor;
            document.getElementById('selectedFromAccountName').textContent = `${accountName} (${formatCurrency(parseFloat(accountBalance))})`;
            
            // Update "To Account" dropdown to exclude selected account
            updateToAccountOptions();
        });
    });
    
    // To Account dropdown listeners
    document.querySelectorAll('.to-account-option').forEach(option => {
        option.addEventListener('click', function(e) {
            e.preventDefault();
            
            const accountId = this.getAttribute('data-id');
            const accountName = this.getAttribute('data-name');
            const accountBalance = this.getAttribute('data-balance');
            const accountColor = this.getAttribute('data-color');
            
            // Update hidden select
            document.getElementById('toAccount').value = accountId;
            
            // Update visible dropdown button
            document.getElementById('selectedToAccountDot').style.backgroundColor = accountColor;
            document.getElementById('selectedToAccountName').textContent = `${accountName} (${formatCurrency(parseFloat(accountBalance))})`;
            
            // Update "From Account" dropdown to exclude selected account
            updateFromAccountOptions();
        });
    });
}

/**
 * Update To Account options to exclude selected From Account
 */
function updateToAccountOptions() {
    const selectedFromId = document.getElementById('fromAccount').value;
    const toOptions = document.querySelectorAll('.to-account-option');
    
    toOptions.forEach(option => {
        const optionId = option.getAttribute('data-id');
        const listItem = option.parentElement;
        
        if (optionId === selectedFromId) {
            listItem.style.display = 'none';
        } else {
            listItem.style.display = 'block';
        }
    });
}

/**
 * Update From Account options to exclude selected To Account
 */
function updateFromAccountOptions() {
    const selectedToId = document.getElementById('toAccount').value;
    const fromOptions = document.querySelectorAll('.from-account-option');
    
    fromOptions.forEach(option => {
        const optionId = option.getAttribute('data-id');
        const listItem = option.parentElement;
        
        if (optionId === selectedToId) {
            listItem.style.display = 'none';
        } else {
            listItem.style.display = 'block';
        }
    });
}

// Flash message handling has been removed - base.html and base.js handle everything
// Society Management System - Main JavaScript File

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize all components
    initAutoHideAlerts();
    initFormValidation();
    initTableSearch();
    initPrintButtons();
    initConfirmationDialogs();
    initDateTimeFormatting();
    
});

// ============================================
// 1. AUTO-HIDE ALERTS/FLASH MESSAGES
// ============================================
function initAutoHideAlerts() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert) {
                // Fade out effect
                alert.style.transition = 'opacity 1s';
                alert.style.opacity = '0';
                
                // Remove after fade
                setTimeout(function() {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 1000);
            }
        }, 5000);
    });
}

// ============================================
// 2. FORM VALIDATION
// ============================================
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');
            
            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    highlightField(field, 'This field is required');
                } else {
                    removeHighlight(field);
                    
                    // Email validation
                    if (field.type === 'email' && !isValidEmail(field.value)) {
                        isValid = false;
                        highlightField(field, 'Please enter a valid email address');
                    }
                    
                    // Phone number validation
                    if (field.name === 'contact' && field.value && !isValidPhone(field.value)) {
                        isValid = false;
                        highlightField(field, 'Please enter a valid phone number');
                    }
                }
            });
            
            if (!isValid) {
                event.preventDefault();
                showNotification('Please fix the errors in the form', 'error');
            }
        });
    });
}

// Helper: Highlight invalid field
function highlightField(field, message) {
    field.classList.add('is-invalid');
    
    // Remove existing error message
    const nextElement = field.nextElementSibling;
    if (nextElement && nextElement.classList.contains('invalid-feedback')) {
        nextElement.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.insertBefore(errorDiv, field.nextSibling);
}

// Helper: Remove highlight
function removeHighlight(field) {
    field.classList.remove('is-invalid');
    const nextElement = field.nextElementSibling;
    if (nextElement && nextElement.classList.contains('invalid-feedback')) {
        nextElement.remove();
    }
}

// Helper: Email validation
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Helper: Phone validation
function isValidPhone(phone) {
    const re = /^[\d\s\+\-\(\)]{10,15}$/;
    return re.test(phone);
}

// ============================================
// 3. TABLE SEARCH FUNCTIONALITY
// ============================================
function initTableSearch() {
    // Add search box to tables
    const tables = document.querySelectorAll('table');
    
    tables.forEach(function(table, index) {
        // Check if table has data
        if (table.querySelector('tbody tr') && !table.closest('.no-search')) {
            addSearchBox(table, index);
        }
    });
}

function addSearchBox(table, index) {
    // Create search container
    const searchDiv = document.createElement('div');
    searchDiv.className = 'row mb-3';
    searchDiv.innerHTML = `
        <div class="col-md-4 offset-md-8">
            <div class="input-group">
                <span class="input-group-text"><i class="bi bi-search"></i>🔍</span>
                <input type="text" class="form-control" id="tableSearch${index}" 
                       placeholder="Search in table...">
            </div>
        </div>
    `;
    
    // Insert search box before table
    table.parentNode.insertBefore(searchDiv, table);
    
    // Add search functionality
    const searchInput = document.getElementById(`tableSearch${index}`);
    const rows = table.querySelectorAll('tbody tr');
    
    searchInput.addEventListener('keyup', function() {
        const searchTerm = this.value.toLowerCase();
        
        rows.forEach(function(row) {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        // Show "no results" message
        showNoResultsMessage(table, rows, searchTerm);
    });
}

function showNoResultsMessage(table, rows, searchTerm) {
    const tbody = table.querySelector('tbody');
    let noResultsRow = document.getElementById('noResultsRow');
    
    // Check if any rows are visible
    const visibleRows = Array.from(rows).filter(row => row.style.display !== 'none');
    
    if (visibleRows.length === 0 && searchTerm) {
        // Remove existing no results row
        if (noResultsRow) {
            noResultsRow.remove();
        }
        
        // Add no results row
        noResultsRow = document.createElement('tr');
        noResultsRow.id = 'noResultsRow';
        const colspan = table.querySelector('thead tr').children.length;
        noResultsRow.innerHTML = `<td colspan="${colspan}" class="text-center text-muted">
            No results found for "${searchTerm}"
        </td>`;
        tbody.appendChild(noResultsRow);
    } else if (noResultsRow) {
        noResultsRow.remove();
    }
}

// ============================================
// 4. PRINT BUTTONS
// ============================================
function initPrintButtons() {
    // Add print button to cards with data-print attribute
    const printContainers = document.querySelectorAll('[data-print="true"]');
    
    printContainers.forEach(function(container) {
        const printBtn = document.createElement('button');
        printBtn.className = 'btn btn-sm btn-secondary float-end';
        printBtn.innerHTML = '🖨️ Print';
        printBtn.onclick = function() {
            printContainer(container);
        };
        
        // Add button to header
        const header = container.querySelector('.card-header');
        if (header) {
            header.appendChild(printBtn);
        }
    });
}

function printContainer(container) {
    const printWindow = window.open('', '_blank');
    const content = container.innerHTML;
    const styles = document.querySelectorAll('style, link[rel="stylesheet"]');
    let stylesHTML = '';
    
    styles.forEach(function(style) {
        stylesHTML += style.outerHTML;
    });
    
    printWindow.document.write(`
        <html>
            <head>
                <title>Print - Society Management System</title>
                ${stylesHTML}
                <style>
                    body { padding: 20px; }
                    .btn, .no-print { display: none; }
                </style>
            </head>
            <body>
                <div class="container">
                    ${content}
                </div>
                <script>
                    window.onload = function() { window.print(); window.close(); }
                </script>
            </body>
        </html>
    `);
    
    printWindow.document.close();
}

// ============================================
// 5. CONFIRMATION DIALOGS
// ============================================
function initConfirmationDialogs() {
    // Intercept delete links
    const deleteLinks = document.querySelectorAll('a[onclick*="confirm"]');
    
    deleteLinks.forEach(function(link) {
        link.addEventListener('click', function(event) {
            const originalConfirm = link.getAttribute('onclick');
            const message = originalConfirm.match(/'([^']*)'/)[1] || 'Are you sure?';
            
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
    
    // Add confirmation to any element with data-confirm attribute
    const confirmElements = document.querySelectorAll('[data-confirm]');
    
    confirmElements.forEach(function(element) {
        element.addEventListener('click', function(event) {
            const message = element.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
}

// ============================================
// 6. DATE/TIME FORMATTING
// ============================================
function initDateTimeFormatting() {
    // Format all elements with data-date attribute
    const dateElements = document.querySelectorAll('[data-date]');
    
    dateElements.forEach(function(element) {
        const dateStr = element.getAttribute('data-date');
        if (dateStr) {
            const date = new Date(dateStr);
            element.textContent = formatDate(date);
        }
    });
    
    // Format all elements with data-datetime attribute
    const datetimeElements = document.querySelectorAll('[data-datetime]');
    
    datetimeElements.forEach(function(element) {
        const datetimeStr = element.getAttribute('data-datetime');
        if (datetimeStr) {
            const date = new Date(datetimeStr);
            element.textContent = formatDateTime(date);
        }
    });
}

function formatDate(date) {
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(date) {
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ============================================
// 7. NOTIFICATION SYSTEM
// ============================================
function showNotification(message, type = 'info') {
    // Create notification container if it doesn't exist
    let container = document.getElementById('notificationContainer');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 350px;
        `;
        document.body.appendChild(container);
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(function() {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// ============================================
// 8. DASHBOARD STATISTICS ANIMATION
// ============================================
function animateNumbers() {
    const statNumbers = document.querySelectorAll('.card h2');
    
    statNumbers.forEach(function(element) {
        const finalValue = parseInt(element.textContent);
        if (!isNaN(finalValue) && finalValue > 0) {
            animateValue(element, 0, finalValue, 1000);
        }
    });
}

function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 10);
    let current = start;
    
    const timer = setInterval(function() {
        current += increment;
        if (current >= end) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 10);
}

// ============================================
// 9. STATUS COLOR HELPER
// ============================================
function getStatusBadge(status) {
    let color = 'secondary';
    
    switch(status?.toLowerCase()) {
        case 'pending':
            color = 'warning';
            break;
        case 'in progress':
            color = 'info';
            break;
        case 'completed':
            color = 'success';
            break;
        case 'checked out':
            color = 'secondary';
            break;
        case 'in building':
            color = 'success';
            break;
    }
    
    return `<span class="badge bg-${color}">${status}</span>`;
}

// ============================================
// 10. EXPORT TABLE TO CSV
// ============================================
function exportTableToCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csvData = [];
    
    rows.forEach(function(row) {
        const rowData = [];
        const cols = row.querySelectorAll('td, th');
        
        cols.forEach(function(col) {
            rowData.push('"' + col.textContent.trim() + '"');
        });
        
        csvData.push(rowData.join(','));
    });
    
    const csvString = csvData.join('\n');
    const blob = new Blob([csvString], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    
    window.URL.revokeObjectURL(url);
}

// ============================================
// 11. TOGGLE SIDEBAR (if needed)
// ============================================
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        if (mainContent) {
            mainContent.classList.toggle('expanded');
        }
    }
}

// ============================================
// 12. AUTO-REFRESH DASHBOARD (optional)
// ============================================
let autoRefreshInterval;

function startAutoRefresh(seconds = 30) {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(function() {
        if (window.location.pathname.includes('dashboard')) {
            location.reload();
        }
    }, seconds * 1000);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
}

// ============================================
// 13. INITIALIZE ALL TOOLTIPS
// ============================================
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-toggle="tooltip"]');
    tooltips.forEach(function(element) {
        element.setAttribute('title', element.getAttribute('data-title') || '');
    });
}

// ============================================
// 14. FORM RESET HANDLER
// ============================================
function initFormReset() {
    const resetButtons = document.querySelectorAll('button[type="reset"]');
    
    resetButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const form = button.closest('form');
            if (form) {
                setTimeout(function() {
                    form.querySelectorAll('.is-invalid').forEach(function(field) {
                        field.classList.remove('is-invalid');
                    });
                    
                    form.querySelectorAll('.invalid-feedback').forEach(function(feedback) {
                        feedback.remove();
                    });
                }, 100);
            }
        });
    });
}

// Initialize everything on page load
window.addEventListener('load', function() {
    animateNumbers();
    initTooltips();
    initFormReset();
});

// Export functions for use in HTML
window.societyManagement = {
    showNotification: showNotification,
    exportTableToCSV: exportTableToCSV,
    toggleSidebar: toggleSidebar,
    startAutoRefresh: startAutoRefresh,
    stopAutoRefresh: stopAutoRefresh,
    getStatusBadge: getStatusBadge
};
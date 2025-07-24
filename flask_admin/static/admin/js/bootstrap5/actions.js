// bootstrap5/actions.js

class AdminModelActions {
    constructor(actionErrorMessage, actionConfirmations) {
        this.actionErrorMessage = actionErrorMessage;
        this.actionConfirmations = actionConfirmations;
        
        this.init();
    }
    
    execute(name) {
        const selectedCheckboxes = document.querySelectorAll('input.action-checkbox:checked');
        
        if (selectedCheckboxes.length === 0) {
            // Use Bootstrap 5 alert/toast if available, fallback to browser alert
            if (window.bootstrap && window.bootstrap.Toast) {
                this.showToast(this.actionErrorMessage, 'warning');
            } else {
                alert(this.actionErrorMessage);
            }
            return false;
        }
        
        const confirmMessage = this.actionConfirmations[name];
        if (confirmMessage) {
            if (!confirm(confirmMessage)) {
                return false;
            }
        }
        
        // Update hidden form and submit it
        const form = document.getElementById('action_form');
        if (!form) {
            console.error('Action form not found');
            return false;
        }
        
        // Set action value
        const actionInput = form.querySelector('input[name="action"]');
        if (actionInput) {
            actionInput.value = name;
        }
        
        // Remove existing checkboxes from form
        form.querySelectorAll('input.action-checkbox').forEach(input => input.remove());
        
        // Clone checked checkboxes to form
        selectedCheckboxes.forEach(checkbox => {
            const clone = checkbox.cloneNode(true);
            clone.style.display = 'none'; // Hide cloned checkboxes
            form.appendChild(clone);
        });
        
        form.submit();
        return false;
    }
    
    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1055';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        // Initialize and show toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: 4000
        });
        
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
    
    initSelectAll() {
        const selectAllCheckbox = document.querySelector('.action-rowtoggle');
        const individualCheckboxes = document.querySelectorAll('input.action-checkbox');
        
        if (!selectAllCheckbox) return;
        
        // Handle select all checkbox change
        selectAllCheckbox.addEventListener('change', (event) => {
            const isChecked = event.target.checked;
            individualCheckboxes.forEach(checkbox => {
                checkbox.checked = isChecked;
                // Trigger change event for any listeners
                checkbox.dispatchEvent(new Event('change', { bubbles: true }));
            });
            
            this.updateSelectAllState();
        });
        
        // Handle individual checkbox changes
        individualCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateSelectAllState();
            });
        });
        
        // Initial state update
        this.updateSelectAllState();
    }
    
    updateSelectAllState() {
        const selectAllCheckbox = document.querySelector('.action-rowtoggle');
        const individualCheckboxes = document.querySelectorAll('input.action-checkbox');
        
        if (!selectAllCheckbox || individualCheckboxes.length === 0) return;
        
        const checkedCount = document.querySelectorAll('input.action-checkbox:checked').length;
        const totalCount = individualCheckboxes.length;
        
        if (checkedCount === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCount === totalCount) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
        
        // Update visual state for better UX
        this.updateBulkActionsVisibility(checkedCount);
    }
    
    updateBulkActionsVisibility(selectedCount) {
        // Show/hide bulk actions based on selection
        const bulkActionsDropdown = document.querySelector('.nav-item:has(.fa-cogs)');
        const bulkActionsLink = document.querySelector('.nav-item .fa-cogs')?.closest('button');
        
        if (bulkActionsDropdown && bulkActionsLink) {
            if (selectedCount > 0) {
                // Enable bulk actions
                bulkActionsLink.classList.remove('disabled');
                bulkActionsLink.setAttribute('data-bs-toggle', 'dropdown');
            } else {
                // Disable bulk actions
                bulkActionsLink.classList.add('disabled');
                bulkActionsLink.removeAttribute('data-bs-toggle');
            }
        }
        
        // Update counter in bulk actions button
        if (bulkActionsLink && selectedCount > 0) {
            const badge = bulkActionsLink.querySelector('.badge') || document.createElement('span');
            badge.className = 'badge bg-warning text-dark ms-1';
            badge.textContent = selectedCount;
            if (!bulkActionsLink.querySelector('.badge')) {
                bulkActionsLink.appendChild(badge);
            }
        } else {
            const badge = bulkActionsLink?.querySelector('.badge');
            if (badge) badge.remove();
        }
    }
    
    init() {
        // Initialize select all functionality
        this.initSelectAll();
        
        // Add visual feedback for row selection
        document.addEventListener('change', (event) => {
            if (event.target.classList.contains('action-checkbox')) {
                const row = event.target.closest('tr');
                if (row) {
                    if (event.target.checked) {
                        row.classList.add('table-active');
                    } else {
                        row.classList.remove('table-active');
                    }
                }
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Get configuration data
    const messageData = document.getElementById('message-data');
    const actionsData = document.getElementById('actions-confirmation-data');
    
    if (messageData && actionsData) {
        try {
            const actionErrorMessage = JSON.parse(messageData.textContent);
            const actionConfirmations = JSON.parse(actionsData.textContent);
            
            // Create global instance
            window.modelActions = new AdminModelActions(actionErrorMessage, actionConfirmations);
            
        } catch (error) {
            console.error('Error initializing admin model actions:', error);
            // Fallback to basic functionality
            window.modelActions = {
                execute: function(name) {
                    const selected = document.querySelectorAll('input.action-checkbox:checked').length;
                    if (selected === 0) {
                        alert('Please select at least one record.');
                        return false;
                    }
                    return confirm('Are you sure you want to perform this action?');
                }
            };
        }
    }
    
    // Initialize tooltips for action buttons
    const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipElements.forEach(element => {
        new bootstrap.Tooltip(element);
    });
});

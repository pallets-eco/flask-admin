// bootstrap5/modal.js

document.addEventListener('DOMContentLoaded', function() {
    // Handle modal trigger clicks using event delegation
    document.body.addEventListener('click', function(event) {
        // Find the closest trigger element (an element with both `data-bs-toggle="modal"` and an `href`)
        const trigger = event.target.closest('[data-bs-toggle="modal"][href]');
        if (!trigger) return;
        
        event.preventDefault();
        
        const targetSelector = trigger.getAttribute('data-bs-target');
        const href = trigger.getAttribute('href');
        
        if (!targetSelector || !href) return;
        
        const modalElement = document.querySelector(targetSelector);
        if (!modalElement) {
            console.error(`Modal target "${targetSelector}" not found.`);
            return;
        }

        const modalContent = modalElement.querySelector('.modal-content');
        if (!modalContent) {
            console.error('Modal is missing a .modal-content container.');
            return;
        }

        // Use getOrCreateInstance to prevent creating duplicate modal objects.
        const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
        
        // Load modal content from the href via fetch
        fetch(href)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status} ${response.statusText}`);
                }
                return response.text();
            })
            .then(html => {
                modalContent.innerHTML = html;
                modal.show();
                
                // Dispatch a specific, contextual event so other scripts know that
                // modal content is ready and where to find it.
                const contentLoadedEvent = new CustomEvent('fa.modal.contentLoaded', {
                    bubbles: true,
                    detail: {
                        // Pass the container of the new content as the event detail.
                        // This is more efficient than forcing listeners to re-scan the whole DOM.
                        contentContainer: modalContent
                    }
                });
                modalContent.dispatchEvent(contentLoadedEvent);
                // =====================================================================
            })
            .catch(error => {
                console.error('Error loading modal content:', error);
                // Display a user-friendly error inside the modal
                modalContent.innerHTML = `
                    <div class="modal-header">
                        <h5 class="modal-title text-danger">Error</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>Could not load the requested content.</p>
                        <p class="text-muted small">${error.message}</p>
                    </div>`;
                modal.show();
            });
    });

    // Listen for any modal on the page to be hidden.
    document.body.addEventListener('hidden.bs.modal', function(event) {
        // `event.target` is the modal element that was just hidden.
        const modalContent = event.target.querySelector('.modal-content');
        if (modalContent) {
            // Clear the content to ensure it's fresh the next time it's opened
            // and to clean up any event listeners attached to the old content.
            modalContent.innerHTML = '';
        }
    });
});
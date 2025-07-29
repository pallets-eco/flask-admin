// bootstrap5/form.js

(function() {
    /**
     * AdminForm class handles the initialization of form widgets and inline forms
     * for the Flask-Admin interface, adapted for Bootstrap 5.
     */
    class AdminForm {
        constructor() {
            this.fieldConverters = [];
        }

        // --- Private Plugin Initializers (jQuery-dependent) ---

        _initSelect2($el) {
            if (!$.fn.select2) return;
            const opts = {
                width: '100%',
                theme: 'bootstrap-5',
                placeholder: $el.data('placeholder'),
                allowClear: $el.data('allow-blank') || false,
                minimumInputLength: $el.data('minimum-input-length') || 0,
            };

            // detect if the select2 is inside a modal
            const modal = $el.closest('.modal');
            if (modal.length > 0) {
                opts.dropdownParent = modal;
            }

            if ($el.data('tags')) {
                opts.tags = true;
                opts.tokenSeparators = [','];
            }

            $el.select2(opts);
        }

        _initSelect2Ajax($el) {
            if (!$.fn.select2) return;
            const opts = {
                width: '100%',
                theme: 'bootstrap-5',
                placeholder: $el.data('placeholder'),
                minimumInputLength: $el.data('minimum-input-length'),
                ajax: {
                    url: $el.data('url'),
                    dataType: 'json',
                    data: (params) => ({
                        query: params.term,
                        page: params.page || 1
                    }),
                    processResults: (data) => ({
                        results: data.results,
                        pagination: { more: data.more }
                    }),
                },
                initSelection: (element, callback) => {
                    const $el = $(element);
                    const data = JSON.parse($el.attr('data-json'));
                    if (data) {
                        callback(Array.isArray(data) ? data.map(v => ({id: v[0], text: v[1]})) : {id: data[0], text: data[1]});
                    }
                }
            };

            // detect if the select2 is inside a modal
            const modal = $el.closest('.modal');
            if (modal.length > 0) {
                opts.dropdownParent = modal;
            }

            $el.select2(opts);
        }

        // --- Public API Methods ---

        /**
         * Applies a specific style plugin to a single element.
         * This can be called externally on dynamically added elements.
         * @param {jQuery Element} $el - The element to style (passed as jQuery object for plugins).
         * @param {String} name - The data-role name.
         */
        applyStyle($el, name) {
            switch (name) {
                case 'select2':
                    this._initSelect2($el);
                    break;
                case 'select2-tags':
                    this._initSelect2($el.data('tags', true));
                    break;
                case 'select2-ajax':
                    this._initSelect2Ajax($el);
                    break;
            }
        }

        /**
         * Scans a parent DOM element and applies styles to all child elements
         * with a `data-role` attribute.
         * @param {DOMElement} parent - The container element to scan for stylable fields.
         */
        applyGlobalStyles(parent) {
            if (!parent) return;
            parent.querySelectorAll('[data-role]').forEach(el => {
                const $el = $(el); // Convert to jQuery object for plugins
                this.applyStyle($el, $el.data('role'));
            });
        }

        /**
         * Adds a new inline form group based on a template.
         * @param {DOMElement} el - The 'Add' button that was clicked.
         * @param {String} elID - The base ID of the form field.
         */
        addInlineField(el, elID) {
            const fieldsetContainer = el.closest('.inline-field');
            if (!fieldsetContainer) return;

            const fieldList = fieldsetContainer.querySelector('.inline-field-list');
            const template = fieldsetContainer.querySelector('.inline-field-template');
            if (!fieldList || !template) return;

            let maxId = -1;
            fieldList.querySelectorAll(':scope > .inline-field').forEach(field => {
                const parts = field.id.split('-');
                const idx = parseInt(parts[parts.length - 1], 10);
                if (!isNaN(idx) && idx > maxId) {
                    maxId = idx;
                }
            });
            const newId = maxId + 1;

            const newFieldHTML = template.innerHTML.replace(/__prefix__/g, newId);

            const parser = new DOMParser();
            const doc = parser.parseFromString(newFieldHTML, 'text/html');
            const newFieldNode = doc.body.firstChild;

            if (!newFieldNode) {
                console.error("Failed to create new inline field from template.");
                return;
            }

            newFieldNode.id = `${elID}-${newId}`;

            fieldList.appendChild(newFieldNode);
            this.applyGlobalStyles(newFieldNode);

            newFieldNode.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // --- Global Initialization ---

    // Expose faForm instance to the window scope to be accessible by other scripts.
    window.faForm = new AdminForm();

    // On initial page load, apply styles to the entire document body.
    document.addEventListener('DOMContentLoaded', () => {
        window.faForm.applyGlobalStyles(document.body);
        document.dispatchEvent(new CustomEvent('fa.main.ready', { bubbles: true }));
    });

    // Listen for the custom event dispatched by modal.js when modal content is ready.
    document.addEventListener('fa.modal.contentLoaded', function(event) {
        // Check if the event detail contains the content container.
        if (event.detail && event.detail.contentContainer) {
            // Call applyGlobalStyles ONLY on the new content, which is much more efficient.
            window.faForm.applyGlobalStyles(event.detail.contentContainer);
        }
    });

    // Event handler for removing inline form fields.
    document.body.addEventListener('click', function(event) {
        const removeButton = event.target.closest('.inline-remove-field');
        if (removeButton) {
            event.preventDefault();
            const confirmationMessage = removeButton.getAttribute('value') || 'Are you sure you want to delete this record?';
            if (confirm(confirmationMessage)) {
                removeButton.closest('.inline-field').remove();
            }
        }
    });

})();
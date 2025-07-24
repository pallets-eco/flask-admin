// bootstrap5/filters.js - Bootstrap 5 Filters Handler

class AdminFilters {
    constructor(element, filtersElement, filterGroups, activeFilters) {
        this.root = document.querySelector(element);
        this.card = this.root.querySelector('#filter-card');
        this.container = this.root.querySelector('.filters-list');
        this.filtersElement = filtersElement;
        this.filterGroups = filterGroups;
        this.activeFilters = activeFilters;
        this.lastCount = 0;
        
        this.init();
    }
    
    getCount(name) {
        const idx = name.indexOf('_');
        if (idx === -1) {
            return 0;
        }
        return parseInt(name.substr(3, idx - 3), 10);
    }
    
    makeName(name) {
        const result = 'flt' + this.lastCount + '_' + name;
        this.lastCount += 1;
        return result;
    }
    
    updateEmptyState() {
        const filterItems = this.container.querySelectorAll('.filter-item');
        const submitButton = this.root.querySelector('button[type="submit"]');

        if (filterItems.length === 0) {
            // If there are no filters, hide the entire card.
            this.card?.classList.add('d-none');
        } else {
            // If there are filters, ensure the card is visible.
            this.card?.classList.remove('d-none');
        }
    }
    
    removeFilter(event) {
        event.preventDefault();
        const filterItem = event.target.closest('.filter-item');
        if (filterItem) {
            filterItem.remove();
            this.updateEmptyState();

            // Removing a filter is a change, so show the "Apply" button if filters still exist.
            const submitButton = this.root.querySelector('button[type="submit"]');
            if (this.container.querySelectorAll('.filter-item').length > 0) {
                 submitButton?.classList.remove('d-none');
            }
        }
        return false;
    }
    
    changeOperation(subfilters, filterItem, select) {
        const selectedIndex = select.selectedIndex;
        const selectedFilter = subfilters[selectedIndex];
        const inputContainer = filterItem.querySelector('.filter-input-container');
        
        // Clear existing input
        inputContainer.innerHTML = '';
        
        // Create and style the new input field
        const field = this.createFilterInput(inputContainer, null, selectedFilter);
        this.styleFilterInput(selectedFilter, field);
        
        const submitButton = this.root.querySelector('button[type="submit"]');
        submitButton?.classList.remove('d-none');
    }
    
    createFilterInput(inputContainer, filterValue, filter) {
        let field;
        
        if (filter.type === "select2-tags") {
            field = document.createElement('input');
            field.type = 'hidden';
            field.className = 'filter-val form-control';
            field.name = this.makeName(filter.arg);
            field.value = filterValue || '';
        } else if (filter.options) {
            field = document.createElement('select');
            field.className = 'filter-val form-select form-select-sm';
            field.name = this.makeName(filter.arg);
            
            const emptyOption = document.createElement('option');
            emptyOption.value = '';
            emptyOption.textContent = '-- Select --';
            field.appendChild(emptyOption);
            
            filter.options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option[0];
                optionElement.textContent = option[1];
                if (filterValue && filterValue === option[0]) {
                    optionElement.selected = true;
                }
                field.appendChild(optionElement);
            });
        } else {
            field = document.createElement('input');
            field.type = 'text';
            field.className = 'filter-val form-control form-control-sm';
            field.name = this.makeName(filter.arg);
            field.value = filterValue || '';
            field.placeholder = 'Enter value...';
        }
        
        if (field.type === 'text') {
            const inputGroup = document.createElement('div');
            inputGroup.className = 'input-group input-group-sm';
            inputGroup.appendChild(field);

            const clearButton = document.createElement('button');
            clearButton.type = 'button';
            clearButton.className = 'btn btn-outline-secondary';
            clearButton.innerHTML = '<i class="fas fa-times"></i>';
            clearButton.title = 'Clear value';
            clearButton.addEventListener('click', () => {
                field.value = '';
                field.dispatchEvent(new Event('change', { bubbles: true }));
            });
            inputGroup.appendChild(clearButton);

            inputContainer.appendChild(inputGroup);
        } else {
            inputContainer.appendChild(field);
        }
        
        // Show the "Apply" button when the filter input changes
        field.addEventListener('input', () => {
            const submitButton = this.root.querySelector('button[type="submit"]');
            submitButton?.classList.remove('d-none');
        });
        
        field.addEventListener('change', () => {
            const submitButton = this.root.querySelector('button[type="submit"]');
            submitButton?.classList.remove('d-none');
        });
        
        return field;
    }
    
    styleFilterInput(filter, field) {
        if (filter.type) {
            if (filter.type === "datepicker") {
                field.type = 'date';
            } else if (filter.type === "daterangepicker") {
                this.createDateRange(field, 'date');
            } else if (filter.type === "datetimepicker") {
                field.type = 'datetime-local';
            } else if (filter.type === "datetimerangepicker") {
                this.createDateRange(field, 'datetime-local');
            } else if (filter.type === "timepicker") {
                field.type = 'time';
            } else if (filter.type === "timerangepicker") {
                this.createDateRange(field, 'time');
            }
            
            if (window.faForm && window.faForm.applyStyle) {
                window.faForm.applyStyle(field, filter.type);
            }
        } else if (filter.options) {
            filter.type = "select2";
            if (window.faForm && window.faForm.applyStyle) {
                window.faForm.applyStyle(field, filter.type);
            }
        }
        
        return field;
    }
    
    createDateRange(originalField, inputType) {
        const inputGroup = originalField.parentElement;
        
        const startField = document.createElement('input');
        startField.type = inputType;
        startField.name = originalField.name + '_start';
        startField.className = 'form-control form-control-sm filter-val';
        startField.placeholder = 'From...';
        
        const endField = document.createElement('input');
        endField.type = inputType;
        endField.name = originalField.name + '_end';
        endField.className = 'form-control form-control-sm filter-val';
        endField.placeholder = 'To...';
        
        const separator = document.createElement('span');
        separator.className = 'input-group-text';
        separator.innerHTML = '<i class="fas fa-arrow-right"></i>';
        
        inputGroup.replaceChild(startField, originalField);
        inputGroup.insertBefore(separator, inputGroup.lastElementChild);
        inputGroup.insertBefore(endField, inputGroup.lastElementChild);
        
        [startField, endField].forEach(field => {
            field.addEventListener('change', () => {
                const submitButton = this.root.querySelector('button[type="submit"]');
                submitButton?.classList.remove('d-none');
            });
        });
        
        return startField;
    }
    
    addFilter(name, subfilters, selectedIndex, filterValue) {
        const template = document.getElementById('filter-item-template');
        const filterItem = template.content.cloneNode(true).firstElementChild;

        this.container.appendChild(filterItem);

        filterItem.querySelector('.filter-name').textContent = name;
        
        const removeButton = filterItem.querySelector('.remove-filter');
        removeButton.addEventListener('click', (e) => this.removeFilter(e));
        
        const select = filterItem.querySelector('.filter-op');
        let filterSelection = 0;
        
        subfilters.forEach((subfilter, index) => {
            const option = document.createElement('option');
            option.value = subfilter.arg;
            option.textContent = subfilter.operation;
            
            if (subfilter.index === selectedIndex) {
                option.selected = true;
                filterSelection = index;
            }
            select.appendChild(option);
        });
        
        if (window.jQuery && window.jQuery.fn.select2) {
            window.jQuery(select).select2({
                width: 'resolve',
                theme: 'bootstrap-5',
                minimumResultsForSearch: Infinity
            }).on("change", () => {
                this.changeOperation(subfilters, filterItem, select);
            });
        } else {
            select.addEventListener('change', () => {
                this.changeOperation(subfilters, filterItem, select);
            });
        }
        
        const filter = subfilters[filterSelection];
        const inputContainer = filterItem.querySelector('.filter-input-container');
        
        const newFilterField = this.createFilterInput(inputContainer, filterValue, filter);
        const styledFilterField = this.styleFilterInput(filter, newFilterField);
        
        this.updateEmptyState();
        
        setTimeout(() => styledFilterField.focus(), 400);
        
        return styledFilterField;
    }
    
    init() {
        document.querySelectorAll(`${this.filtersElement} a.filter`).forEach(filterLink => {
            filterLink.addEventListener('click', (event) => {
                event.preventDefault();
                const name = filterLink.textContent.trim();
                this.addFilter(name, this.filterGroups[name], false, null);
            });
        });
        
        this.activeFilters.forEach(activeFilter => {
            const [idx, name, filterValue] = activeFilter;
            this.addFilter(name, this.filterGroups[name], idx, filterValue);
        });
        
        this.updateEmptyState();
        
        this.root.querySelectorAll('.filter-val').forEach(input => {
            const name = input.getAttribute('name');
            if (name) {
                const count = this.getCount(name);
                if (count > this.lastCount) {
                    this.lastCount = count;
                }
            }
        });
        
        this.lastCount += 1;

        if (this.activeFilters.length > 0) {
            const submitButton = this.root.querySelector('button[type="submit"]');
            submitButton?.classList.remove('d-none');
        }
    }
}

// Initialize when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('adminFormReady', function() {
        const filterGroupsData = document.getElementById('filter-groups-data');
        const activeFiltersData = document.getElementById('active-filters-data');
        
        if (filterGroupsData && activeFiltersData) {
            try {
                const filterGroups = JSON.parse(filterGroupsData.textContent);
                const activeFilters = JSON.parse(activeFiltersData.textContent);
                new AdminFilters('#filter_form', '.field-filters', filterGroups, activeFilters);
            } catch (error) {
                console.error('Error initializing admin filters:', error);
            }

            
        }
    });
    
    const formReadyEvent = new CustomEvent('adminFormReady');
    document.dispatchEvent(formReadyEvent);
});
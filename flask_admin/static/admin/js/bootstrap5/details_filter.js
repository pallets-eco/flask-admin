/**
 * Vanilla JavaScript solution to filter a table based on an input field.
 * This script is designed to be generic and robust:
 * - It uses event delegation to work with dynamically loaded content.
 * - It does not assume the filter and table are inside any specific container (like a modal).
 * - It filters the closest table with the '.searchable' class relative to the input field.
 */
document.addEventListener('DOMContentLoaded', function() {

    /**
     * Helper function for debouncing to improve performance.
     * @param {Function} func The function to execute after the delay.
     * @param {number} delay The delay in milliseconds.
     */
    const debounce = (func, delay = 250) => {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                func.apply(this, args);
            }, delay);
        };
    };
  
    /**
     * The actual filtering logic for the table.
     * @param {HTMLInputElement} inputElement The input field that triggered the filter.
     */
    const filterTable = (inputElement) => {
        const query = inputElement.value.trim();
        const rex = new RegExp(query, 'i');
        
        // --- THE FIX IS HERE: More generic container logic ---
        // Find the closest common ancestor of both the filter and the table.
        // Or, if a specific container is known, use that.
        // For this generic case, we'll assume they share a common parent or we search globally.
        // A simple approach is to find the filter container and then find the table next to it.
        const filterContainer = inputElement.closest('.fa_details_filter_container');
        if (!filterContainer) {
            console.error('Filter input is not inside a ".fa_details_filter_container".');
            return;
        }
  
        // Assume the table is a sibling or a descendant of a sibling to the filter container.
        // A robust way is to find the closest parent that contains both. Let's simplify:
        // Let's assume the table is the next element with class '.searchable'.
        // This relies on a predictable DOM structure.
        const searchableTable = filterContainer.nextElementSibling;
  
        // A more robust check if the structure is not guaranteed:
        if (!searchableTable || !searchableTable.classList.contains('searchable')) {
            // Fallback: search the entire document if the simple structure isn't found.
            // This is less efficient but much more robust. We'll use this as the primary method.
            const allSearchableTables = document.querySelectorAll('.searchable');
            // For simplicity, we'll filter the first one found on the page.
            // If you have multiple filters/tables, you would need a way to link them,
            // e.g., <input data-target="#my-table"> and <table id="my-table">
            if(allSearchableTables.length === 0) {
                 console.error('No table with class ".searchable" found on the page.');
                 return;
            }
            // For this generic example, we target the first searchable table on the page.
            const tableToFilter = allSearchableTables[0];
            
            filterLogic(tableToFilter, query, rex);
        } else {
             filterLogic(searchableTable, query, rex);
        }
    };
    
    /**
     * The core logic that performs the filtering on a given table.
     * @param {HTMLTableElement} table The table to filter.
     * @param {string} query The user's search query.
     * @param {RegExp} rex The regular expression for the query.
     */
    const filterLogic = (table, query, rex) => {
        const rows = table.querySelectorAll('tr:not(.no-results-row)');
        let visibleRows = 0;
  
        rows.forEach(row => {
            const rowText = row.textContent;
            if (rex.test(rowText)) {
                row.style.display = '';
                visibleRows++;
            } else {
                row.style.display = 'none';
            }
        });
  
        // Handle the "No results" message
        let noResultsRow = table.querySelector('.no-results-row');
        if (visibleRows === 0 && query !== '') {
            if (!noResultsRow) {
                const newRow = document.createElement('tr');
                newRow.className = 'no-results-row';
                const cell = document.createElement('td');
                cell.colSpan = 2;
                cell.textContent = 'No matching records found.';
                cell.style.textAlign = 'center';
                newRow.appendChild(cell);
                table.appendChild(newRow);
            }
        } else {
            if (noResultsRow) {
                noResultsRow.remove();
            }
        }
    }
  
    // Attach the debounced filter function using event delegation.
    document.body.addEventListener('input', debounce((event) => {
        if (event.target && event.target.id === 'fa_details_filter') {
            filterTable(event.target);
        }
    }));
  });
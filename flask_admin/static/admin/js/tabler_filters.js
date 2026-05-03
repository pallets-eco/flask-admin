// Vanilla JS replacement for bs4_filters.js.
// No jQuery, no select2. Works with Bootstrap 5 / Tabler.
//
// Data contract (unchanged from bs4 version):
//   #filter-groups-data  — JSON blob of filter group definitions
//   #active-filters-data — JSON blob of currently active filters
//   #filter_form         — the filter <form> element
//   .field-filters       — the dropdown menu whose <a class="filter"> items add filters

const AdminFilters = function (element, filtersElement, filterGroups, activeFilters) {
    const root = document.querySelector(element);
    const filterTable = root.querySelector('.filters');
    let lastCount = 0;

    // ── helpers ──────────────────────────────────────────────────────────────

    function getCount(name) {
        const idx = name.indexOf('_');
        if (idx === -1) return 0;
        return parseInt(name.substr(3, idx - 3), 10);
    }

    function makeName(name) {
        return 'flt' + (lastCount++) + '_' + name;
    }

    function showApplyButton() {
        root.querySelectorAll('button[type="submit"]').forEach(function (b) {
            b.classList.remove('d-none');
        });
    }

    function hideApplyButton() {
        root.querySelectorAll('button[type="submit"]').forEach(function (b) {
            b.classList.add('d-none');
        });
    }

    // Return the appropriate <input> type for a filter based on its type tag.
    function inputTypeFor(filter) {
        switch (filter.type) {
            case 'datepicker':
            case 'daterangepicker':
                return 'date';
            case 'datetimepicker':
            case 'datetimerangepicker':
                return 'datetime-local';
            case 'timepicker':
            case 'timerangepicker':
                return 'time';
            default:
                return 'text';
        }
    }

    // ── filter row management ────────────────────────────────────────────────

    // Build and insert the value <td>, replacing the placeholder td.
    function createFilterInput(placeholderTd, filterValue, filter) {
        const td = document.createElement('td');
        let field;

        if (filter.options) {
            field = document.createElement('select');
            field.className = 'filter-val form-select form-select-sm';
            filter.options.forEach(function (pair) {
                const opt = document.createElement('option');
                opt.value = pair[0];
                opt.textContent = pair[1];
                if (filterValue != null && filterValue == pair[0]) {
                    opt.selected = true;
                }
                field.appendChild(opt);
            });
        } else {
            field = document.createElement('input');
            field.type = inputTypeFor(filter);
            field.className = 'filter-val form-control form-control-sm';
            if (filterValue != null) field.value = filterValue;
        }

        field.name = makeName(filter.arg);
        field.addEventListener('input', showApplyButton);
        field.addEventListener('change', showApplyButton);
        td.appendChild(field);
        placeholderTd.replaceWith(td);
        return field;
    }

    // Rebuild the value cell when the operation <select> changes.
    function changeOperation(subfilters, row, opSelect) {
        const selectedFilter = subfilters[opSelect.selectedIndex];
        const lastTd = row.querySelector('td:last-child');
        createFilterInput(lastTd, null, selectedFilter);
        showApplyButton();
    }

    function removeFilter(row) {
        row.remove();
        const remaining = filterTable.querySelectorAll('tr');
        if (remaining.length === 0) {
            hideApplyButton();
        } else {
            showApplyButton();
        }
    }

    function addFilter(name, subfilters, selectedIndex, filterValue) {
        // Ensure a <tbody> exists in the filter table.
        let tbody = filterTable.querySelector('tbody');
        if (!tbody) {
            tbody = document.createElement('tbody');
            filterTable.appendChild(tbody);
        }

        const row = document.createElement('tr');
        tbody.appendChild(row);

        // Cell 1: remove button + filter name label.
        const labelTd = document.createElement('td');
        const removeBtn = document.createElement('a');
        removeBtn.href = '#';
        removeBtn.className = 'btn btn-secondary btn-sm remove-filter';
        removeBtn.innerHTML = '<span>&times;</span>&nbsp;' + name;
        removeBtn.addEventListener('click', function (e) {
            e.preventDefault();
            removeFilter(row);
        });
        labelTd.appendChild(removeBtn);
        row.appendChild(labelTd);

        // Cell 2: operation <select> (equals, not equals, …).
        const opTd = document.createElement('td');
        const opSelect = document.createElement('select');
        opSelect.className = 'filter-op form-select form-select-sm';

        let filterSelection = 0;
        subfilters.forEach(function (subfilter, i) {
            const opt = document.createElement('option');
            opt.value = subfilter.arg;
            opt.textContent = subfilter.operation;
            if (subfilter.index == selectedIndex) {
                opt.selected = true;
                filterSelection = i;
            }
            opSelect.appendChild(opt);
        });
        opTd.appendChild(opSelect);
        row.appendChild(opTd);

        // Cell 3: value input (placeholder replaced by createFilterInput).
        const valueTd = document.createElement('td');
        row.appendChild(valueTd);

        const filter = subfilters[filterSelection];
        const field = createFilterInput(valueTd, filterValue, filter);

        opSelect.addEventListener('change', function () {
            changeOperation(subfilters, row, opSelect);
        });

        field.focus();
        return field;
    }

    // ── event wiring ─────────────────────────────────────────────────────────

    // "Add Filter" dropdown clicks.
    const filtersMenu = document.querySelector(filtersElement);
    if (filtersMenu) {
        filtersMenu.addEventListener('click', function (e) {
            const link = e.target.closest('a.filter');
            if (!link) return;
            const name = link.textContent.trim();
            addFilter(name, filterGroups[name], false, null);
            showApplyButton();
        });
    }

    // Restore active filters on page load.
    activeFilters.forEach(function (activeFilter) {
        const idx = activeFilter[0];
        const name = activeFilter[1];
        const filterValue = activeFilter[2];
        addFilter(name, filterGroups[name], idx, filterValue);
    });

    // Sync lastCount from any pre-rendered filter-val inputs.
    root.querySelectorAll('.filter-val').forEach(function (el) {
        const count = getCount(el.name || '');
        if (count > lastCount) lastCount = count;
    });
    lastCount += 1;
};

document.addEventListener('DOMContentLoaded', function () {
    const filterGroupsEl = document.getElementById('filter-groups-data');
    if (filterGroupsEl) {
        new AdminFilters(
            '#filter_form',
            '.field-filters',
            JSON.parse(filterGroupsEl.textContent),
            JSON.parse(document.getElementById('active-filters-data').textContent)
        );
    }
});

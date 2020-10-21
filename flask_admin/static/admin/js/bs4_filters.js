var AdminFilters = function(element, filtersElement, filterGroups, activeFilters) {
    var $root = $(element);
    var $container = $('.filters', $root);
    var lastCount = 0;

    function getCount(name) {
        var idx = name.indexOf('_');

        if (idx === -1) {
            return 0;
        }

        return parseInt(name.substr(3, idx - 3), 10);
    }

    function makeName(name) {
        var result = 'flt' + lastCount + '_' + name;
        lastCount += 1;
        return result;
    }

    function removeFilter() {
        $(this).closest('tr').remove();
        if($('.filters tr').length == 0) {
            $('button', $root).hide();
            $('a[class=btn]', $root).hide();
            $('.filters tbody').remove();
        } else {
            $('button', $root).show();
        }

        return false;
    }

    // triggered when the filter operation (equals, not equals, etc) is changed
    function changeOperation(subfilters, $el, filter, $select) {
        // get the filter_group subfilter based on the index of the selected option
        var selectedFilter = subfilters[$select.select2('data').element[0].index];
        var $inputContainer = $el.find('td').last();

        // recreate and style the input field (turn into date range or select2 if necessary)
        var $field = createFilterInput($inputContainer, null, selectedFilter);
        styleFilterInput(selectedFilter, $field);

        $('button', $root).show();
    }

    // generate HTML for filter input - allows changing filter input type to one with options or tags
    function createFilterInput(inputContainer, filterValue, filter) {
        if (filter.type == "select2-tags") {
            var $field = $('<input type="hidden" class="filter-val form-control" />').attr('name', makeName(filter.arg));
            $field.val(filterValue);
        } else if (filter.options) {
            var $field = $('<select class="filter-val" />').attr('name', makeName(filter.arg));

            $(filter.options).each(function() {
                // for active filter inputs with options, add "selected" if there is a matching active filter
                if (filterValue && (filterValue == this[0])) {
                    $field.append($('<option/>')
                        .val(this[0]).text(this[1]).attr('selected', true));
                } else {
                    $field.append($('<option/>')
                        .val(this[0]).text(this[1]));
                }
            });
        } else {
            var $field = $('<input type="text" class="filter-val form-control" />').attr('name', makeName(filter.arg));
            $field.val(filterValue);
        }
        inputContainer.replaceWith($('<td/>').append($field));

        return $field;
    }

    // add styling to input field, accommodates filters that change the input field's HTML
    function styleFilterInput(filter, field) {
        if (filter.type) {
            if ((filter.type == "datepicker") || (filter.type == "daterangepicker")) {
                field.attr('data-date-format', "YYYY-MM-DD");
            } else if ((filter.type == "datetimepicker") || (filter.type == "datetimerangepicker")) {
                field.attr('data-date-format', "YYYY-MM-DD HH:mm:ss");
            } else if ((filter.type == "timepicker")  || (filter.type == "timerangepicker")) {
                field.attr('data-date-format', "HH:mm:ss");
            } else if (filter.type == "select2-tags") {
                var options = [];
                if (filter.options) {
                    filter.options.forEach(function(option) {
                        options.push({id:option[0], text:option[1]});
                    });
                    // save tag options as json on data attribute
                    field.attr('data-tags', JSON.stringify(options));
                }
            }
            faForm.applyStyle(field, filter.type);
        } else if (filter.options) {
            filter.type = "select2";
            faForm.applyStyle(field, filter.type);
        }

        return field;
    }

    function addFilter(name, subfilters, selectedIndex, filterValue) {
        var $el = $('<tr class="form-horizontal" />').appendTo($container);

        // Filter list
        $el.append(
            $('<td/>').append(
                $('<a href="#" class="btn btn-secondary remove-filter" />')
                    .append($('<span class="close-icon">&times;</span>'))
                    .append('&nbsp;')
                    .append(name)
                    .click(removeFilter)
                )
        );

        // Filter operation <select> (equal, not equal, etc)
        var $select = $('<select class="filter-op" />');

        // if one of the subfilters are selected, use that subfilter to create the input field
        var filterSelection = 0;
        $.each(subfilters, function( subfilterIndex, subfilter ) {
            if (this.index == selectedIndex) {
                $select.append($('<option/>').attr('value', subfilter.arg).attr('selected', true).text(subfilter.operation));
                filterSelection = subfilterIndex;
            } else {
                $select.append($('<option/>').attr('value', subfilter.arg).text(subfilter.operation));
            }
        });

        $el.append(
            $('<td/>').append($select)
        );

        // select2 for filter-op (equal, not equal, etc)
        $select.select2({width: 'resolve'}).on("change", function(e) {
            changeOperation(subfilters, $el, filter, $select);
        });

        // get filter option from filter_group, only for new filter creation
        var filter = subfilters[filterSelection];
        var $inputContainer = $('<td/>').appendTo($el);

        var $newFilterField = createFilterInput($inputContainer, filterValue, filter).focus();
        var $styledFilterField = styleFilterInput(filter, $newFilterField);

        return $styledFilterField;
    }

    // Add Filter Button, new filter
    $('a.filter', filtersElement).click(function() {
        var name = ($(this).text().trim !== undefined ? $(this).text().trim() : $(this).text().replace(/^\s+|\s+$/g,''));

        addFilter(name, filterGroups[name], false, null);

        $('button', $root).show();
    });

    // on page load - add active filters
    $.each(activeFilters, function( activeIndex, activeFilter ) {
        var idx = activeFilter[0],
            name = activeFilter[1],
            filterValue = activeFilter[2];
        var $activeField = addFilter(name, filterGroups[name], idx, filterValue);
    });

    // show "Apply Filter" button when filter input is changed
    $('.filter-val', $root).on('input change', function() {
        $('button', $root).show();
    });

    $('.remove-filter', $root).click(removeFilter);

    $('.filter-val', $root).not('.select2-container').each(function() {
        var count = getCount($(this).attr('name'));
        if (count > lastCount)
            lastCount = count;
    });

    lastCount += 1;
};

(function($) {
    $('[data-role=tooltip]').tooltip({
        html: true,
        placement: 'bottom'
    });
    if ($('#filter-groups-data').length == 1) {
        var filter = new AdminFilters(
            '#filter_form', '.field-filters',
            JSON.parse($('#filter-groups-data').text()),
            JSON.parse($('#active-filters-data').text())
        );
    }
})(jQuery);

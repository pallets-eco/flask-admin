var AdminFilters = function(element, filtersElement, filterGroups, activeFilters) {
    var $root = $(element);
    var $container = $('.filters', $root);
    var lastCount = 0;

    function updateActionVisibility() {
        if ($container.find('.filter-item').length === 0) {
            $('button', $root).addClass('d-none');
        } else {
            $('button', $root).removeClass('d-none');
        }
    }

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
        $(this).closest('.filter-item').remove();
        updateActionVisibility();
        return false;
    }

    function changeOperation(subfilters, $el, $select) {
        var selectData = $select.select2('data');
        var selectedIndex = selectData.length ? selectData[0].element[0].index : 0;
        var selectedFilter = subfilters[selectedIndex];
        var $inputContainer = $el.find('.filter-field').first();

        var $field = createFilterInput($inputContainer, null, selectedFilter);
        styleFilterInput(selectedFilter, $field);

        $('button', $root).removeClass('d-none');
    }

    function createFilterInput(inputContainer, filterValue, filter) {
        inputContainer.empty();
        var $field;

        if (filter.type == "select2-tags") {
            $field = $('<input type="hidden" class="filter-val form-control" />').attr('name', makeName(filter.arg));
            $field.val(filterValue);
        } else if (filter.options) {
            $field = $('<select class="filter-val form-control" />').attr('name', makeName(filter.arg));

            $(filter.options).each(function() {
                if (filterValue && (filterValue == this[0])) {
                    $field.append($('<option/>')
                        .val(this[0]).text(this[1]).attr('selected', true));
                } else {
                    $field.append($('<option/>')
                        .val(this[0]).text(this[1]));
                }
            });
        } else {
            $field = $('<input type="text" class="filter-val form-control" />').attr('name', makeName(filter.arg));
            $field.val(filterValue);
        }

        inputContainer.append($field);

        $field.on('input change', function() {
            $('button', $root).removeClass('d-none');
        });

        return $field;
    }

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
        var $el = $('<div class="filter-item form-horizontal" />').appendTo($container);

        var $labelWrapper = $('<div class="filter-label" />').appendTo($el);
        var $labelLink = $('<a href="#" class="btn btn-secondary remove-filter" />')
            .append($('<span class="close-icon">&times;</span>'))
            .append('&nbsp;')
            .append(name)
        $labelWrapper.append($labelLink);

        var $opContainer = $('<div class="filter-operation" />').appendTo($el);
        var $select = $('<select class="filter-op form-control" />').appendTo($opContainer);

        var filterSelection = 0;
        $.each(subfilters, function(subfilterIndex, subfilter) {
            if (this.index == selectedIndex) {
                $select.append($('<option/>').attr('value', subfilter.arg).attr('selected', true).text(subfilter.operation));
                filterSelection = subfilterIndex;
            } else {
                $select.append($('<option/>').attr('value', subfilter.arg).text(subfilter.operation));
            }
        });

        $select.select2({width: 'resolve'}).on("change", function() {
            changeOperation(subfilters, $el, $select);
        });

        var filter = subfilters[filterSelection];
        var $fieldContainer = $('<div class="filter-field" />').appendTo($el);
        var $newFilterField = createFilterInput($fieldContainer, filterValue, filter).focus();
        styleFilterInput(filter, $newFilterField);

        updateActionVisibility();

        return $newFilterField;
    }

    $('a.filter', filtersElement).click(function() {
        var name = ($(this).text().trim !== undefined ? $(this).text().trim() : $(this).text().replace(/^\s+|\s+$/g,''));

        addFilter(name, filterGroups[name], false, null);

        $('button', $root).removeClass('d-none');

        return false;
    });

    $.each(activeFilters, function(activeIndex, activeFilter) {
        var idx = activeFilter[0],
            name = activeFilter[1],
            filterValue = activeFilter[2];
        addFilter(name, filterGroups[name], idx, filterValue);
    });

    updateActionVisibility();

    $('.filter-val', $root).on('input change', function() {
        $('button', $root).removeClass('d-none');
    });

    $container.on('click', '.remove-filter', removeFilter);

    $('.filter-val', $root).not('.select2-container').each(function() {
        var count = getCount($(this).attr('name'));
        if (count > lastCount) {
            lastCount = count;
        }
    });

    lastCount += 1;
};

(function($) {
    $('[data-role=tooltip]').tooltip({
        html: true,
        placement: 'bottom'
    });
    $(document).on('adminFormReady', function(evt){
        if ($('#filter-groups-data').length == 1) {
            var filter = new AdminFilters(
                '#filter_form', '.field-filters',
                JSON.parse($('#filter-groups-data').text()),
                JSON.parse($('#active-filters-data').text())
            );
        }
    });
})(jQuery);

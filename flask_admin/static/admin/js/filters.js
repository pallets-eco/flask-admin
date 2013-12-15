var AdminFilters = function(element, filters_element, operations, options, types) {
    var $root = $(element);
    var $container = $('.filters', $root);
    var lastCount = 0;

    function getCount(name) {
        var idx = name.indexOf('_');
        return parseInt(name.substr(3, idx - 3));
    }

    function changeOperation() {
        var $row = $(this).closest('tr');
        var $el = $('.filter-val:input', $row);
        console.log($el);
        var count = getCount($el.attr('name'));
        $el.attr('name', 'flt' + count + '_' + $(this).val());
        $('button', $root).show();
    }

    function removeFilter() {
        $(this).closest('tr').remove();
        $('button', $root).show();

        return false;
    }

    function addFilter(name, op) {
        var $el = $('<tr />').appendTo($container);

        // Filter list
        $el.append(
                $('<td/>').append(
                    $('<a href="#" class="btn remove-filter" />')
                        .append($('<span class="close-icon">&times;</span>'))
                        .append('&nbsp;')
                        .append(name)
                        .click(removeFilter)
                    )
            );

        // Filter type
        var $select = $('<select class="filter-op" />')
                      .change(changeOperation);

        $(op).each(function() {
            $select.append($('<option/>').attr('value', this[0]).text(this[1]));
        });

        $el.append(
                $('<td/>').append($select)
            );

        $select.select2({width: 'resolve'});

        // Input
        var optId = op[0][0];

        var $field;

        if (optId in options) {
            $field = $('<select class="filter-val" />')
                        .attr('name', 'flt' + lastCount + '_' + optId);

            $(options[optId]).each(function() {
                $field.append($('<option/>')
                    .val(this[0]).text(this[1]));
            });

            $el.append($('<td/>').append($field));
            $field.select2({width: 'resolve'});
        } else
        {
            $field = $('<input type="text" class="filter-val" />')
                        .attr('name', 'flt' + lastCount + '_' + optId);
            $el.append($('<td/>').append($field));
        }

        if (optId in types) {
            $field.attr('data-role', types[optId]);
            faForm.applyStyle($field, types[optId]);
        }

        lastCount += 1;
    }

    $('a.filter', filters_element).click(function() {
        var name = $(this).text().trim();

        addFilter(name, operations[name]);

        $('button', $root).show();

        //return false;
    });

    $('.filter-op', $root).change(changeOperation);
    $('.filter-val', $root).change(function() {
        $('button', $root).show();
    });
    $('.remove-filter', $root).click(removeFilter);

    $('.filter-val', $root).each(function() {
        var count = getCount($(this).attr('name'));
        if (count > lastCount)
            lastCount = count;
    });

    lastCount += 1;
};

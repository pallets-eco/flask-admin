var AdminFilters = function(element, filters_element, operations, options, types) {
    var $root = $(element);
    var $container = $('.filters', $root);
    var lastCount = 0;

    function getCount(name) {
        var idx = name.indexOf('_');
        return parseInt(name.substr(3, idx - 3));
    }

    function changeOperation() {
        var $parent = $(this).parent();
        var $el = $('.filter-val', $parent);
        var count = getCount($el.attr('name'));
        $el.attr('name', 'flt' + count + '_' + $(this).val());
        $('button', $root).show();
    }

    function removeFilter() {
        $(this).parent().remove();
        $('button', $root).show();

        return false;
    }

    function addFilter(name, op) {
        var $el = $('<div class="filter-row" />').appendTo($container);

        $('<a href="#" class="btn remove-filter" />')
                .append($('<span class="close-icon">&times;</span>'))
                .append('&nbsp;')
                .append(name)
                .appendTo($el)
                .click(removeFilter);

        var $select = $('<select class="filter-op" />')
                      .appendTo($el)
                      .change(changeOperation);

        $(op).each(function() {
            $select.append($('<option/>').attr('value', this[0]).text(this[1]));
        });

        $select.select2({width: 'resolve'});

        var optId = op[0][0];

        var $field;

        if (optId in options) {
            $field = $('<select class="filter-val" />')
                        .attr('name', 'flt' + lastCount + '_' + optId)
                        .appendTo($el);

            $(options[optId]).each(function() {
                $field.append($('<option/>')
                    .val(this[0]).text(this[1]))
                    .appendTo($el);
            });

            $field.select2();
        } else
        {
            $field = $('<input type="text" class="filter-val" />')
                        .attr('name', 'flt' + lastCount + '_' + optId)
                        .appendTo($el);
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

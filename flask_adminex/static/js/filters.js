var Filters = function(element, operations, options, types) {
    var $root = $(element)
    var $container = $('#filters');
    var count = $('#filters>div', $root).length;

    function appendValueControl(element, id, optionId) {
        var field;

        // Conditionally generate select or textbox
        if (optionId in options) {
            field = $('<select class="filter-val" />').attr('name', 'flt' + id + 'v');
            $(options[optionId]).each(function() {
                field.append($('<option/>').val(this[0]).text(this[1]));
            });
        } else
        {
            field = $('<input type="text" class="filter-val" />').attr('name', 'flt' + id + 'v');
        }

        $(element).append(field);

        if (optionId in options)
            field.chosen();

        if (optionId in types) {
            field.attr('data-role', types[optionId]);
            adminForm.applyStyle(field, types[optionId]);
        }
    }

    function addFilter() {
        var node = $('<div class="filter-row" />').attr('id', 'fltdiv' + count).appendTo($container);

        $('<a href="#" class="remove-filter" />')
            .append('<i class="icon-remove"/>')
            .click(removeFilter)
            .appendTo(node);

        var operation = $('<select class="filter-op" />')
                .attr('name', 'flt' + count)
                .change(changeOperation)
                .appendTo(node);

        var index = 0;
        $(operations).each(function() {
            operation.append($('<option/>').val(index).text(this.toString()));
            index++;
        });
        operation.chosen();

        appendValueControl(node, count, 0);

        count += 1;

        $('button', $root).show();

        return false;
    }

    function removeFilter() {
        var row = $(this).parent();
        var idx = parseInt(row.attr('id').substr(6));

        // Remove row
        row.remove();

        // Renumber any rows that are after
        for (var i = idx + 1; i < count; ++i) {
            row = $('#fltdiv' + i);
            row.attr('id', 'fltdiv' + (i - 1));

            $('.filter-op', row).attr('name', 'flt' + (i - 1));
            $('.filter-val', row).attr('name', 'flt' + (i - 1) + 'v');
        }

        count -= 1;

        $('button', $root).show();

        return false;
    }

    function changeOperation() {
        var row = $(this).parent();
        var rowIdx = parseInt(row.attr('id').substr(6));

        // Get old value field
        var oldValue = $('.filter-val', row);
        var oldValueId = oldValue.attr('id');

        // Delete old value
        oldValue.remove();
        if (oldValueId != null)
            $('div#' + oldValueId + '_chzn', row).remove();

        var optId = $(this).val();
        appendValueControl(row, rowIdx, optId);

        $('button', $root).show();
    };

    $('#add_filter', $root).click(addFilter);
    $('.remove-filter', $root).click(removeFilter);
    $('.filter-op').change(changeOperation);
    $('.filter-val').change(function() {
        $('button', $root).show();
    });
};

(function() {
    var AdminForm = function() {
      this.applyStyle = function(el, name) {
        switch (name) {
            case 'select2':
                $(el).select2({width: 'resolve'});
                break;
            case 'select2blank':
                $(el).select2({allowClear: true, width: 'resolve'});
                break;
            case 'select2tags':
                $(el).select2({tags: [], tokenSeparators: [','], width: 'resolve'});
                break;
            case 'datepicker':
                $(el).datepicker();
                break;
            case 'datetimepicker':
                $(el).datepicker({displayTime: true});
                break;
        }
      };

      this.addInlineField = function(id, el, template) {
        var $el = $(el);
        var $template = $(template);

        // Figure out new field ID
        var lastField = $el.children('.fa-inline-field').last();

        var prefix = id + '-0';
        if (lastField.length > 0) {
            var parts = $(lastField[0]).attr('id').split('-');
            idx = parseInt(parts[parts.length - 1]) + 1;
            prefix = id + '-' + idx;
        }

        // Set form ID
        $template.attr('id', prefix);

        // Fix form IDs
        $('[name]', $template).each(function(e) {
            var me = $(this);

            var id = me.attr('id');
            var name = me.attr('name');

            id = prefix + (id !== '' ? '-' + id : '');
            name = prefix + (name !== '' ? '-' + name : '');

            me.attr('id', id);
            me.attr('name', name);
        });

        $template.appendTo($el);

        // Select first field
        $('input:first', $template).focus();

        // Apply styles
        this.applyGlobalStyles($template);
      };

      this.applyGlobalStyles = function(parent) {
        $('[data-role=select2]', parent).select2({width: 'resolve'});
        $('[data-role=select2blank]', parent).select2({allowClear: true, width: 'resolve'});
        $('[data-role=select2tags]', parent).select2({tags: [], tokenSeparators: [','], width: 'resolve'});
        $('[data-role=datepicker]', parent).datepicker();
        $('[data-role=datetimepicker]', parent).datepicker({displayTime: true});
      };
    };

    // Add live event handler
    $('.fa-remove-field').live('click', function(e) {
        e.preventDefault();

        var form = $(this).closest('.fa-inline-field');
        form.remove();
    });

    // Expose faForm globally
    var faForm = window.faForm = new AdminForm();

    // Apply global styles
    faForm.applyGlobalStyles(document);
})();

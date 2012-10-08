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
            case 'datepicker':
                $(el).datepicker();
                break;
            case 'datetimepicker':
                $(el).datepicker({displayTime: true});
                break;
        }
      };

      this.addInlineModel = function(id, el, template) {
        var $el = $(el);
        var $template = $(template);

        // Figure out new form ID
        var lastForm = $el.children('.fa-inline-form').last();

        var prefix = id + '-0';
        if (lastForm.length > 0) {
            var parts = $(lastForm[0]).attr('id').split('-');
            idx = parseInt(parts[parts.length - 1]) + 1;
            prefix = id + '-' + idx;
        }

        // Set form ID
        $template.attr('id', prefix);

        // Fix form IDs
        $('[name]', $template).each(function(e) {
            var me = $(this);

            me.attr('id', prefix + '-' + me.attr('id'));
            me.attr('name', prefix + '-' + me.attr('name'));
        });

        $template.appendTo($el);

        // Apply styles
        this.applyGlobalStyles($template);
      };

      this.applyGlobalStyles = function(parent) {
        $('[data-role=select2]', parent).select2({width: 'resolve'});
        $('[data-role=select2blank]', parent).select2({allowClear: true, width: 'resolve'});
        $('[data-role=datepicker]', parent).datepicker();
        $('[data-role=datetimepicker]', parent).datepicker({displayTime: true});
      };
    };

    // Add live event handler
    $('.fa-remove-form').live('click', function(e) {
        e.preventDefault();

        var form = $(this).closest('.fa-inline-form');
        form.remove();
    });

    // Expose faForm globally
    var faForm = window.faForm = new AdminForm();

    // Apply global styles
    faForm.applyGlobalStyles(document);
})();

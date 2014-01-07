(function() {
    var AdminForm = function() {
      // Field converters
      var fieldConverters = [];

      /**
      * Process AJAX fk-widget
      */
      function processAjaxWidget($el, name) {
        var multiple = $el.attr('data-multiple') == '1';

        var opts = {
          width: 'resolve',
          minimumInputLength: 1,
          placeholder: 'data-placeholder',
          ajax: {
            url: $el.attr('data-url'),
            data: function(term, page) {
              return {
                query: term,
                offset: (page - 1) * 10,
                limit: 10
              };
            },
            results: function(data, page) {
              var results = [];

              for (var k in data) {
                var v = data[k];

                results.push({id: v[0], text: v[1]});
              }

              return {
                results: results,
                more: results.length == 10
              };
            }
          },
          initSelection: function(element, callback) {
            $el = $(element);
            var value = jQuery.parseJSON($el.attr('data-json'));
            var result = null;

            if (value) {
              if (multiple) {
                result = [];

                for (var k in value) {
                  var v = value[k];
                  result.push({id: v[0], text: v[1]});
                }

                callback(result);
              } else {
                result = {id: value[0], text: value[1]};
              }
            }

            callback(result);
          }
        };

        if ($el.attr('data-allow-blank'))
          opts['allowClear'] = true;

        opts['multiple'] = multiple;

        $el.select2(opts);
      }

      /**
      * Process data-role attribute for the given input element. Feel free to override
      *
      * @param {Selector} $el jQuery selector
      * @param {String} name data-role value
      */
      this.applyStyle = function($el, name) {
        // Process converters first
        for (var conv in fieldConverters) {
            var fieldConv = fieldConverters[conv];

            if (fieldConv($el, name))
                return true;
        }

        switch (name) {
            case 'select2':
                var opts = {
                    width: 'resolve'
                };

                if ($el.attr('data-allow-blank'))
                    opts['allowClear'] = true;

                if ($el.attr('data-tags')) {
                    $.extend(opts, {
                        tokenSeparators: [','],
                        tags: []
                    });
                }

                $el.select2(opts);
                return true;
            case 'select2-ajax':
                processAjaxWidget($el, name);
                return true;
            case 'datepicker':
                $el.datetimepicker({
                  minView: 'month'
                });
                return true;
            case 'datetimepicker':
                $el.datetimepicker();
                return true;
            case 'timepicker':
                $el.datetimepicker({
                  startView: 'day',
                  maxView: 'day',
                  formatViewType: 'time'
                });
                return true;
        }
      };

      /**
      * Add inline form field
      *
      * @method addInlineField
      * @param {Node} el Button DOM node
      * @param {String} elID Form ID
      */
      this.addInlineField = function(el, elID) {
        // Get current inline field
        var $el = $(el).closest('.inline-field');
        // Figure out new field ID
        var id = elID;

        var $parentForm = $el.parent().closest('.inline-field');

        if ($parentForm.length > 0) {
          id = $parentForm.attr('id') + '-' + elID;
        }

        var $fieldList = $el.find('> .inline-field-list');
        var $lastField = $fieldList.children('.inline-field').last();

        var prefix = id + '-0';
        if ($lastField.length > 0) {
            var parts = $lastField.attr('id').split('-');
            idx = parseInt(parts[parts.length - 1], 10) + 1;
            prefix = id + '-' + idx;
        }

        // Get tempalate
        var $template = $($el.find('> .inline-field-template').text());

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

        $template.appendTo($fieldList);

        // Select first field
        $('input:first', $template).focus();

        // Apply styles
        this.applyGlobalStyles($template);
      };

      /**
      * Apply global input styles.
      *
      * @method applyGlobalStyles
      * @param {Selector} jQuery element
      */
      this.applyGlobalStyles = function(parent) {
        var self = this;

        $('[data-role]', parent).each(function() {
            var $el = $(this);
            self.applyStyle($el, $el.attr('data-role'));
        });
      };

      /**
      * Add a field converter for customizing styles
      *
      * @method addFieldConverter
      * @param {converter} function($el, name)
      */
      this.addFieldConverter = function(converter) {
          fieldConverters.push(converter);
      };
    };

    // Add on event handler
    $('body').on('click', '.inline-remove-field' , function(e) {
        e.preventDefault();

        var form = $(this).closest('.inline-field');
        form.remove();
    });

    // Expose faForm globally
    var faForm = window.faForm = new AdminForm();

    // Apply global styles for current page after page loaded
    $(function() {
        faForm.applyGlobalStyles(document);
    });
})();

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
            var value = jQuery.parseJSON(element.val());
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
            var fildConv = fieldConverters[conv];

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
                        multiple: true,
                        tokenSeparators: [',']
                    });
                }

                $el.select2(opts);
                return true;
            case 'select2-ajax':
                processAjaxWidget($el, name);
                return true;
            case 'datepicker':
                $el.datepicker();
                return true;
            case 'datetimepicker':
                $el.datepicker({displayTime: true});
                return true;
        }
      };

      /**
      * Add inline form field
      *
      * @method addInlineField
      * @param {String} id Form ID
      * @param {Node} el Form element
      * @param {String} template Form template
      */
      this.addInlineField = function(id, el, template) {
        var $el = $(el);
        var $template = $($(template).text());

        // Figure out new field ID
        var lastField = $el.children('.fa-inline-field').last();

        var prefix = id + '-0';
        if (lastField.length > 0) {
            var parts = $(lastField[0]).attr('id').split('-');
            idx = parseInt(parts[parts.length - 1], 10) + 1;
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
    };

    // Add live event handler
    $('.fa-remove-field').live('click', function(e) {
        e.preventDefault();

        var form = $(this).closest('.fa-inline-field');
        form.remove();
    });

    // Expose faForm globally
    var faForm = window.faForm = new AdminForm();

    // Apply global styles for current page after page loaded
    $(function() {
        faForm.applyGlobalStyles(document);
    });
})();

/* ---------------------------------------------------------------
 *  Fomantic-UI form helpers for Flask-Admin
 *  Legacy code + changes
 *  ------------------------------------------------------------- */
(function () {

  /* =================================================================
   *  AdminForm
   * ================================================================= */
  var AdminForm = function () {

    /* ---------- Field-converter extension hook ------------------- */
    var fieldConverters = [];

    this.addFieldConverter = function (fn) {
      fieldConverters.push(fn);
    };

    /* --------------------------------------------------------------
     *  applyStyle($el, role)
     *  Called for every element with a “data-role” attribute
     * ------------------------------------------------------------ */
    this.applyStyle = function ($el, role, need_transform = false) {

      /* 1. Let external converters claim it first */
      for (var i = 0; i < fieldConverters.length; i++) {
        if (fieldConverters[i]($el, role) === true) {
          return true;
        }
      }

      /*
        @TODO:  Add new or change fields in: flask_admin\form\widgets.py
                that corresponds with FomanticUI components

        ! Due to the backend implementation, some rendered fields must
        be manipulated/formatted via DOM.
      */

      /* --------------------------------------------------------------
       *  Element Transformation - Convert basic HTML to FomanticUI structure
       * ------------------------------------------------------------ */
      function transformElement($el, role) {
        if ($el.is('input[type="checkbox"]')) {
          role = 'checkbox';
        }

        switch (role) {
          case 'select2':
            $el.addClass('search');
            break;

          case 'checkbox':
            var $label = $el.parent().find('label');
            $label.html($('<b/>').append($label.text()));
            var checkboxWrapper = $('<div class="ui toggle right aligned fluid checkbox"></div>');
            var segmentWrapper = $('<div class="ui segment"></div>');
            $el.wrap(checkboxWrapper);
            $el.parent().wrap(segmentWrapper);
            $label.appendTo($el.parent());
            $el.parent().checkbox();
            break;

          case 'datetimepicker':
          case 'datepicker':
          case 'timepicker':
            var calendarWrapper = $('<div class="ui calendar"></div>');
            calendarWrapper.attr('data-date-format', $el.data('date-format'))
            var inputWrapper = $('<div class="ui fluid input left icon"></div>');
            var icon = role === 'timepicker' ? $('<i class="time icon"></i>') : $('<i class="calendar icon"></i>');
            $el.wrap(inputWrapper);
            $el.parent().append(icon);
            $el.parent().wrap(calendarWrapper);
            $el = $el.parent().parent();
            break;

          case 'file-upload':
            if (originalEl.type === 'file' && !parent.hasClass('ui file input')) {
              var wrapper = $('<div class="ui file input"></div>');
              $el.wrap(wrapper);
              return { el: $el.parent(), role: role };
            }
            break;
        }

        return { el: $el, role: role }; // Return element and role
      }

      if (need_transform) {
        // Transform the element before styling
        var result = transformElement($el, role);
        $el = result.el;
        role = result.role;
      }

      /* 2. Native handlers */
      switch (role) {
        /* --------------------- DROPDOWNS ------------------------- */
        case 'select2':
        case 'select2-tags':            // legacy alias
          $el.dropdown();
          return true;

        case 'select2-tags-freeform':
          $el.dropdown({
            fullTextSearch: true,
            allowAdditions: true,
            hideAdditions: false,
            forceSelection: false,
            placeholder: 'Add options: tag1, tag2, ...',
          });
          return true;

        /* --------------------- DATE / TIME ----------------------- */
        /* Assumes Fomantic-UI Calendar plugin */
        case 'datepicker':
          $el.calendar({
            type: 'date',
            context: 'body',
            formatter: {
              date: $el.data('date-format') || 'YYYY-MM-DD'
            }
          });
          return true;

        case 'datetimepicker':
          $el.calendar({
            type: 'datetime',
            context: 'body',
            formatter: {
              datetime: $el.data('date-format') || 'YYYY-MM-DD HH:mm:ss'
            }
          });
          return true;

        case 'timepicker':
          $el.calendar({
            type: 'time',
            context: 'body',
            formatter: {
              time: $el.data('date-format') || 'HH:mm:ss'
            }
          });
          return true;

        /* --------------------- LEAFLET MAP ----------------------- */
        case 'leaflet':
          /* falls back to the existing helper from the BS4 file.
             If you don’t need maps, just delete this case. */
          if (typeof processLeafletWidget === 'function') {
            processLeafletWidget($el, role);
          }
          return true;
      }

      /* Nothing claimed the element */
      return false;
    }; /* applyStyle */


    /**
      * Add inline form field
      *
      * @method addInlineField
      * @param {Node} el Button DOM node
      * @param {String} elID Form ID
      */
    this.addInlineField = function (el, elID) {
      // Get current inline field
      var $el = $(el).closest('.inline-field');
      // Figure out new field ID
      var id = elID;

      var $parentForm = $el.parent().closest('.inline-field');

      if ($parentForm.hasClass('fresh')) {
        id = $parentForm.attr('id');
        if (elID) {
          id += '-' + elID;
        }
      }

      var $fieldList = $el.find('> .inline-field-list');
      var maxId = 0;

      $fieldList.children('.inline-field').each(function (idx, field) {
        var $field = $(field);

        var parts = $field.attr('id').split('-');
        idx = parseInt(parts[parts.length - 1], 10) + 1;

        if (idx > maxId) {
          maxId = idx;
        }
      });

      var prefix = id + '-' + maxId;

      // Get template
      var $template = $($el.find('> .inline-field-template').text());

      // Set form ID
      $template.attr('id', prefix);

      // Mark form that we just created
      $template.addClass('fresh');

      // Fix form IDs
      $('[name]', $template).each(function (e) {
        var me = $(this);

        var id = me.attr('id');
        var name = me.attr('name');

        id = prefix + (id !== '' ? '-' + id : '');
        name = prefix + (name !== '' ? '-' + name : '');

        me.attr('id', id);
        me.attr('name', name);
      });

      $template.accordion();
      $template.appendTo($fieldList);

      // Select first field
      $('input:first', $template).focus();

      // Apply styles
      this.applyGlobalStyles($template);
    };

    /* --------------------------------------------------------------
     *  applyGlobalStyles(parent)
     *  Scan a DOM subtree & style everything with data-role
     * ------------------------------------------------------------ */
    this.applyGlobalStyles = function (parent) {
      var self = this;
      $(':input[data-role], a[data-role], .field > input[type="checkbox"]', parent).each(function () {
        var $el = $(this);
        self.applyStyle($el, $el.attr('data-role'), true);
      });
    };

  }; /* AdminForm */

  /* =================================================================
   *  Inline-form “−” button (unchanged from original)
   * ================================================================= */
  $('body').on('click', '.inline-remove-field', function (e) {
    e.preventDefault();
    var confirmed = confirm($('.inline-remove-field').attr('value'));
    if (confirmed) {
      $(this).closest('.inline-field').remove();
    }
  });

  /* =================================================================
   *  Expose globally & fire adminFormReady
   * ================================================================= */
  var faForm = window.faForm = new AdminForm();
  $(document).trigger('adminFormReady');

  /* Style everything that’s already on the page */
  $(function () {
    faForm.applyGlobalStyles(document);
  });

})();

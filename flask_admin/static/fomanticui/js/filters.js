/*  Fomantic-UI admin list filters
 *  --------------------------------------------------------------
 *  This replaces the old Select2-based implementation with native
 *  Fomantic-UI dropdowns + the existing Flask-Admin form helpers.
 *  -------------------------------------------------------------- */
var AdminFilters = function (element, filtersElement, filtersFormElement, filterGroups, activeFilters) {
  var $root = $(element);
  var $container = $('.filters', $root);
  var $filtersFormElement = $(filtersFormElement);

  var lastCount = 0;

  /* ------------------------------------------------------------
   *  Helpers
   * ---------------------------------------------------------- */
  function getCount(name) {
    var idx = name.indexOf('_');
    if (idx === -1) { return 0; }
    return parseInt(name.substr(3, idx - 3), 10);
  }

  function makeName(arg) {
    var name = 'flt' + lastCount + '_' + arg;
    lastCount += 1;
    return name;
  }

  function updateFiltersCount() {
    $('.filters-count').text($('.filters > tr').length || '');
  }

  function isCalendar(type) {
    return [
      'datepicker', 'datetimepicker', 'timepicker',
      'daterangepicker', 'datetimerangepicker', 'timerangepicker'
    ].includes(type);
  }
  function isCalendarRange(type) {
    return [
      'daterangepicker', 'datetimerangepicker', 'timerangepicker'
    ].includes(type);
  }

  function ensureContainerExists() {
    if ($container.length === 0) {
      $container = $('<tbody class="filters ui form" />').appendTo($root);
    }
  }

  /* ------------------------------------------------------------
   *  Remove filter row
   * ---------------------------------------------------------- */
  function removeFilter() {
    $(this).closest('tr').remove();

    if ($('.filters >tr').length === 0) {
      $('#apply-filters-btn', $root).addClass('disabled');
      $('.filters').remove();               // remove empty tbody
      $container = $();                     // reset reference
    } else {
      $('#apply-filters-btn', $root).removeClass('disabled');
    }
    updateFiltersCount();
    return false;
  }

  /* ------------------------------------------------------------
   *  Build / style the value field
   * ---------------------------------------------------------- */
  function createFilterInput($td, filterValue, filter) {
    let $field;

    /* ---------- CALENDAR TYPES --------------------------------- */
    if (isCalendar(filter.type)) {
      /* single date / time input */
      if (!isCalendarRange(filter.type)) {
        const $input = $('<input type="text" class="filter-val" />')
          .attr('name', makeName(filter.arg))
          .val(filterValue || '');

        $field = $('<div class="ui fluid field calendar" />')
          .append(
            $('<div class="ui input left icon" />')
              .append('<i class="calendar icon"></i>')
              .append($input)
          );
      }
      /* ---------------- RANGE: start + end --------------------- */
      else {
        const name = makeName(filter.arg);
        const $hidden = $('<input type="hidden" class="filter-val" />')
          .attr('name', name)
          .val(filterValue || '');

        const $startInput = $('<input type="text" placeholder="Start" />');
        const $endInput = $('<input type="text" placeholder="End"  />');

        const [startValue, endValue] = (filterValue || '').split(' to ');
        $startInput.val(startValue || '');
        $endInput.val(endValue || '');

        const $startCal = $('<div class="ui calendar field range-start" />')
          .append($('<div class="ui input left icon"><i class="calendar icon"></i></div>')
            .append($startInput));
        const $endCal = $('<div class="ui calendar field range-end" />')
          .append($('<div class="ui input left icon"><i class="calendar icon"></i></div>')
            .append($endInput));

        // wrapper that faForm will receive
        $field = $('<div class="two fields m-0" />')
          .append(
            $('<div class="field" />').append($startCal)
          )
          .append(
            $('<div class="field" />').append($endCal)
          )
          .append($hidden);

        /* keep hidden input updated */
        function syncHidden() {
          const start = $startInput.val();
          const end = $endInput.val();
          $hidden.val(start && end ? `${start} to ${end}` : '');
        }
        $startInput.add($endInput).on('change input', syncHidden);
      }
    }

    /* Handle select2-tags type filters and filters with options */
    else if (filter.type === 'select2-tags' || filter.options) {
      /* Case 1: select2-tags type filter */
      if (filter.type === 'select2-tags') {
        // Parse selected values from comma-separated string
        let selectedValues = [];
        if (filterValue) {
          selectedValues = filterValue.split(',').map(function (s) { return s.trim(); });
        }

        // Create multi-select dropdown field
        $field = $('<select class="filter-val ui fluid search clearable dropdown" multiple />')
          .attr('name', makeName(filter.arg));

        // If filter has predefined options, add them to dropdown
        if (filter.options) {
          $(filter.options).each(function () {
            var opt = $('<option/>').val(this[0]).text(this[1]);
            if (selectedValues.includes(this[0])) { opt.attr('selected', true); }
            $field.append(opt);
          });
        }
        // Otherwise add selected values as options
        else {
          selectedValues.forEach(function (value) {
            var opt = $('<option/>').val(value).text(value);
            opt.attr('selected', true);
            $field.append(opt);
          });
        }

      }
      /* Case 2: Filter with predefined options but not select2-tags type */
      else if (filter.type != 'select2-tags' && filter.options) {
        // Create single-select dropdown field
        $field = $('<select class="filter-val ui fluid dropdown" />')
          .attr('name', makeName(filter.arg));

        // Add search capability for dropdowns with many options
        if (filter.options.length > 8) {
          $field.addClass('search');
        }

        // Add options to dropdown
        $(filter.options).each(function () {
          var opt = $('<option/>').val(this[0]).text(this[1]);
          if (filterValue && (filterValue === this[0])) { opt.attr('selected', true); }
          $field.append(opt);
        });
      }
    }

    /* Fallback: plain text input */
    else {
      $field = $('<input type="text" class="filter-val" />')
        .attr('name', makeName(filter.arg))
        .val(filterValue || '');
    }

    $td.replaceWith($('<td/>').append($field));

    // auto-show "Apply" button once value changes
    $field.on('input change', function () {
      $('#apply-filters-btn', $root).removeClass('disabled');
    });

    return $field;
  }

  function styleFilterInput(filter, $field) {

    /* ----- CALENDARS ------------------------------------------ */
    if (isCalendar(filter.type)) {
      const rangeToSingle = {
        'daterangepicker': 'datepicker',
        'datetimerangepicker': 'datetimepicker',
        'timerangepicker': 'timepicker'
      };
      /* range: initialise both calendars; single: just one */
      if (isCalendarRange(filter.type)) {

        const $start = $field.find('.range-start');
        const $end = $field.find('.range-end');

        faForm.applyStyle($start, rangeToSingle[filter.type]);
        faForm.applyStyle($end, rangeToSingle[filter.type]);

        /* link start & end */
        $start.calendar('setting', 'endCalendar', $end);
        $end.calendar('setting', 'startCalendar', $start);
      } else {
        faForm.applyStyle($field, filter.type);
      }
    }
    /* ----- SELECT WITH OPTIONS ------------------------------- */
    else if (!filter.options && filter.type === 'select2-tags') {
      faForm.applyStyle($field, 'select2-tags-freeform');
    }
    /* ----- SELECT WITH FREE OPTIONS ------------------------------- */
    else if (filter.options) {
      faForm.applyStyle($field, 'select2-tags');
    }
    return $field;
  }

  /* ------------------------------------------------------------
   *  Operation dropdown (equals / not equals / …) change handler
   * ---------------------------------------------------------- */
  function changeOperation(subfilters, $row, $select) {
    var selectedIndex = $select.prop('selectedIndex');
    var selectedFilter = subfilters[selectedIndex];
    var $inputCell = $row.find('td').last();

    var $field = createFilterInput($inputCell, null, selectedFilter);
    styleFilterInput(selectedFilter, $field);

    $('#apply-filters-btn', $root).removeClass('disabled');
  }

  /* ------------------------------------------------------------
   *  Add a new filter row
   * ---------------------------------------------------------- */
  function addFilter(name, subfilters, selectedIndex, filterValue) {
    ensureContainerExists();

    var $row = $('<tr/>').appendTo($container);

    /* Column label + remove button */
    $row.append(
      $('<td/>').append(
        $('<div class="ui icon compact labeled fluid button" />')
          .append($('<i class="trash red icon remove-filter" />').click(removeFilter))
          .append(document.createTextNode(name))
      )
    );

    /* Operation dropdown */
    var $select = $('<select class="filter-osp ui fluid dropdown" />');
    var filterSelection = 0;

    $.each(subfilters, function (idx, subfilter) {
      var $opt = $('<option/>')
        .val(subfilter.arg)
        .text(subfilter.operation);
      if (subfilter.index === selectedIndex) {
        $opt.attr('selected', true);
        filterSelection = idx;
      }
      $select.append($opt);
    });

    $row.append($('<td/>').append($select));
    $select.dropdown().on('change', function () {
      changeOperation(subfilters, $row, $select);
    });

    /* Value field */
    var chosenFilter = subfilters[filterSelection];
    var $inputCell = $('<td/>').appendTo($row);
    var $newValueField = createFilterInput($inputCell, filterValue, chosenFilter).focus();
    styleFilterInput(chosenFilter, $newValueField);

    updateFiltersCount();
    $('#apply-filters-btn', $root).removeClass('disabled');
    return $newValueField;
  }

  /* ------------------------------------------------------------
   *  "Add Filter" menu click
   * ---------------------------------------------------------- */
  $('.item.filter', filtersElement).on('click', function () {
    var text = $(this).find('span').text();
    var name = (text.trim !== undefined ? text.trim() : text.replace(/^\s+|\s+$/g, ''));
    addFilter(name, filterGroups[name], false, null);
  });

  /* ------------------------------------------------------------
   *  Restore active filters on page load
   * ---------------------------------------------------------- */
  if (activeFilters.length > 0) {
    $('#filters-table-container-toggle').click();  // open panel
  }
  $.each(activeFilters, function (_, active) {

    var idx = active[0],
      name = active[1],
      value = active[2];
    addFilter(name, filterGroups[name], idx, value);
    $("#apply-filters-btn").addClass("disabled");
  });

  /* ------------------------------------------------------------
   *  Apply-filters button collects inputs & submits form
   * ---------------------------------------------------------- */
  $('#apply-filters-btn').on('click', function () {
    var $tbody = $root.find('tbody');
    $filtersFormElement.find('input[type="hidden"][name^="flt"]').remove();

    $tbody.find('input, select').each(function () {
      var $input = $(this);
      var name = $input.attr('name');
      var value = $input.val();
      if (name && value) {
        $('<input>').attr({ type: 'hidden', name: name, value: value })
          .appendTo($filtersFormElement);
      }
    });
    $filtersFormElement.submit();
  });

  /* ------------------------------------------------------------ */
  lastCount += 1;
};

/* ==================================================================
 *  Bootstrapper
 * ================================================================== */
(function ($) {
  var $toggleBtn = $('#filters-table-container-toggle');

  function getFiltersCount() {
    return $('.filters > tr').length;
  }

  $toggleBtn.on('click', function () {
    var $container = $('#filters-table-container');
    var $label = $(this).find('span');

    $container.toggleClass('d-none');
    $(this).toggleClass('black');
    $label.text(getFiltersCount() || '');
  });

  /* Initialise when the admin form is ready */
  $(document).on('adminFormReady', function () {
    if ($('#filter-groups-data').length) {
      new AdminFilters(
        '#filters-table',
        '.field-filters',
        '#filter_form',
        JSON.parse($('#filter-groups-data').text()),
        JSON.parse($('#active-filters-data').text())
      );
    }
  });

  /* Trigger immediately for static pages */
  $(document).trigger('adminFormReady');
})(jQuery);

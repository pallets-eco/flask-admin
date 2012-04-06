/* ===========================================================
 * bootstrap-datepicker.js v1.3.0
 * http://twitter.github.com/bootstrap/javascript.html#datepicker
 * ===========================================================
 * Copyright 2011 Twitter, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * Contributed by Scott Torborg - github.com/storborg
 * Loosely based on jquery.date_input.js by Jon Leighton, heavily updated and
 * rewritten to match bootstrap javascript approach and add UI features.
 *
 * Enhancements and fixes by Serge S. Koval - github.com/mrjoes
 *
 * =========================================================== */


!function ( $ ) {

  var all = [];

  function clearDatePickers(except) {
    var ii;
    for(ii = 0; ii < all.length; ii++) {
      if(all[ii] != except) {
        all[ii].hide();
      }
    }
  }

  function DatePicker( element, options ) {
    this.$el = $(element);
    this.proxy('show').proxy('ahead').proxy('hide').proxy('keyHandler').proxy('selectDate');

    var options = $.extend({}, $.fn.datepicker.defaults, options );

    // If custom parse/format function was not passed in options and time-based display
    // is enabled, use time-compatible parse/format functions
    if (options.displayTime && !!!options.parse && !!!options.format) {
      options.parse = this.parseDateTime;
    }

    $.extend(this, options);
    this.$el.data('datepicker', this);
    all.push(this);
    this.init();
  }

  DatePicker.prototype = {
    init: function() {
        var $months = this.nav('months', 1);
        var $years = this.nav('years', 12);

        var $nav = $('<div>').addClass('nav').append($months, $years);

        this.$month = $('.name', $months);
        this.$year = $('.name', $years);

        $calendar = $("<div>").addClass('calendar');

        // Populate day of week headers, realigned by startOfWeek.
        for (var i = 0; i < this.shortDayNames.length; i++) {
          $calendar.append('<div class="dow">' + this.shortDayNames[(i + this.startOfWeek) % 7] + '</div>');
        };

        this.$days = $('<div>').addClass('days');
        $calendar.append(this.$days);

        this.$picker = $('<div>')
          .addClass('datepicker')
          .append($nav, $calendar)
          .insertAfter(this.$el);

        this.$picker.children()
          .click(function(e) { e.stopPropagation() })
          // Use this to prevent accidental text selection.
          .mousedown(function(e) { e.preventDefault() });

        if (this.displayTime) {
          this.$time = $('<div class="time">')
              .append('<label for="_time">Time</label>')
              .append('<input id="_time" type="text" />')
              .click(function(e) { e.stopPropagation(); });

          this.$picker.append(this.$time);
        }

        this.$el
          .focus(this.show)
          .click(this.show)
          .change($.proxy(function() { this.selectDate(); }, this));

        this.selectDate();
        this.hide();
      }

    , nav: function( c, months ) {
        var $subnav = $('<div>' +
                          '<span class="prev button">&larr;</span>' +
                          '<span class="name"></span>' +
                          '<span class="next button">&rarr;</span>' +
                        '</div>').addClass(c)
        $('.prev', $subnav).click($.proxy(function() { this.ahead(-months, 0) }, this));
        $('.next', $subnav).click($.proxy(function() { this.ahead(months, 0) }, this));
        return $subnav;

    }

    , updateName: function($area, s) {
        // Update either the month or year field, with a background flash
        // animation.
        var cur = $area.find('.fg').text(),
            $fg = $('<div>').addClass('fg').append(s);
        $area.empty();
        if(cur != s) {
          var $bg = $('<div>').addClass('bg');
          $area.append($bg, $fg);
          $bg.fadeOut('slow', function() {
            $(this).remove();
          });
        } else {
          $area.append($fg);
        }
    }

    , selectMonth: function(date) {
        this.displayedDate = date;

        var newMonth = new Date(date.getFullYear(), date.getMonth(), 1);

        if (!this.curMonth || !(this.curMonth.getFullYear() == newMonth.getFullYear() &&
                                this.curMonth.getMonth() == newMonth.getMonth())) {

          this.curMonth = newMonth;

          var rangeStart = this.rangeStart(date), rangeEnd = this.rangeEnd(date);
          var num_days = this.daysBetween(rangeStart, rangeEnd);
          this.$days.empty();

          for (var ii = 0; ii <= num_days; ii++) {
            var thisDay = new Date(rangeStart.getFullYear(), rangeStart.getMonth(), rangeStart.getDate() + ii, 12, 00);
            var $day = $('<div>').attr('date', this.format(thisDay));
            $day.text(thisDay.getDate());

            if (thisDay.getMonth() != date.getMonth()) {
              $day.addClass('overlap');
            };

            this.$days.append($day);
          };

          this.updateName(this.$month, this.monthNames[date.getMonth()]);
          this.updateName(this.$year, this.curMonth.getFullYear());

          $('div', this.$days).click($.proxy(function(e) {
            var $targ = $(e.target);

            // The date= attribute is used here to provide relatively fast
            // selectors for setting certain date cells.
            this.update($targ.attr("date"));

            // Don't consider this selection final if we're just going to an
            // adjacent month.
            if(!$targ.hasClass('overlap')) {
              this.hide();
            }

          }, this));

          $("[date='" + this.format(new Date()) + "']", this.$days).addClass('today');

        };

        $('.selected', this.$days).removeClass('selected');
        $('[date="' + this.selectedDateStr + '"]', this.$days).addClass('selected');
      }

    , selectDate: function(date) {
        if (typeof(date) == "undefined") {
          date = this.parse(this.$el.val());
        };

        if (!date) {
            date = new Date();

          if (this.displayTime) {
            date = new Date(date.getFullYear(), date.getMonth(), date.getDate());
          }
        }

        this.selectedDate = date;
        this.displayedDate = date;
        this.selectedDateStr = this.format(this.selectedDate);
        this.selectMonth(this.selectedDate);

        if (this.displayTime) {
          $('input', this.$time).val(this.formatTime(date));
        }
      }

    , update: function(s) {
        if (this.displayTime)
          s = s + ' ' + this.getTimeString()

        this.$el.val(s).change();
      }

    , show: function(e) {
        e && e.stopPropagation();

        // Hide all other datepickers.
        clearDatePickers(this);

        this.selectDate();

        var offset = this.$el.offset();

        this.$picker.css({
          top: offset.top + this.$el.outerHeight() + 2,
          left: offset.left
        }).show();

        $('html').on('keydown', this.keyHandler);
      }

    , hide: function() {
        this.$picker.hide();
        $('html').off('keydown', this.keyHandler);
      }

    , keyHandler: function(e) {
        // Keyboard navigation shortcuts.
        switch (e.keyCode)
        {
          case 9:
          case 27:
            // Tab or escape hides the datepicker. In this case, just return
            // instead of breaking, so that the e doesn't get stopped.
            this.hide(); return;
          case 13:
            // Enter selects the currently highlighted date.
            this.update(this.selectedDateStr); this.hide(); break;
          default:
            return;
        }
        e.preventDefault();
      }

    , getTimeString: function(s) {
        var time = $('input', this.$time).val();
        return this.getTime(time);
    }

    , pad: function(s) {
        if (s.length === 1)
          s = '0' + s;
        return s;
    }

    , parse: function(s) {
        // Parse a partial RFC 3339 string into a Date.
        var m;
        if ((m = s.match(/^(\d{4,4})-(\d{2,2})-(\d{2,2})$/))) {
          return new Date(m[1], m[2] - 1, m[3]);
        } else {
          return null;
        }
      }

    , parseDateTime: function(s) {
        // Parse a partial RFC 3339 string into a Date.
        var m;
        if ((m = s.match(/^(\d{4,4})-(\d{2,2})-(\d{2,2}) (\d{2,2}):(\d{2,2}):(\d{2,2})$/))) {
          return new Date(m[1], m[2] - 1, m[3], m[4], m[5], m[6]);
        } else {
          return null;
        }
      }

    , validateTime: function(s) {
        return s.match(/^(\d{2,2}):(\d{2,2}):(\d{2,2})$/);
    }

    , getTime: function(s) {
      if (this.validateTime(s)) {
          return s;
      } else {
        // Time without seconds
        if (s.match(/^(\d{2,2}):(\d{2,2})$/)) {
          return s + ':00';
        }
      }

      return '00:00:00';
    }

    , format: function(date) {
        // Format a Date into a string as specified by RFC 3339.
        var month = this.pad((date.getMonth() + 1).toString()),
            dom = this.pad(date.getDate().toString());

        return date.getFullYear() + '-' + month + "-" + dom;
      }

    , formatTime: function(date) {
        var hour = this.pad(date.getHours().toString()),
            min = this.pad(date.getMinutes().toString()),
            sec = this.pad(date.getSeconds().toString());

      return hour + ':' + min + ':' + sec;
    }

    , ahead: function(months, days) {
        // Move ahead ``months`` months and ``days`` days, both integers, can be
        // negative.
        this.selectMonth(new Date(this.displayedDate.getFullYear(),
                                 this.displayedDate.getMonth() + months,
                                 this.displayedDate.getDate() + days));
      }

    , proxy: function(meth) {
        // Bind a method so that it always gets the datepicker instance for
        // ``this``. Return ``this`` so chaining calls works.
        this[meth] = $.proxy(this[meth], this);
        return this;
      }

    , daysBetween: function(start, end) {
        // Return number of days between ``start`` Date object and ``end``.
        var start = Date.UTC(start.getFullYear(), start.getMonth(), start.getDate());
        var end = Date.UTC(end.getFullYear(), end.getMonth(), end.getDate());
        return (end - start) / 86400000;
      }

    , findClosest: function(dow, date, direction) {
        // From a starting date, find the first day ahead of behind it that is
        // a given day of the week.
        var difference = direction * (Math.abs(date.getDay() - dow - (direction * 7)) % 7);
        return new Date(date.getFullYear(), date.getMonth(), date.getDate() + difference);
      }

    , rangeStart: function(date) {
        // Get the first day to show in the current calendar view.
        return this.findClosest(this.startOfWeek,
                                new Date(date.getFullYear(), date.getMonth()),
                                -1);
      }

    , rangeEnd: function(date) {
        // Get the last day to show in the current calendar view.
        return this.findClosest((this.startOfWeek - 1) % 7,
                                new Date(date.getFullYear(), date.getMonth() + 1, 0),
                                1);
      }
  };

  /* DATEPICKER PLUGIN DEFINITION
   * ============================ */

  $.fn.datepicker = function( options ) {
    return this.each(function() { new DatePicker(this, options); });
  };

  $(function() {
    $('html').click(clearDatePickers);
  });

  $.fn.datepicker.DatePicker = DatePicker;

  $.fn.datepicker.defaults = {
    monthNames: ["January", "February", "March", "April", "May", "June",
                 "July", "August", "September", "October", "November", "December"]
  , shortDayNames: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
  , startOfWeek: 1
  , displayTime: false
  };
}( window.jQuery || window.ender );

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
          minimumInputLength: $el.attr('data-minimum-input-length'),
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
            var value = JSON.parse($el.attr('data-json'));
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
       * Process Leaflet (map) widget
       */
      function processLeafletWidget($el, name) {
        if (!window.MAPBOX_MAP_ID) {
          console.error("You must set MAPBOX_MAP_ID in your Flask settings to use the map widget");
          return false;
        }
        if (!window.DEFAULT_CENTER_LAT || !window.DEFAULT_CENTER_LONG) {
          console.error("You must set DEFAULT_CENTER_LAT and DEFAULT_CENTER_LONG in your Flask settings to use the map widget");
          return false;
        }

        var geometryType = $el.data("geometry-type")
        if (geometryType) {
          geometryType = geometryType.toUpperCase();
        } else {
          geometryType = "GEOMETRY";
        }
        var multiple = geometryType.lastIndexOf("MULTI", geometryType) === 0;
        var editable = ! $el.is(":disabled");

        var $map = $("<div>").width($el.data("width")).height($el.data("height"));
        $el.after($map).hide();

        var center = null;
        if($el.data("lat") && $el.data("lng")) {
          center = L.latLng($el.data("lat"), $el.data("lng"));
        }

        var maxBounds = null;
        if ($el.data("max-bounds-sw-lat") && $el.data("max-bounds-sw-lng") &&
          $el.data("max-bounds-ne-lat") && $el.data("max-bounds-ne-lng"))
        {
          maxBounds = L.latLngBounds(
            L.latLng($el.data("max-bounds-sw-lat"), $el.data("max-bounds-sw-lng")),
            L.latLng($el.data("max-bounds-ne-lat"), $el.data("max-bounds-ne-lng"))
          )
        }

        var editableLayers;
        if ($el.val()) {
          editableLayers = new L.geoJson(JSON.parse($el.val()));
          center = center || editableLayers.getBounds().getCenter();
        } else {
          editableLayers = new L.geoJson();
        }

        var mapOptions = {
          center: center,
          zoom: $el.data("zoom") || 12,
          minZoom: $el.data("min-zoom"),
          maxZoom: $el.data("max-zoom"),
          maxBounds: maxBounds
        }

        if (!editable) {
          mapOptions.dragging = false;
          mapOptions.touchzoom = false;
          mapOptions.scrollWheelZoom = false;
          mapOptions.doubleClickZoom = false;
          mapOptions.boxZoom = false;
          mapOptions.tap = false;
          mapOptions.keyboard = false;
          mapOptions.zoomControl = false;
        }

        // only show attributions if the map is big enough
        // (otherwise, it gets in the way)
        if ($map.width() * $map.height() < 10000) {
          mapOptions.attributionControl = false;
        }

        var map = L.map($map.get(0), mapOptions)
        map.addLayer(editableLayers);

        if (center) {
          // if we have more than one point, make the map show everything
          var bounds = editableLayers.getBounds()
          if (!bounds.getNorthEast().equals(bounds.getSouthWest())) {
            map.fitBounds(bounds);
          }
        } else {
          // use the default map center
          map.setView([window.DEFAULT_CENTER_LAT, window.DEFAULT_CENTER_LONG], 12);
        }

        // set up tiles
        if($el.data('tile-layer-url')){
          var attribution = $el.data('tile-layer-attribution') || ''
          L.tileLayer('//'+$el.data('tile-layer-url'), {
            attribution: attribution,
            maxZoom: 18
          }).addTo(map)
        } else {
          var mapboxUrl = 'https://api.mapbox.com/styles/v1/mapbox/'+window.MAPBOX_MAP_ID+'/tiles/{z}/{x}/{y}?access_token='+window.MAPBOX_ACCESS_TOKEN
          L.tileLayer(mapboxUrl, {
            attribution: 'Map data &copy; <a href="//openstreetmap.org">OpenStreetMap</a> contributors, <a href="//creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="//mapbox.com">Mapbox</a>',
            maxZoom: 18
          }).addTo(map);
        }


        // everything below here is to set up editing, so if we're not editable,
        // we can just return early.
        if (!editable) {
          return true;
        }

        // set up Leaflet.draw editor
        var drawOptions = {
          draw: {
            // circles are not geometries in geojson
            circle: false,
            circlemarker: false
          },
          edit: {
            featureGroup: editableLayers
          }
        }

        if ($.inArray(geometryType, ["POINT", "MULTIPOINT"]) > -1) {
          drawOptions.draw.polyline = false;
          drawOptions.draw.polygon = false;
          drawOptions.draw.rectangle = false;
        } else if ($.inArray(geometryType, ["LINESTRING", "MULTILINESTRING"]) > -1) {
          drawOptions.draw.marker = false;
          drawOptions.draw.polygon = false;
          drawOptions.draw.rectangle = false;
        } else if ($.inArray(geometryType, ["POLYGON", "MULTIPOLYGON"]) > -1) {
          drawOptions.draw.marker = false;
          drawOptions.draw.polyline = false;
        }
        var drawControl = new L.Control.Draw(drawOptions);
        map.addControl(drawControl);
        if (window.MAPBOX_SEARCH) {
          var circle = L.circleMarker([0, 0]);
          var $autocompleteEl = $('<input style="position: absolute; z-index: 9999; display: block; margin: -42px 0 0 10px; width: 50%">');
          var $form = $($el.get(0).form);

          $autocompleteEl.insertAfter($map);
          $form.on('submit', function (evt) {
            if ($autocompleteEl.is(':focus')) {
              evt.preventDefault();
              return false;
            }
          });
          var autocomplete = new google.maps.places.Autocomplete($autocompleteEl.get(0));
          autocomplete.addListener('place_changed', function() {
            var place = autocomplete.getPlace();
            var loc = place.geometry.location;
            var viewport = place.geometry.viewport;
            circle.setLatLng(L.latLng(loc.lat(), loc.lng()));
            circle.addTo(map);
            if (viewport) {
              map.fitBounds([
                viewport.getNorthEast().toJSON(),
                viewport.getSouthWest().toJSON(),
              ]);
            }
            else {
              map.fitBounds(circle.getBounds());
            }
          });
        }


        // save when the editableLayers are edited
        var saveToTextArea = function() {
          var geo = editableLayers.toGeoJSON();
          if (geo.features.length === 0) {
            $el.val("");
            return true
          }
          if (multiple) {
            var coords = $.map(geo.features, function(feature) {
              return [feature.geometry.coordinates];
            })
            geo = {
              "type": geometryType,
              "coordinates": coords
            }
          } else {
            geo = geo.features[0].geometry;
          }
          $el.val(JSON.stringify(geo));
        }

        // handle creation
        map.on('draw:created', function (e) {
          if (!multiple) {
            editableLayers.clearLayers();
          }
          editableLayers.addLayer(e.layer);
          saveToTextArea();
        })
        map.on('draw:edited', saveToTextArea);
        map.on('draw:deleted', saveToTextArea);
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

        // make x-editable's POST compatible with WTForms
        // for x-editable, x-editable-combodate, and x-editable-boolean cases
        var overrideXeditableParams = function(params) {
            var newParams = {};
            newParams['list_form_pk'] = params.pk;
            newParams[params.name] = params.value;
            if ($(this).data('csrf')) {
                newParams['csrf_token'] = $(this).data('csrf');
            }
            return newParams;
        }

        switch (name) {
            case 'select2':
                var opts = {
                    width: 'resolve'
                };

                if ($el.attr('data-allow-blank'))
                    opts['allowClear'] = true;

                opts['minimumInputLength'] = $el.attr('data-minimum-input-length');

                if ($el.attr('data-tags')) {
                    $.extend(opts, {
                        tokenSeparators: [','],
                        tags: []
                    });
                }

                $el.select2(opts);
                return true;
            case 'select2-tags':
                // get tags from element
                if ($el.attr('data-tags')) {
                    var tags = JSON.parse($el.attr('data-tags'));
                } else {
                    var tags = [];
                }

                // default to a comma for separating list items
                // allows using spaces as a token separator
                if ($el.attr('data-token-separators')) {
                    var tokenSeparators = JSON.parse($el.attr('data-tags'));
                } else {
                    var tokenSeparators = [','];
                }

                if ($el.attr('data-allow-duplicate-tags')) {
                    var allowDuplicateTags = JSON.parse($el.attr('data-allow-duplicate-tags'));
                } else {
                    var allowDuplicateTags = false;
                }

                if (allowDuplicateTags) {
                    // To allow duplicate tags, we need to have a unique ID for each entry.
                    // The easiest way to do this is appending the current Unix timestamp.
                    // However, this causes the ID to change (the ID is what flask-admin receives later on).
                    // We separate the date with a '#' and put a space at the end of the ID
                    // (something the user can't do due to 'trim') to specially mark these entries.
                    var createSearchChoice = function (term) {
                        return {
                            id: $.trim(term) + "#" + new Date().getTime() + " ",
                            text: $.trim(term)
                        };
                    };
                } else {
                    var createSearchChoice = undefined;
                }

                var opts = {
                    width: 'resolve',
                    tags: tags,
                    tokenSeparators: tokenSeparators,
                    createSearchChoice: createSearchChoice,
                    formatNoMatches: function() {
                        return 'Enter comma separated values';
                    }
                };

                $el.select2(opts);

                // submit on ENTER
                $el.parent().find('input.select2-input').on('keyup', function(e) {
                   if(e.keyCode === 13)
                      $(this).closest('form').submit();
                });
                return true;
            case 'select2-ajax':
                processAjaxWidget($el, name);
                return true;
            case 'datepicker':
                $el.daterangepicker({
                  timePicker: false,
                  showDropdowns: true,
                  singleDatePicker: true,
                  format: $el.attr('data-date-format')
                },
                function(start, end) {
                    $('.filter-val').trigger("change");
                });
                return true;
            case 'daterangepicker':
                $el.daterangepicker({
                  timePicker: false,
                  showDropdowns: true,
                  separator: ' to ',
                  format: $el.attr('data-date-format')
                },
                function(start, end) {
                    $('.filter-val').trigger("change");
                });
                return true;
            case 'datetimepicker':
                $el.daterangepicker({
                  timePicker: true,
                  showDropdowns: true,
                  singleDatePicker: true,
                  timePickerIncrement: 1,
                  timePicker12Hour: false,
                  format: $el.attr('data-date-format')
                },
                function(start, end) {
                    $('.filter-val').trigger("change");
                });
                $el.on('show.daterangepicker', function (event, data) {
                  if ($el.val() == "") {
                    var now = moment().seconds(0); // set seconds to 0
                    // change datetime to current time if field is blank
                    $el.data('daterangepicker').setCustomDates(now, now);
                  }
                });
                return true;
            case 'datetimerangepicker':
                $el.daterangepicker({
                  timePicker: true,
                  showDropdowns: true,
                  timePickerIncrement: 1,
                  timePicker12Hour: false,
                  separator: ' to ',
                  format: $el.attr('data-date-format')
                },
                function(start, end) {
                    $('.filter-val').trigger("change");
                });
                return true;
            case 'timepicker':
                $el.daterangepicker({
                  // Bootstrap 2 option
                  timePicker: true,
                  showDropdowns: true,
                  format: $el.attr('data-date-format'),
                  timePicker12Hour: false,
                  timePickerIncrement: 1,
                  singleDatePicker: true
                },
                function(start, end) {
                    $('.filter-val').trigger("change");
                });
                // hack to hide calendar to create a time-only picker
                $el.data('daterangepicker').container.find('.calendar-date').hide();
                $el.on('showCalendar.daterangepicker', function (event, data) {
                    var $container = data.container;
                    $container.find('.calendar-date').remove();
                });
                return true;
            case 'timerangepicker':
                $el.daterangepicker({
                  // Bootstrap 2 option
                  timePicker: true,
                  showDropdowns: true,
                  format: $el.attr('data-date-format'),
                  timePicker12Hour: false,
                  separator: ' to ',
                  timePickerIncrement: 1
                },
                function(start, end) {
                    $('.filter-val').trigger("change");
                });
                // hack - hide calendar + range inputs
                $el.data('daterangepicker').container.find('.calendar-date').hide();
                $el.data('daterangepicker').container.find('.daterangepicker_start_input').hide();
                $el.data('daterangepicker').container.find('.daterangepicker_end_input').hide();
                // hack - add TO between time inputs
                $el.data('daterangepicker').container.find('.left').before($('<div style="float: right; margin-top: 20px; padding-left: 5px; padding-right: 5px;"> to </span>'));
                $el.on('showCalendar.daterangepicker', function (event, data) {
                    var $container = data.container;
                    $container.find('.calendar-date').remove();
                });
                return true;
            case 'leaflet':
                processLeafletWidget($el, name);
                return true;
            case 'x-editable':
                $el.editable({
                    params: overrideXeditableParams,
                    combodate: {
                        // prevent minutes from showing in 5 minute increments
                        minuteStep: 1,
                        maxYear: 2030,
                    }
                });
                return true;
            case 'x-editable-combodate':
                // Fixes bootstrap4 issue where data-template breaks bs4 popover.
                // https://github.com/flask-admin/flask-admin/issues/2022
                let template = $el.data('template');
                $el.removeAttr('data-template');
                $el.editable({
                    params: overrideXeditableParams,
                    template: template,
                    combodate: {
                        // prevent minutes from showing in 5 minute increments
                        minuteStep: 1,
                        maxYear: 2030,
                    }
                });
                return true;
            case 'x-editable-select2-multiple':
                $el.editable({
                    params: overrideXeditableParams,
                    ajaxOptions: {
                        // prevents keys with the same value from getting converted into arrays
                        traditional: true
                    },
                    select2: {
                        multiple: true
                    },
                    display: function(value) {
                        // override to display text instead of ids on list view
                        var html = [];
                        // temporary patch to provide bs3 & bs4 compatibility
                        var data = $.fn.editableutils.itemsByValue(value, $el.data('source'), 'id').concat(
                            $.fn.editableutils.itemsByValue(value, $el.data('source'), 'value'));

                        if(data.length) {
                            $.each(data, function(i, v) { html.push($.fn.editableutils.escape(v.text)); });
                            $(this).html(html.join(', '));
                        } else {
                            $(this).empty();
                        }
                    }
                });
                return true;
            case 'x-editable-boolean':
                $el.editable({
                    params: overrideXeditableParams,
                    display: function(value, response) {
                      // display boolean value as an icon
                      var glyph = (value == '1') ? 'ok-circle' : 'minus-sign';
                      var fa = (value == '1') ? 'fa-check' : 'fa-minus-circle';
                      $(this).empty().append($('<span />', {
                        'class': `fa ${fa} glyphicon glyphicon-${glyph} icon-${glyph}`,
                        'title': $(this).parent().data('title'),
                      }));
                    },
                    success: function(response, newValue) {
                      // update display
                      var glyph = (newValue == '1') ? 'ok-circle' : 'minus-sign';
                      var fa = (newValue  == '1') ? 'fa-check' : 'fa-minus-circle';
                      $(this).empty().append($('<span />', {
                        'class': `fa ${fa} glyphicon glyphicon-${glyph} icon-${glyph}`,
                        'title': $(this).parent().data('title'),
                      }));
                    }
                });
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

        if ($parentForm.hasClass('fresh')) {
          id = $parentForm.attr('id');
          if (elID) {
            id += '-' + elID;
          }
        }

        var $fieldList = $el.find('> .inline-field-list');
        var maxId = 0;

        $fieldList.children('.inline-field').each(function(idx, field) {
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

        $(':input[data-role], a[data-role]', parent).each(function() {
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
        var r = confirm($('.inline-remove-field').attr('value'));
        var form = $(this).closest('.inline-field');
        if ( r == true ){
        form.remove();
      }
    });

    // Expose faForm globally
    var faForm = window.faForm = new AdminForm();
    $(document).trigger('adminFormReady')

    // Apply global styles for current page after page loaded
    $(function() {
        faForm.applyGlobalStyles(document);
    });
})();

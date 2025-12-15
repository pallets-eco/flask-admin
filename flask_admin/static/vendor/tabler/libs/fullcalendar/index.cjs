'use strict';

Object.defineProperty(exports, '__esModule', { value: true });

var index_cjs = require('@fullcalendar/core/index.cjs');
var interactionPlugin = require('@fullcalendar/interaction/index.cjs');
var dayGridPlugin = require('@fullcalendar/daygrid/index.cjs');
var timeGridPlugin = require('@fullcalendar/timegrid/index.cjs');
var listPlugin = require('@fullcalendar/list/index.cjs');
var multiMonthPlugin = require('@fullcalendar/multimonth/index.cjs');

function _interopDefaultLegacy (e) { return e && typeof e === 'object' && 'default' in e ? e : { 'default': e }; }

var interactionPlugin__default = /*#__PURE__*/_interopDefaultLegacy(interactionPlugin);
var dayGridPlugin__default = /*#__PURE__*/_interopDefaultLegacy(dayGridPlugin);
var timeGridPlugin__default = /*#__PURE__*/_interopDefaultLegacy(timeGridPlugin);
var listPlugin__default = /*#__PURE__*/_interopDefaultLegacy(listPlugin);
var multiMonthPlugin__default = /*#__PURE__*/_interopDefaultLegacy(multiMonthPlugin);

index_cjs.globalPlugins.push(interactionPlugin__default["default"], dayGridPlugin__default["default"], timeGridPlugin__default["default"], listPlugin__default["default"], multiMonthPlugin__default["default"]);

Object.keys(index_cjs).forEach(function (k) {
	if (k !== 'default' && !exports.hasOwnProperty(k)) Object.defineProperty(exports, k, {
		enumerable: true,
		get: function () { return index_cjs[k]; }
	});
});
Object.keys(interactionPlugin).forEach(function (k) {
	if (k !== 'default' && !exports.hasOwnProperty(k)) Object.defineProperty(exports, k, {
		enumerable: true,
		get: function () { return interactionPlugin[k]; }
	});
});

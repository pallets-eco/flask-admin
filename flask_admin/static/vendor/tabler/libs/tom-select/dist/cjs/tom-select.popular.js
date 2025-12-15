"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tom_select_ts_1 = require("./tom-select.js");
const plugin_ts_1 = require("./plugins/caret_position/plugin.js");
const plugin_ts_2 = require("./plugins/dropdown_input/plugin.js");
const plugin_ts_3 = require("./plugins/no_backspace_delete/plugin.js");
const plugin_ts_4 = require("./plugins/remove_button/plugin.js");
const plugin_ts_5 = require("./plugins/restore_on_backspace/plugin.js");
tom_select_ts_1.default.define('caret_position', plugin_ts_1.default);
tom_select_ts_1.default.define('dropdown_input', plugin_ts_2.default);
tom_select_ts_1.default.define('no_backspace_delete', plugin_ts_3.default);
tom_select_ts_1.default.define('remove_button', plugin_ts_4.default);
tom_select_ts_1.default.define('restore_on_backspace', plugin_ts_5.default);
exports.default = tom_select_ts_1.default;
//# sourceMappingURL=tom-select.popular.js.map
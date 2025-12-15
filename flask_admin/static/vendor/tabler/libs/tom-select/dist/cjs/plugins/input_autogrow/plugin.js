"use strict";
/**
 * Plugin: "input_autogrow" (Tom Select)
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this
 * file except in compliance with the License. You may obtain a copy of the License at:
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
 * ANY KIND, either express or implied. See the License for the specific language
 * governing permissions and limitations under the License.
 *
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = default_1;
const utils_ts_1 = require("../../utils.js");
function default_1() {
    var self = this;
    self.on('initialize', () => {
        var test_input = document.createElement('span');
        var control = self.control_input;
        test_input.style.cssText = 'position:absolute; top:-99999px; left:-99999px; width:auto; padding:0; white-space:pre; ';
        self.wrapper.appendChild(test_input);
        var transfer_styles = ['letterSpacing', 'fontSize', 'fontFamily', 'fontWeight', 'textTransform'];
        for (const style_name of transfer_styles) {
            // @ts-ignore TS7015 https://stackoverflow.com/a/50506154/697576
            test_input.style[style_name] = control.style[style_name];
        }
        /**
         * Set the control width
         *
         */
        var resize = () => {
            test_input.textContent = control.value;
            control.style.width = test_input.clientWidth + 'px';
        };
        resize();
        self.on('update item_add item_remove', resize);
        (0, utils_ts_1.addEvent)(control, 'input', resize);
        (0, utils_ts_1.addEvent)(control, 'keyup', resize);
        (0, utils_ts_1.addEvent)(control, 'blur', resize);
        (0, utils_ts_1.addEvent)(control, 'update', resize);
    });
}
;
//# sourceMappingURL=plugin.js.map
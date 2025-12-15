"use strict";
/**
 * Plugin: "drag_drop" (Tom Select)
 * Copyright (c) contributors
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
const vanilla_ts_1 = require("../../vanilla.js");
const insertAfter = (referenceNode, newNode) => {
    var _a;
    (_a = referenceNode.parentNode) === null || _a === void 0 ? void 0 : _a.insertBefore(newNode, referenceNode.nextSibling);
};
const insertBefore = (referenceNode, newNode) => {
    var _a;
    (_a = referenceNode.parentNode) === null || _a === void 0 ? void 0 : _a.insertBefore(newNode, referenceNode);
};
const isBefore = (referenceNode, newNode) => {
    do {
        newNode = newNode === null || newNode === void 0 ? void 0 : newNode.previousElementSibling;
        if (referenceNode == newNode) {
            return true;
        }
    } while (newNode && newNode.previousElementSibling);
    return false;
};
function default_1() {
    var self = this;
    if (self.settings.mode !== 'multi')
        return;
    var orig_lock = self.lock;
    var orig_unlock = self.unlock;
    let sortable = true;
    let drag_item;
    /**
     * Add draggable attribute to item
     */
    self.hook('after', 'setupTemplates', () => {
        var orig_render_item = self.settings.render.item;
        self.settings.render.item = (data, escape) => {
            const item = (0, vanilla_ts_1.getDom)(orig_render_item.call(self, data, escape));
            (0, vanilla_ts_1.setAttr)(item, { 'draggable': 'true' });
            // prevent doc_mousedown (see tom-select.ts)
            const mousedown = (evt) => {
                if (!sortable)
                    (0, utils_ts_1.preventDefault)(evt);
                evt.stopPropagation();
            };
            const dragStart = (evt) => {
                drag_item = item;
                setTimeout(() => {
                    item.classList.add('ts-dragging');
                }, 0);
            };
            const dragOver = (evt) => {
                evt.preventDefault();
                item.classList.add('ts-drag-over');
                moveitem(item, drag_item);
            };
            const dragLeave = () => {
                item.classList.remove('ts-drag-over');
            };
            const moveitem = (targetitem, dragitem) => {
                if (dragitem === undefined)
                    return;
                if (isBefore(dragitem, item)) {
                    insertAfter(targetitem, dragitem);
                }
                else {
                    insertBefore(targetitem, dragitem);
                }
            };
            const dragend = () => {
                document.querySelectorAll('.ts-drag-over').forEach(el => el.classList.remove('ts-drag-over'));
                drag_item === null || drag_item === void 0 ? void 0 : drag_item.classList.remove('ts-dragging');
                drag_item = undefined;
                var values = [];
                self.control.querySelectorAll(`[data-value]`).forEach((el) => {
                    if (el.dataset.value) {
                        let value = el.dataset.value;
                        if (value) {
                            values.push(value);
                        }
                    }
                });
                self.setValue(values);
            };
            (0, utils_ts_1.addEvent)(item, 'mousedown', mousedown);
            (0, utils_ts_1.addEvent)(item, 'dragstart', dragStart);
            (0, utils_ts_1.addEvent)(item, 'dragenter', dragOver);
            (0, utils_ts_1.addEvent)(item, 'dragover', dragOver);
            (0, utils_ts_1.addEvent)(item, 'dragleave', dragLeave);
            (0, utils_ts_1.addEvent)(item, 'dragend', dragend);
            return item;
        };
    });
    self.hook('instead', 'lock', () => {
        sortable = false;
        return orig_lock.call(self);
    });
    self.hook('instead', 'unlock', () => {
        sortable = true;
        return orig_unlock.call(self);
    });
}
;
//# sourceMappingURL=plugin.js.map
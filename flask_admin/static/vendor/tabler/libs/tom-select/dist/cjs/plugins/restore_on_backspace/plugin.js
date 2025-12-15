"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = default_1;
function default_1(userOptions) {
    const self = this;
    const options = Object.assign({
        text: (option) => {
            return option[self.settings.labelField];
        }
    }, userOptions);
    self.on('item_remove', function (value) {
        if (!self.isFocused) {
            return;
        }
        if (self.control_input.value.trim() === '') {
            var option = self.options[value];
            if (option) {
                self.setTextboxValue(options.text.call(self, option));
            }
        }
    });
}
;
//# sourceMappingURL=plugin.js.map
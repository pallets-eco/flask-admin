"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.KEY_SHORTCUT = exports.IS_MAC = exports.KEY_TAB = exports.KEY_DELETE = exports.KEY_BACKSPACE = exports.KEY_DOWN = exports.KEY_RIGHT = exports.KEY_UP = exports.KEY_LEFT = exports.KEY_ESC = exports.KEY_RETURN = exports.KEY_A = void 0;
exports.KEY_A = 65;
exports.KEY_RETURN = 13;
exports.KEY_ESC = 27;
exports.KEY_LEFT = 37;
exports.KEY_UP = 38;
exports.KEY_RIGHT = 39;
exports.KEY_DOWN = 40;
exports.KEY_BACKSPACE = 8;
exports.KEY_DELETE = 46;
exports.KEY_TAB = 9;
exports.IS_MAC = typeof navigator === 'undefined' ? false : /Mac/.test(navigator.userAgent);
exports.KEY_SHORTCUT = exports.IS_MAC ? 'metaKey' : 'ctrlKey'; // ctrl key or apple key for ma
//# sourceMappingURL=constants.js.map
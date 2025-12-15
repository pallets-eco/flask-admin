"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.replaceNode = exports.setAttr = exports.nodeIndex = exports.isEmptyObject = exports.getTail = exports.parentMatch = exports.castAsArray = exports.classesArray = exports.removeClasses = exports.addClasses = exports.applyCSS = exports.triggerEvent = exports.escapeQuery = exports.isHtmlString = exports.getDom = void 0;
const utils_ts_1 = require("./utils.js");
/**
 * Return a dom element from either a dom query string, jQuery object, a dom element or html string
 * https://stackoverflow.com/questions/494143/creating-a-new-dom-element-from-an-html-string-using-built-in-dom-methods-or-pro/35385518#35385518
 *
 * param query should be {}
 */
const getDom = (query) => {
    if (query.jquery) {
        return query[0];
    }
    if (query instanceof HTMLElement) {
        return query;
    }
    if ((0, exports.isHtmlString)(query)) {
        var tpl = document.createElement('template');
        tpl.innerHTML = query.trim(); // Never return a text node of whitespace as the result
        return tpl.content.firstChild;
    }
    return document.querySelector(query);
};
exports.getDom = getDom;
const isHtmlString = (arg) => {
    if (typeof arg === 'string' && arg.indexOf('<') > -1) {
        return true;
    }
    return false;
};
exports.isHtmlString = isHtmlString;
const escapeQuery = (query) => {
    return query.replace(/['"\\]/g, '\\$&');
};
exports.escapeQuery = escapeQuery;
/**
 * Dispatch an event
 *
 */
const triggerEvent = (dom_el, event_name) => {
    var event = document.createEvent('HTMLEvents');
    event.initEvent(event_name, true, false);
    dom_el.dispatchEvent(event);
};
exports.triggerEvent = triggerEvent;
/**
 * Apply CSS rules to a dom element
 *
 */
const applyCSS = (dom_el, css) => {
    Object.assign(dom_el.style, css);
};
exports.applyCSS = applyCSS;
/**
 * Add css classes
 *
 */
const addClasses = (elmts, ...classes) => {
    var norm_classes = (0, exports.classesArray)(classes);
    elmts = (0, exports.castAsArray)(elmts);
    elmts.map(el => {
        norm_classes.map(cls => {
            el.classList.add(cls);
        });
    });
};
exports.addClasses = addClasses;
/**
 * Remove css classes
 *
 */
const removeClasses = (elmts, ...classes) => {
    var norm_classes = (0, exports.classesArray)(classes);
    elmts = (0, exports.castAsArray)(elmts);
    elmts.map(el => {
        norm_classes.map(cls => {
            el.classList.remove(cls);
        });
    });
};
exports.removeClasses = removeClasses;
/**
 * Return arguments
 *
 */
const classesArray = (args) => {
    var classes = [];
    (0, utils_ts_1.iterate)(args, (_classes) => {
        if (typeof _classes === 'string') {
            _classes = _classes.trim().split(/[\t\n\f\r\s]/);
        }
        if (Array.isArray(_classes)) {
            classes = classes.concat(_classes);
        }
    });
    return classes.filter(Boolean);
};
exports.classesArray = classesArray;
/**
 * Create an array from arg if it's not already an array
 *
 */
const castAsArray = (arg) => {
    if (!Array.isArray(arg)) {
        arg = [arg];
    }
    return arg;
};
exports.castAsArray = castAsArray;
/**
 * Get the closest node to the evt.target matching the selector
 * Stops at wrapper
 *
 */
const parentMatch = (target, selector, wrapper) => {
    if (wrapper && !wrapper.contains(target)) {
        return;
    }
    while (target && target.matches) {
        if (target.matches(selector)) {
            return target;
        }
        target = target.parentNode;
    }
};
exports.parentMatch = parentMatch;
/**
 * Get the first or last item from an array
 *
 * > 0 - right (last)
 * <= 0 - left (first)
 *
 */
const getTail = (list, direction = 0) => {
    if (direction > 0) {
        return list[list.length - 1];
    }
    return list[0];
};
exports.getTail = getTail;
/**
 * Return true if an object is empty
 *
 */
const isEmptyObject = (obj) => {
    return (Object.keys(obj).length === 0);
};
exports.isEmptyObject = isEmptyObject;
/**
 * Get the index of an element amongst sibling nodes of the same type
 *
 */
const nodeIndex = (el, amongst) => {
    if (!el)
        return -1;
    amongst = amongst || el.nodeName;
    var i = 0;
    while (el = el.previousElementSibling) {
        if (el.matches(amongst)) {
            i++;
        }
    }
    return i;
};
exports.nodeIndex = nodeIndex;
/**
 * Set attributes of an element
 *
 */
const setAttr = (el, attrs) => {
    (0, utils_ts_1.iterate)(attrs, (val, attr) => {
        if (val == null) {
            el.removeAttribute(attr);
        }
        else {
            el.setAttribute(attr, '' + val);
        }
    });
};
exports.setAttr = setAttr;
/**
 * Replace a node
 */
const replaceNode = (existing, replacement) => {
    if (existing.parentNode)
        existing.parentNode.replaceChild(replacement, existing);
};
exports.replaceNode = replaceNode;
//# sourceMappingURL=vanilla.js.map
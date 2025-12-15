export const addRemoveClass = (el, bool, className) => {
    el.classList[bool ? 'add' : 'remove'](className);
}

export const createSpanEl = (attributes) => {
    const el = document.createElement('span');
    attributes = attributes || {};
    for (let key in attributes) {
        el.setAttribute(key, attributes[key]);
    }
    return el;
}

export const inRange = (value, min, max) => {
    return /^\d+$/.test(value) && min <= value && value <= max;
}

export const insertSpanEl = (el, after, attributes) => {
    const newEl = createSpanEl(attributes);
    el.parentNode.insertBefore(newEl, after ? el.nextSibling : el);
    return newEl;
}

export const isEmpty = (el) => {
    return null === el.getAttribute('value') || '' === el.value;
}

export const merge = (...args) => { // adapted from https://github.com/firstandthird/aug
    const results = {};
    args.forEach(prop => {
        Object.keys(prop || {}).forEach(propName => {
            if (args[0][propName] === undefined) return; // restrict keys to the defaults
            const propValue = prop[propName];
            if (type(propValue) === 'Object' && type(results[propName]) === 'Object') {
                results[propName] = merge(results[propName], propValue);
                return;
            }
            results[propName] = propValue;
        });
    });
    return results;
}

export const type = (value) => {
    return {}.toString.call(value).slice(8, -1);
};

export const values = (selectEl) => {
    const values = [];
    [].forEach.call(selectEl.options, (el) => {
        const value = parseInt(el.value, 10) || 0;
        if (value > 0) {
            values.push({
                index: el.index,
                text: el.text,
                value: value,
            })
        }
    });
    return values.sort((a, b) => a.value - b.value);
}

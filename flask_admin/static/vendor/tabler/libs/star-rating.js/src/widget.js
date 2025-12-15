import { addRemoveClass, createSpanEl, inRange, insertSpanEl, isEmpty, values } from './helpers'
import { supportsPassiveEvents } from 'detect-it'

export class Widget {
    constructor (el, props) { // (HTMLElement, object):void
        this.direction = window.getComputedStyle(el, null).getPropertyValue('direction');
        this.el = el;
        this.events = {
            change: this.onChange.bind(this),
            keydown: this.onKeyDown.bind(this),
            mousedown: this.onPointerDown.bind(this),
            mouseleave: this.onPointerLeave.bind(this),
            mousemove: this.onPointerMove.bind(this),
            reset: this.onReset.bind(this),
            touchend: this.onPointerDown.bind(this),
            touchmove: this.onPointerMove.bind(this),
        };
        this.indexActive = null; // the active span index
        this.indexSelected = null; // the selected span index
        this.props = props;
        this.tick = null;
        this.ticking = false;
        this.values = values(el);
        this.widgetEl = null;
        if (this.el.widget) {
            this.el.widget.destroy(); // remove any stale event listeners
        }
        if (inRange(this.values.length, 1, this.props.maxStars)) {
            this.build();
        } else {
            this.destroy();
        }
    }

    build () { // ():void
        this.destroy();
        this.buildWidget();
        this.selectValue((this.indexSelected = this.selected()), false); // set the initial value but do not trigger change event
        this.handleEvents('add');
        this.el.widget = this; // store a reference to this widget on the SELECT so that we can remove stale event listeners
    }

    buildWidget () { // ():void
        let parentEl = null;
        let widgetEl = null;
        if (this.props.prebuilt) {
            parentEl = this.el.parentNode
            widgetEl = parentEl.querySelector('.' + this.props.classNames.base + '--stars')
        }
        if (null === widgetEl) {
            parentEl = insertSpanEl(this.el, false, { class: this.props.classNames.base });
            parentEl.appendChild(this.el);
            widgetEl = insertSpanEl(this.el, true, { class: this.props.classNames.base + '--stars' });
            this.values.forEach((item, index) => {
                const el = createSpanEl({ 'data-index': index, 'data-value': item.value });
                if ('function' === typeof this.props.stars) {
                    this.props.stars.call(this, el, item, index);
                }
                [].forEach.call(el.children, el => el.style.pointerEvents = 'none');
                widgetEl.innerHTML += el.outerHTML;
            })
        }
        parentEl.dataset.starRating = '';
        parentEl.classList.add(this.props.classNames.base + '--' + this.direction);
        if (this.props.tooltip) {
            widgetEl.setAttribute('role', 'tooltip');
        }
        this.widgetEl = widgetEl
    }

    changeIndexTo (index, force) { // (int):void
        if (this.indexActive !== index || force) {
            [].forEach.call(this.widgetEl.children, (el, i) => { // i starts at zero
                addRemoveClass(el, i <= index, this.props.classNames.active);
                addRemoveClass(el, i === this.indexSelected, this.props.classNames.selected);
            });
            this.widgetEl.setAttribute('data-rating', index + 1);
            if ('function' !== typeof this.props.stars && !this.props.prebuilt) { // @v3 compat
                this.widgetEl.classList.remove('s' + (10 * (this.indexActive + 1)));
                this.widgetEl.classList.add('s' + (10 * (index + 1)));
            }
            if (this.props.tooltip) {
                const label = index < 0 ? this.props.tooltip : this.values[index]?.text;
                this.widgetEl.setAttribute('aria-label', label);
            }
            this.indexActive = index;
        }
        this.ticking = false;
    }

    destroy () { // ():void
        this.indexActive = null; // the active span index
        this.indexSelected = this.selected(); // the selected span index
        const parentEl = this.el.parentNode;
        if (parentEl.classList.contains(this.props.classNames.base)) {
            if (this.props.prebuilt) {
                this.widgetEl = parentEl.querySelector('.' + this.props.classNames.base + '--stars')
                parentEl.classList.remove(this.props.classNames.base + '--' + this.direction);
                delete parentEl.dataset.starRating
            } else {
                parentEl.parentNode.replaceChild(this.el, parentEl);
            }
            this.handleEvents('remove');
        }
        delete this.el.widget // remove the widget reference
    }

    eventListener (el, action, events, items) { // (HTMLElement, string, array, object):void
        events.forEach(ev => el[action + 'EventListener'](ev, this.events[ev], items || false));
    }

    handleEvents (action) { // (string):void
        const formEl = this.el.closest('form');
        if (formEl && formEl.tagName === 'FORM') {
            this.eventListener(formEl, action, ['reset']);
        }
        this.eventListener(this.el, action, ['change']); // always trigger the change event, even when SELECT is disabled
        if ('add' === action && this.el.disabled) return;
        this.eventListener(this.el, action, ['keydown']);
        this.eventListener(this.widgetEl, action, ['mousedown', 'mouseleave', 'mousemove', 'touchend', 'touchmove'],
            supportsPassiveEvents ? { passive: false } : false
        );
    }

    indexFromEvent (ev) { // (MouseEvent|TouchEvent):void
        const origin = ev.touches?.[0] || ev.changedTouches?.[0] || ev;
        const el = document.elementFromPoint(origin.clientX, origin.clientY);
        if (el.parentNode === this.widgetEl) {
            return [].slice.call(el.parentNode.children).indexOf(el);
        }
        return this.indexActive;
    }

    onChange () { // ():void
        this.changeIndexTo(this.selected(), true);
    }

    onKeyDown (ev) { // (KeyboardEvent):void
        const key = ev.key.slice(5);
        if (!~['Left', 'Right'].indexOf(key)) return;
        ev.preventDefault();
        let increment = key === 'Left' ? -1 : 1;
        if (this.direction === 'rtl') {
            increment *= -1;
        }
        const maxIndex = this.values.length - 1;
        const minIndex = -1;
        const index = Math.min(Math.max(this.selected() + increment, minIndex), maxIndex);
        this.selectValue(index, true); // trigger change event
    }

    onPointerDown (ev) { // (MouseEvent|TouchEvent):void
        ev.preventDefault();
        // this.el.focus(); // highlight the rating field
        let index = this.indexFromEvent(ev);
        if (this.props.clearable && index === this.indexSelected) {
            index = -1; // remove the value
        }
        this.selectValue(index, true); // trigger change event
    }

    onPointerLeave (ev) { // (MouseEvent):void
        ev.preventDefault();
        cancelAnimationFrame(this.tick);
        requestAnimationFrame(() => this.changeIndexTo(this.indexSelected));
    }

    onPointerMove (ev) { // (MouseEvent|TouchEvent):void
        ev.preventDefault();
        if (!this.ticking) {
            this.tick = requestAnimationFrame(() => this.changeIndexTo(this.indexFromEvent(ev)));
            this.ticking = true;
        }
    }

    onReset () { // ():void
        const index = this.valueIndex(this.el.querySelector('[selected]')?.value)
        this.selectValue(index || -1, false); // do not trigger change event
    }

    selected () { // ():int
        return this.valueIndex(this.el.value); // get the selected span index
    }

    selectValue (index, triggerChangeEvent) { // (int, bool):void
        this.el.value = this.values[index]?.value || ''; // first set the new value
        this.indexSelected = this.selected(); // get the actual index from the selected value
        if (false === triggerChangeEvent) {
            this.changeIndexTo(this.selected(), true);
        } else {
            this.el.dispatchEvent(new Event('change'));
        }
    }

    valueIndex (value) {
        return this.values.findIndex(val => val.value === +value);
    }
}

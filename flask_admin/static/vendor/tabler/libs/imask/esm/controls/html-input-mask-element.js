import HTMLMaskElement from './html-mask-element.js';
import IMask from '../core/holder.js';
import './mask-element.js';

/** Bridge between InputElement and {@link Masked} */
class HTMLInputMaskElement extends HTMLMaskElement {
  /** InputElement to use mask on */

  constructor(input) {
    super(input);
    this.input = input;
  }

  /** Returns InputElement selection start */
  get _unsafeSelectionStart() {
    return this.input.selectionStart != null ? this.input.selectionStart : this.value.length;
  }

  /** Returns InputElement selection end */
  get _unsafeSelectionEnd() {
    return this.input.selectionEnd;
  }

  /** Sets InputElement selection */
  _unsafeSelect(start, end) {
    this.input.setSelectionRange(start, end);
  }
  get value() {
    return this.input.value;
  }
  set value(value) {
    this.input.value = value;
  }
}
IMask.HTMLMaskElement = HTMLMaskElement;

export { HTMLInputMaskElement as default };

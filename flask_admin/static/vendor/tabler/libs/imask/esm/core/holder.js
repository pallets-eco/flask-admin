/** Applies mask on element */
function IMask(el, opts) {
  // currently available only for input-like elements
  return new IMask.InputMask(el, opts);
}

export { IMask as default };

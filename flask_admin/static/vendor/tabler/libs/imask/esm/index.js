export { default as InputMask } from './controls/input.js';
import IMask from './core/holder.js';
export { default as HTMLContenteditableMaskElement } from './controls/html-contenteditable-mask-element.js';
export { default as HTMLInputMaskElement } from './controls/html-input-mask-element.js';
export { default as HTMLMaskElement } from './controls/html-mask-element.js';
export { default as MaskElement } from './controls/mask-element.js';
export { default as ChangeDetails } from './core/change-details.js';
export { DIRECTION, forceDirection } from './core/utils.js';
export { default as Masked } from './masked/base.js';
export { default as MaskedDate } from './masked/date.js';
export { default as MaskedDynamic } from './masked/dynamic.js';
export { default as MaskedEnum } from './masked/enum.js';
export { default as createMask, normalizeOpts } from './masked/factory.js';
export { default as MaskedFunction } from './masked/function.js';
export { default as MaskedNumber } from './masked/number.js';
export { default as MaskedPattern } from './masked/pattern.js';
export { default as ChunksTailDetails } from './masked/pattern/chunk-tail-details.js';
export { default as PatternFixedDefinition } from './masked/pattern/fixed-definition.js';
export { default as PatternInputDefinition } from './masked/pattern/input-definition.js';
export { PIPE_TYPE, createPipe, pipe } from './masked/pipe.js';
export { default as MaskedRange } from './masked/range.js';
export { default as MaskedRegExp } from './masked/regexp.js';
export { default as RepeatBlock } from './masked/repeat.js';
import './core/action-details.js';
import './controls/input-history.js';
import './core/continuous-tail-details.js';
import './masked/pattern/cursor.js';

try {
  globalThis.IMask = IMask;
} catch {}

export { IMask as default };

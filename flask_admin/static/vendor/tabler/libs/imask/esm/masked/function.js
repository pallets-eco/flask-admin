import Masked from './base.js';
import IMask from '../core/holder.js';
import '../core/change-details.js';
import '../core/continuous-tail-details.js';
import '../core/utils.js';

/** Masking by custom Function */
class MaskedFunction extends Masked {
  /** */

  /** Enable characters overwriting */

  /** */

  /** */

  /** */

  updateOptions(opts) {
    super.updateOptions(opts);
  }
  _update(opts) {
    super._update({
      ...opts,
      validate: opts.mask
    });
  }
}
IMask.MaskedFunction = MaskedFunction;

export { MaskedFunction as default };

import Masked from './base.js';
import IMask from '../core/holder.js';
import '../core/change-details.js';
import '../core/continuous-tail-details.js';
import '../core/utils.js';

/** Masking by RegExp */
class MaskedRegExp extends Masked {
  /** */

  /** Enable characters overwriting */

  /** */

  /** */

  /** */

  updateOptions(opts) {
    super.updateOptions(opts);
  }
  _update(opts) {
    const mask = opts.mask;
    if (mask) opts.validate = value => value.search(mask) >= 0;
    super._update(opts);
  }
}
IMask.MaskedRegExp = MaskedRegExp;

export { MaskedRegExp as default };

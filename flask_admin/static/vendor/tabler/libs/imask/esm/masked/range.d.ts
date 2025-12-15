import ChangeDetails from '../core/change-details';
import { type AppendFlags } from './base';
import MaskedPattern, { MaskedPatternState, type MaskedPatternOptions } from './pattern';
type MaskedRangePatternOptions = MaskedPatternOptions & Pick<MaskedRange, 'from' | 'to'> & Partial<Pick<MaskedRange, 'maxLength'>>;
export type MaskedRangeOptions = Omit<MaskedRangePatternOptions, 'mask'>;
/** Pattern which accepts ranges */
export default class MaskedRange extends MaskedPattern {
    /**
      Optionally sets max length of pattern.
      Used when pattern length is longer then `to` param length. Pads zeros at start in this case.
    */
    maxLength: number;
    /** Min bound */
    from: number;
    /** Max bound */
    to: number;
    get _matchFrom(): number;
    constructor(opts?: MaskedRangeOptions);
    updateOptions(opts: Partial<MaskedRangeOptions>): void;
    _update(opts: Partial<MaskedRangeOptions>): void;
    get isComplete(): boolean;
    boundaries(str: string): [string, string];
    doPrepareChar(ch: string, flags?: AppendFlags): [string, ChangeDetails];
    _appendCharRaw(ch: string, flags?: AppendFlags<MaskedPatternState>): ChangeDetails;
    doValidate(flags: AppendFlags): boolean;
    pad(flags?: AppendFlags): ChangeDetails;
}
export {};
//# sourceMappingURL=range.d.ts.map